# utils.py
def format_message(properties):
    """Format and print a message from Notion properties."""
    sender_parts = properties.get("Sender", {}).get("rich_text", [])
    message_parts = properties.get("Message", {}).get("title", [])
    
    sender_text = "".join([part.get("plain_text", "") for part in sender_parts])
    message_text = "".join([part.get("plain_text", "") for part in message_parts])
    
    return sender_text, message_text

def print_message(sender_text, message_text):
    """Print a formatted message."""
    print(f"from: {sender_text}")
    print(message_text)
    print("-" * 40)