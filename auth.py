# auth.py

def login():
    """
    Prompts the user to log in by asking for their name.
    For now, password is bypassed.
    Returns the username if successful, otherwise None.
    """
    user = input("Enter your name to log in: ").strip()
    if user:
        print(f"Welcome {user}! (password bypassed)")
        return user
    else:
        print("Invalid username. Please try again.")
        return None

def logout(current_user):
    """
    Logs out the current user.
    """
    if current_user:
        print(f"Goodbye {current_user}!")
    else:
        print("No user is currently logged in.")
    return None
