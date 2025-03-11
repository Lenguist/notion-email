# search.py
from datetime import datetime
from utils import format_message, print_message

def search_command(notion, database_id, search_term=None, current_user=None):
    """
    Searches through messages for the search_term in Sender, Recipient, or Message.
    Only displays messages where current_user is involved (as sender or recipient).
    Results are displayed in chronological order.
    """
    if search_term is None:
        search_term = input("Enter search term: ").strip()
    
    if current_user is None:
        current_user = input("Current user: ").strip()
    
    query_filter = {
        "or": [
            {"property": "Sender", "rich_text": {"contains": search_term}},
            {"property": "Recipient", "rich_text": {"contains": search_term}},
            {"property": "Message", "title": {"contains": search_term}}
        ]
    }
    
    response = notion.databases.query(
        database_id=database_id,
        filter=query_filter
    )
    results = response.get("results", [])
    
    def get_timestamp(page):
        try:
            return page["properties"].get("Timestamp", {}).get("number", 0)
        except Exception:
            return 0
    sorted_results = sorted(results, key=get_timestamp)
    
    if not sorted_results:
        print(f"No messages found containing '{search_term}'.")
        return []
    
    print(f"\nSearch results for '{search_term}' ({len(sorted_results)} messages):\n")
    displayed = 0
    displayed_results = []
    
    for page in sorted_results:
        properties = page["properties"]
        sender_text, message_text = format_message(properties)
        recipient_parts = properties.get("Recipient", {}).get("rich_text", [])
        recipient_text = "".join([part.get("plain_text", "") for part in recipient_parts])
        
        # Only display the message if current_user is involved
        if current_user.lower() not in (sender_text.lower(), recipient_text.lower()):
            continue
        
        timestamp_number = properties.get("Timestamp", {}).get("number", None)
        date_str = ""
        if timestamp_number:
            dt_obj = datetime.fromtimestamp(timestamp_number)
            date_str = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"[{date_str}]")
        print(f"From: {sender_text}")
        print(f"To:   {recipient_text}")
        print(message_text)
        print("-" * 40)
        displayed += 1
        displayed_results.append(page)

    if displayed == 0:
        print(f"No messages found containing '{search_term}' for user {current_user}.")
    
    return displayed_results