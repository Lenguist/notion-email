# basic_functionality.py
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client
from pinecone import Pinecone
from utils import format_message, print_message

# Load environment variables
load_dotenv()
NOTION_KEY = os.environ["NOTION_KEY"]
DATABASE_ID = os.environ["DATABASE_ID"]
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")

# Initialize clients
notion = Client(auth=NOTION_KEY)

# Initialize Pinecone if key is available
try:
    if PINECONE_API_KEY:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index("notion-mail")
    else:
        pc = None
        index = None
except Exception as e:
    print(f"Warning: Failed to initialize Pinecone: {e}")
    pc = None
    index = None

def send_mail(sender=None, recipient=None, message=None):
    """
    Send a message to the Notion database.
    Optionally embed the message in Pinecone for semantic search.
    """
    # Get inputs if not provided
    if sender is None:
        sender = input("Sender: ").strip()
    if recipient is None:
        recipient = input("Recipient: ").strip()
    if message is None:
        message = input("Message: ").strip()
    
    # Get current time as Unix timestamp
    now = datetime.now().astimezone()
    timestamp_number = now.timestamp()

    # Construct properties for the new page
    properties = {
        "Sender": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": sender}
                }
            ]
        },
        "Recipient": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": recipient}
                }
            ]
        },
        "Message": {
            "title": [
                {
                    "type": "text",
                    "text": {"content": message}
                }
            ]
        },
        "Timestamp": {
            "number": timestamp_number
        }
    }

    # Create a new page in the database
    try:
        response = notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties=properties
        )
        print("Mail sent successfully!\n")
        
        # Try to embed the message for semantic search
        if pc and index:
            try:
                # Format the text for embedding
                combined_text = f"Sender: {sender}\nRecipient: {recipient}\nMessage: {message}"
                
                # Create embedding using Pinecone
                embedding = pc.inference.embed(
                    model="llama-text-embed-v2",
                    inputs=[combined_text],
                    parameters={"input_type": "passage"}
                )
                
                # Prepare vector for upsert
                vector = {
                    "id": response["id"],
                    "values": embedding[0]["values"],
                    "metadata": {"text": combined_text}
                }
                
                # Upsert to Pinecone
                index.upsert(vectors=[vector], namespace="notion_mail")
            except Exception as e:
                print(f"Skipping embedding due to error: {e}")
                print("Message won't be searchable via semantic search.")
        
        return True
    except Exception as e:
        print(f"Error sending mail: {e}")
        return False

def read_mail(user=None):
    """
    Retrieve and display messages for a specific recipient.
    """
    if user is None:
        user = input("User: ").strip()

    # Query database for matching recipients
    response = notion.databases.query(
        database_id=DATABASE_ID,
        filter={
            "property": "Recipient",
            "rich_text": {
                "equals": user
            }
        }
    )

    results = response.get("results", [])
    print(f"\nMessages ({len(results)}):\n")
    
    for page in results:
        sender_text, message_text = format_message(page["properties"])
        print_message(sender_text, message_text)
    
    if not results:
        print("No messages found.\n")
    
    return results

def main():
    """Main CLI loop for the application."""
    print("Welcome to NotionMail!")
    
    while True:
        print("\nPlease select an option:")
        print("- send: Send mail to a user.")
        print("- read: Check a user's mail.")
        print("- exit: Exit the application.\n")

        option = input("$ ").strip().lower()

        if option == "send":
            send_mail()
        elif option == "read":
            read_mail()
        elif option == "exit":
            print("Exiting NotionMail. Goodbye!")
            break
        else:
            print("Invalid option. Please choose 'send', 'read', or 'exit'.")

if __name__ == "__main__":
    main()