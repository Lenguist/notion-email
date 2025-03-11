# chat-mail.py
import os
import json
import io
import contextlib
from dotenv import load_dotenv
from notion_client import Client
from auth import login, logout
from basic_functionality import send_mail, read_mail
from search import search_command
from semantic_search import semantic_search
from openai import OpenAI

# Initialize OpenAI client
load_dotenv()
openai_client = OpenAI()

def capture_output(func, *args, **kwargs):
    """Capture printed output from a function."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        result = func(*args, **kwargs)
    return buffer.getvalue(), result

def get_ai_instructions(user_prompt, documentation):
    """
    Uses GPT-4o-mini to interpret the user's prompt and generate structured commands.
    Returns a JSON object with a "commands" list.
    """
    messages = [
        {"role": "system", "content": documentation},
        {"role": "user", "content": user_prompt}
    ]
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0
    )
    content = response.choices[0].message.content.strip()
    try:
        instruction = json.loads(content)
        if "commands" not in instruction:
            instruction = {"commands": []}
    except json.JSONDecodeError:
        print(f"Warning: Could not parse JSON from AI response: {content}")
        instruction = {"commands": []}
    return instruction

def execute_commands(commands, notion, database_id, current_user):
    """
    Executes each command in the provided list and returns the combined output.
    Supported actions: send, read, search, semantic_search.
    """
    output = ""
    for cmd in commands:
        action = cmd.get("action", "").lower()
        params = cmd.get("params", {})
        
        if action == "send":
            recipient = params.get("recipient", "")
            message = params.get("message", "")
            captured_output, _ = capture_output(
                send_mail, 
                sender=current_user, 
                recipient=recipient, 
                message=message
            )
            output += captured_output + "\n"
            
        elif action == "read":
            captured_output, _ = capture_output(
                read_mail, 
                user=current_user
            )
            output += captured_output + "\n"
            
        elif action == "search":
            term = params.get("keyword", "")
            captured_output, _ = capture_output(
                search_command, 
                notion, 
                database_id, 
                search_term=term, 
                current_user=current_user
            )
            output += captured_output + "\n"
            
        elif action == "semantic_search":
            query = params.get("query", "")
            captured_output, _ = capture_output(
                semantic_search, 
                query=query, 
                current_user=current_user
            )
            output += captured_output + "\n"
            
        else:
            output += f"Unknown action: {action}\n"
            
    return output

def get_final_answer(command_output, user_prompt, documentation, current_user):
    """
    Uses GPT-4o-mini to generate a conversational answer based on
    the command output and original user prompt.
    """
    messages = [
        {"role": "system", "content": f"You are a concise email assistant for {current_user}. Address {current_user} directly in first person. Keep your responses brief but informative. Include only the most relevant information from the email operations. Don't use unnecessary words or explanations."},
        {"role": "user", "content": f"User prompt: {user_prompt}\n\nCommand output:\n{command_output}\n\nProvide a concise, direct answer. Remember you're talking to {current_user}."}
    ]
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def main():
    # Load environment variables
    load_dotenv()
    NOTION_KEY = os.environ["NOTION_KEY"]
    DATABASE_ID = os.environ["DATABASE_ID"]
    notion = Client(auth=NOTION_KEY)
    
    # Require login
    current_user = None
    print("Welcome to Chat-based NotionMail!")
    while not current_user:
        current_user = login()

    # Load documentation for the AI
    try:
        with open("documentation.txt", "r") as f:
            documentation = f.read()
    except Exception as e:
        print("Error loading documentation.txt:", e)
        documentation = (
            "You are an assistant that can control a mail system. The available commands are:\n"
            "- \"send\": Sends an email. Requires parameters: \"recipient\" and \"message\".\n"
            "- \"read\": Reads all emails for the logged-in user.\n"
            "- \"search\": Searches emails by keyword. Requires parameter: \"keyword\".\n"
            "- \"semantic_search\": Performs semantic search on emails. Requires parameter: \"query\".\n\n"
            "When given a natural language prompt, output a JSON object with a key \"commands\" "
            "that is a list of command objects. For example:\n"
            "{\"commands\": [{\"action\": \"read\", \"params\": {}}]}"
        )

    # Main conversation loop
    print(f"Hello {current_user}, how can I help you today?")
    while True:
        user_query = input("You: ").strip()
        if user_query.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        # Get structured instructions from AI
        instruction = get_ai_instructions(user_query, documentation)
        commands = instruction.get("commands", [])
        
        # Debug output - can be removed in production
        print("\n[AI Instructions]")
        print(json.dumps(instruction, indent=2))
        
        # Execute the commands
        if commands:
            command_output = execute_commands(commands, notion, DATABASE_ID, current_user)
        else:
            command_output = "No valid commands were generated."

        # Generate final conversational answer with updated prompt and pass current_user
        final_answer = get_final_answer(command_output, user_query, documentation, current_user)
        print("\n[Final Answer]")
        print(final_answer)
        print("\nHow else can I help you today? (type 'exit' to quit)")

if __name__ == "__main__":
    main()