import os
import json
import random
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notion_client import Client
from openai import OpenAI
from pinecone import Pinecone

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate sample emails and add them to Notion database')
parser.add_argument('--use_pinecone', action='store_false', help='Disable Pinecone embedding (enabled by default)')
args = parser.parse_args()

# Load environment variables
load_dotenv()
NOTION_KEY = os.environ["NOTION_KEY"]
DATABASE_ID = os.environ["DATABASE_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")

# Initialize clients
notion = Client(auth=NOTION_KEY)
openai_client = OpenAI()

# Initialize Pinecone if enabled
use_pinecone = args.use_pinecone
if use_pinecone and PINECONE_API_KEY:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index("notion-mail")

# Folder for test messages
MESSAGES_FOLDER = "test_messages"
os.makedirs(MESSAGES_FOLDER, exist_ok=True)

def load_schema():
    """Load the database schema from schema.json"""
    with open("schema.json", "r") as f:
        return json.load(f)

def read_prompt():
    """Read the conversation prompt from sample_emails_prompt.txt"""
    try:
        with open("sample_emails_prompt.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Warning: sample_emails_prompt.txt not found. Using default prompt.")
        return ("Generate a conversation between 3 coworkers discussing project deadlines "
                "and upcoming meetings. Include at least 15 messages.")

def random_date(start: datetime, end: datetime) -> str:
    """Generate a random ISO formatted datetime string between start and end."""
    delta = end - start
    random_seconds = random.randrange(int(delta.total_seconds()))
    random_dt = start + timedelta(seconds=random_seconds)
    return random_dt.isoformat()

def generate_messages():
    # Read custom prompt content
    prompt_content = read_prompt()
    
    # Format the full prompt with formatting instructions
    full_prompt = (
        f"{prompt_content}\n\n"
        "Each message should be formatted as a JSON object on a separate line, with keys: "
        "'sender', 'recipient', and 'message'. Example:\n"
        '{"sender": "Alice", "recipient": "Bob", "message": "Hello Bob!"}\n'
        "Remember: each person can only see emails they wrote or that were sent to them. "
        "Don't create a threeway conversation where everyone can see all messages.\n"
        "Only output the JSON lines."
    )
    
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a creative assistant."},
            {"role": "user", "content": full_prompt}
        ]
    )
    
    return completion.choices[0].message.content.strip()

def save_messages(raw_messages: str):
    """Save each message as a JSON file and return the parsed messages."""
    messages = []
    lines = raw_messages.splitlines()
    for i, line in enumerate(lines):
        if line.strip():
            try:
                message = json.loads(line)
                messages.append(message)
                file_path = os.path.join(MESSAGES_FOLDER, f"message_{i+1}.json")
                with open(file_path, "w") as f:
                    json.dump(message, f, indent=4)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line: {line}")
    return messages

def add_messages_to_database(messages):
    """Add messages to the Notion database with properties defined in schema.json."""
    schema = load_schema()
    start_date = datetime(2025, 3, 1)
    end_date = datetime(2025, 3, 10, 23, 59, 59)
    
    # Store page IDs for later embedding
    page_ids = []
    
    for message in messages:
        sender = message.get("sender", "Unknown")
        recipient = message.get("recipient", "Unknown")
        text = message.get("message", "")
        rand_ts = random_date(start_date, end_date)
        dt_obj = datetime.fromisoformat(rand_ts)
        timestamp_number = dt_obj.timestamp()
        
        properties = {
            "Sender": {
                "rich_text": [
                    {"type": "text", "text": {"content": sender}}
                ]
            },
            "Recipient": {
                "rich_text": [
                    {"type": "text", "text": {"content": recipient}}
                ]
            },
            "Message": {
                "title": [
                    {"type": "text", "text": {"content": text}}
                ]
            },
            "Timestamp": {
                "number": timestamp_number
            }
        }
        
        try:
            response = notion.pages.create(
                parent={"database_id": DATABASE_ID},
                properties=properties
            )
            page_ids.append(response["id"])
            print(f"Added message from '{sender}' to '{recipient}' with timestamp {rand_ts}")
        except Exception as e:
            print(f"Error adding message: {e}")
    
    return page_ids

def embed_messages(page_ids):
    """Embed messages and store in Pinecone."""
    if not use_pinecone or not PINECONE_API_KEY:
        print("Skipping embedding (Pinecone disabled or API key not found)")
        return
    
    print("Embedding messages in Pinecone...")
    messages = []
    
    for page_id in page_ids:
        page = notion.pages.retrieve(page_id=page_id)
        properties = page.get("properties", {})
        
        sender = "".join([p.get("plain_text", "") for p in properties.get("Sender", {}).get("rich_text", [])])
        recipient = "".join([p.get("plain_text", "") for p in properties.get("Recipient", {}).get("rich_text", [])])
        message_text = "".join([p.get("plain_text", "") for p in properties.get("Message", {}).get("title", [])])
        
        combined_text = f"Sender: {sender}\nRecipient: {recipient}\nMessage: {message_text}"
        messages.append({"id": page_id, "text": combined_text})
    
    if not messages:
        print("No messages to embed.")
        return
    
    # Create embeddings
    texts = [msg["text"] for msg in messages]
    
    # Use Pinecone inference to embed the texts
    embeddings = pc.inference.embed(
        model="llama-text-embed-v2",
        inputs=texts,
        parameters={"input_type": "passage"}
    )
    
    # Prepare vectors for upsert
    vectors = []
    for msg, emb in zip(messages, embeddings):
        vector = {
            "id": msg["id"],
            "values": emb["values"],
            "metadata": {"text": msg["text"]}
        }
        vectors.append(vector)
    
    # Upsert vectors to the index
    upsert_response = index.upsert(vectors=vectors, namespace="notion_mail")
    print(f"Embedded {len(vectors)} messages in Pinecone")

def main():
    print("Generating messages using OpenAI...")
    raw_messages = generate_messages()
    
    print("Saving messages to folder:", MESSAGES_FOLDER)
    messages = save_messages(raw_messages)
    
    print(f"Saved {len(messages)} messages. Adding them to Notion with random timestamps...")
    page_ids = add_messages_to_database(messages)
    
    # Embed messages if Pinecone is enabled
    if use_pinecone and PINECONE_API_KEY:
        embed_messages(page_ids)
    
    print("All messages added successfully.")

if __name__ == "__main__":
    main()