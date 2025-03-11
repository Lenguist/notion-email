# dev.py
import os
import json
from collections import Counter
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables from .env file
load_dotenv()

# Retrieve Notion integration key and database ID from environment variables
NOTION_KEY = os.environ["NOTION_KEY"]
DATABASE_ID = os.environ.get("DATABASE_ID")

# Initialize the Notion client with the integration token
notion = Client(auth=NOTION_KEY)

def load_schema():
    """Load the database schema from schema.json"""
    with open("schema.json", "r") as f:
        return json.load(f)

def check_database_exists():
    """Check if the database exists at the specified ID"""
    if not DATABASE_ID:
        return False
    
    try:
        notion.databases.retrieve(database_id=DATABASE_ID)
        return True
    except Exception:
        return False

def create_database():
    """Create a new Notion database based on schema.json"""
    schema = load_schema()
    
    # Create database in user's Notion workspace
    response = notion.databases.create(
        parent={"type": "page_id", "page_id": input("Enter parent page ID: ")},
        title=[{"type": "text", "text": {"content": "NotionMail Database"}}],
        properties=schema["properties"]
    )
    
    # Save the new database ID to .env file
    with open(".env", "a") as f:
        f.write(f"\nDATABASE_ID={response['id']}")
    
    print(f"Database created with ID: {response['id']}")
    print("Updated .env file with the new DATABASE_ID")
    
    return response["id"]

def validate_database_schema():
    """Validate that the database schema matches our expected schema"""
    expected_schema = load_schema()["properties"]
    current_schema = notion.databases.retrieve(database_id=DATABASE_ID)["properties"]
    
    # Check if all expected properties exist with correct types
    missing_props = []
    incorrect_types = []
    
    for prop_name, prop_details in expected_schema.items():
        if prop_name not in current_schema:
            missing_props.append(prop_name)
        elif current_schema[prop_name]["type"] != prop_details["type"]:
            incorrect_types.append(f"{prop_name} (expected {prop_details['type']}, got {current_schema[prop_name]['type']})")
    
    if missing_props or incorrect_types:
        print("Database schema validation failed:")
        if missing_props:
            print(f"  Missing properties: {', '.join(missing_props)}")
        if incorrect_types:
            print(f"  Incorrect types: {', '.join(incorrect_types)}")
        return False
    
    return True

def query_database():
    """Query the Notion database and return the response."""
    response = notion.databases.query(database_id=DATABASE_ID)
    return response

def extract_text_from_property(prop):
    """Extract plain text from a Notion property."""
    if "rich_text" in prop:
        return "".join([part.get("plain_text", "") for part in prop["rich_text"]])
    elif "title" in prop:
        return "".join([part.get("plain_text", "") for part in prop["title"]])
    return ""

def display_statistics():
    """
    Display overall statistics:
    - What fields are in the database right now.
    - How many different senders and recipients.
    - How many messages sent and received by each person.
    """
    data = query_database()
    results = data.get("results", [])
    
    # Collect all property fields available in the pages
    fields_set = set()
    for page in results:
        properties = page.get("properties", {})
        for key in properties.keys():
            fields_set.add(key)
    
    print("=" * 50)
    print("Overall Database Statistics")
    print("=" * 50)
    print(f"Total Pages: {len(results)}")
    print("Fields in database:", ", ".join(sorted(fields_set)))
    
    # Counters for messages sent and received
    sent_counter = Counter()
    received_counter = Counter()
    
    for page in results:
        properties = page.get("properties", {})
        sender = extract_text_from_property(properties.get("Sender", {}))
        recipient = extract_text_from_property(properties.get("Recipient", {}))
        
        if sender:
            sent_counter[sender] += 1
        if recipient:
            received_counter[recipient] += 1
    
    print("\nUnique Senders:", len(sent_counter))
    print("Unique Recipients:", len(received_counter))
    
    print("\nMessages Sent by Each Person:")
    for sender, count in sent_counter.most_common():
        print(f"  {sender}: {count}")
    
    print("\nMessages Received by Each Person:")
    for recipient, count in received_counter.most_common():
        print(f"  {recipient}: {count}")
    
    print("=" * 50)

def display_pretty():
    """
    For each page in the database, display the page ID and its properties in a pretty format.
    """
    data = query_database()
    for page in data.get("results", []):
        print("=" * 50)
        print(f"Page ID: {page.get('id')}\n")
        print("Properties:")
        print(json.dumps(page.get("properties", {}), indent=4))
    print("=" * 50)

def main():
    """
    Main function to check, create or validate database, and display statistics.
    """
    # Check if database exists
    if not check_database_exists():
        print("Database does not exist or cannot be accessed.")
        create_new = input("Create a new database? (y/n): ").lower() == 'y'
        if create_new:
            global DATABASE_ID
            DATABASE_ID = create_database()
        else:
            print("Exiting.")
            return
    
    # Validate database schema
    if not validate_database_schema():
        print("Database schema doesn't match expected schema.")
        print("Please fix the database schema or update schema.json.")
        return
    
    # Display statistics
    display_statistics()
    
    # Uncomment to see detailed page data
    # display_pretty()

if __name__ == "__main__":
    main()