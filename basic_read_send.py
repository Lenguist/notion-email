import os
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables and initialize client
load_dotenv()
NOTION_KEY = os.environ["NOTION_KEY"]
DATABASE_ID = os.environ["DATABASE_ID"]
notion = Client(auth=NOTION_KEY)

def send_mail():
    """Prompts for sender, recipient, and message, then creates a new page in the Notion database."""
    sender = input("Sender: ").strip()
    recipient = input("Recipient: ").strip()
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
    notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties=properties
    )
    print("Mail sent successfully!\n")

def read_mail():
    """Retrieves and displays messages where the recipient matches the provided username."""
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
        sender_parts = page["properties"].get("Sender", {}).get("rich_text", [])
        message_parts = page["properties"].get("Message", {}).get("title", [])
        
        sender_text = "".join([part.get("plain_text", "") for part in sender_parts])
        message_text = "".join([part.get("plain_text", "") for part in message_parts])
        
        print(f"from: {sender_text}")
        print(message_text)
        print("-" * 40)
    if not results:
        print("No messages found.\n")

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