# advanced.py
import os
from dotenv import load_dotenv
from notion_client import Client
from auth import login, logout
from basic_functionality import send_mail, read_mail
from semantic_search import semantic_search
from search import search_command

def main():
    # Load environment variables and initialize Notion client
    load_dotenv()
    NOTION_KEY = os.environ["NOTION_KEY"]
    DATABASE_ID = os.environ["DATABASE_ID"]
    notion = Client(auth=NOTION_KEY)

    current_user = None
    print("Welcome to Advanced NotionMail with Semantic Search!")
    
    while True:
        print("\nPlease select an option:")
        print("- login:             Log in to your account.")
        print("- logout:            Log out of your account.")
        print("- send:              Send mail to a user.")
        print("- read:              Check your mail.")
        print("- search:            Keyword search (exact matching).")
        print("- semantic_search:   Semantic search using meaning similarity.")
        print("- exit:              Exit the application.\n")
        
        option = input("$ ").strip().lower()
        
        if option == "login":
            if current_user:
                print(f"Already logged in as {current_user}.")
            else:
                current_user = login()
        elif option == "logout":
            current_user = logout(current_user)
        elif option == "send":
            if not current_user:
                print("You must be logged in to send mail. Please log in first.")
            else:
                # Use sender=current_user and prompt for recipient and message
                send_mail(sender=current_user)
        elif option == "read":
            if not current_user:
                print("You must be logged in to read mail. Please log in first.")
            else:
                # Use current_user as the recipient
                read_mail(user=current_user)
        elif option == "search":
            if not current_user:
                print("You must be logged in to search messages. Please log in first.")
            else:
                term = input("Enter a keyword to search: ").strip()
                if term:
                    search_command(notion, DATABASE_ID, search_term=term, current_user=current_user)
                else:
                    print("Please provide a valid search term.")
        elif option == "semantic_search":
            if not current_user:
                print("You must be logged in to perform semantic search. Please log in first.")
            else:
                query = input("Enter a phrase for semantic search: ").strip()
                if query:
                    semantic_search(query=query, current_user=current_user)
                else:
                    print("Please provide a valid query.")
        elif option == "exit":
            print("Exiting Advanced NotionMail. Goodbye!")
            break
        else:
            print("Invalid option. Please choose one of the listed commands.")

if __name__ == "__main__":
    main()