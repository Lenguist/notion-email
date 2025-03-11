# semantic_search.py
import os
from dotenv import load_dotenv
from pinecone import Pinecone
from utils import format_message, print_message

# Load environment variables
load_dotenv()
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "notion-mail")

# Initialize Pinecone client if possible
try:
    if PINECONE_API_KEY:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index = pc.Index(PINECONE_INDEX_NAME)
    else:
        pc = None
        index = None
except Exception as e:
    print(f"Warning: Failed to initialize Pinecone: {e}")
    pc = None
    index = None

def semantic_search(query=None, current_user=None, top_k=3, namespace="notion_mail"):
    """
    Uses Pinecone's inference API to find semantically similar messages.
    Only returns messages that involve the current_user (as sender or recipient).
    """
    if not pc or not index:
        print("Error: Pinecone is not properly configured. Semantic search unavailable.")
        return []
    
    if query is None:
        query = input("Enter a phrase for semantic search: ").strip()
    
    if current_user is None:
        current_user = input("Current user: ").strip()
    
    if not current_user:
        print("Error: You must provide a username to perform semantic search.")
        return []

    try:
        # Embed the query using Pinecone's inference service
        embeddings = pc.inference.embed(
            model="llama-text-embed-v2",
            inputs=[query],
            parameters={"input_type": "query"}
        )
        query_vector = embeddings[0]["values"]

        # Query the index for similar vectors
        results = index.query(
            namespace=namespace,
            vector=query_vector,
            top_k=top_k * 3,  # request more to account for filtering
            include_values=False,
            include_metadata=True
        )
    except Exception as e:
        print(f"Error performing semantic search: {e}")
        return []

    print(f"\nSemantic search results for '{query}':")
    displayed = 0
    displayed_results = []
    
    for match in results["matches"]:
        metadata = match.get("metadata", {})
        text = metadata.get("text", "")
        
        # Parse the text format: "Sender: X\nRecipient: Y\nMessage: Z"
        lines = text.splitlines()
        if len(lines) >= 2:
            sender_line = lines[0]
            recipient_line = lines[1]
            
            # Extract sender and recipient values
            sender = sender_line.replace("Sender:", "").strip()
            recipient = recipient_line.replace("Recipient:", "").strip()
            
            # Check if current_user matches either sender or recipient (case-insensitive)
            if current_user.lower() in (sender.lower(), recipient.lower()):
                # Reconstruct message format for display
                message_content = "\n".join(lines[2:]).replace("Message:", "", 1).strip()
                
                score = match.get("score", 0)
                print(f"\nScore: {score:.4f}")
                print(f"From: {sender}")
                print(f"To: {recipient}")
                print(message_content)
                print("-" * 40)
                
                displayed += 1
                displayed_results.append({
                    "id": match.get("id"),
                    "score": score,
                    "sender": sender,
                    "recipient": recipient,
                    "message": message_content
                })
                
                if displayed >= top_k:
                    break
    
    if displayed == 0:
        print(f"No matching messages found for user '{current_user}'.")
    
    return displayed_results

if __name__ == "__main__":
    semantic_search()