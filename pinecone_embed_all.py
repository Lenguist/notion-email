import os
import json
from dotenv import load_dotenv
from notion_client import Client
from pinecone import Pinecone, ServerlessSpec  # Import required Pinecone classes

# Load environment variables
load_dotenv()
NOTION_KEY = os.environ["NOTION_KEY"]
DATABASE_ID = os.environ["DATABASE_ID"]
PINECONE_API_KEY = os.environ["PINECONE_API_KEY"]

# Initialize Notion client
notion = Client(auth=NOTION_KEY)

# Initialize Pinecone client by creating an instance of Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Connect to your index; now using the index name "notion-mail"
index = pc.Index("notion-mail")

def get_messages():
    """
    Retrieves messages from the Notion database and returns a list of dictionaries.
    Each dictionary contains the page ID and a combined text from Sender, Recipient, and Message.
    """
    response = notion.databases.query(database_id=DATABASE_ID)
    messages = []
    for page in response.get("results", []):
        properties = page.get("properties", {})
        sender = "".join([p.get("plain_text", "") for p in properties.get("Sender", {}).get("rich_text", [])])
        recipient = "".join([p.get("plain_text", "") for p in properties.get("Recipient", {}).get("rich_text", [])])
        message_text = "".join([p.get("plain_text", "") for p in properties.get("Message", {}).get("title", [])])
        combined_text = f"Sender: {sender}\nRecipient: {recipient}\nMessage: {message_text}"
        messages.append({"id": page["id"], "text": combined_text})
    return messages

def embed_and_upsert():
    """
    Embeds each message using Pinecone’s inference API and upserts the resulting vectors into the Pinecone index.
    The full embedding vector is used without truncation.
    """
    messages = get_messages()
    if not messages:
        print("No messages found in Notion.")
        return

    texts = [msg["text"] for msg in messages]

    # Use Pinecone inference to embed the texts.
    embeddings = pc.inference.embed(
        model="llama-text-embed-v2",
        inputs=texts,
        parameters={"input_type": "passage"}
    )

    # Prepare vectors for upsert; each vector contains an id, values, and metadata.
    vectors = []
    for msg, emb in zip(messages, embeddings):
        vector = {
            "id": msg["id"],
            "values": emb["values"],
            "metadata": {"text": msg["text"]}
        }
        vectors.append(vector)

    # Upsert vectors to the index (using a namespace "notion_mail")
    upsert_response = index.upsert(vectors=vectors, namespace="notion_mail")
    print("Upsert response:", upsert_response)

if __name__ == "__main__":
    print("Embedding all existing messages and upserting to Pinecone...")
    embed_and_upsert()
    print("Embedding update complete.")
