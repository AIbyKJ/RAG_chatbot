import requests
import os

# BASE_URL = "http://127.0.0.1:8000"
BASE_URL = "http://40.82.161.202:8000"

def clear_all_chat_history():
    """Clear all chat history memory for all users."""
    res = requests.delete(f"{BASE_URL}/vectordb/memory")
    if res.status_code == 200:
        print("✅", res.json().get("message", "Memory cleared for all users."))
    else:
        print("Error:", res.json().get("error", "Failed to clear all memory."))


def clear_chat_history_by_user():
    try:
        # Fetch all available user IDs from the backend
        res = requests.get(f"{BASE_URL}/users")
        if res.status_code == 200:
            available_users = res.json().get("user_ids", [])
        else:
            print("Error fetching available users.")
            return

        if available_users:
            print("Available users with chat history:")
            for i, user in enumerate(available_users, 1):
                print(f"{i}. {user}")
            print()
        else:
            print("No users with chat history found.")
            return
    except Exception as e:
        print(f"Error fetching available users: {e}")
        return
    
    user_id = input("Enter user ID to clear memory: ").strip()
    if not user_id:
        print("User ID cannot be empty.")
        return
    
    res = requests.delete(f"{BASE_URL}/vectordb/memory/{user_id}")
    if res.status_code == 200:
        print("✅", res.json().get("message", "Memory cleared."))
    else:
        print("Error:", res.json().get("error", "Failed to clear memory."))

def clear_all_pdf():
    """Clear all PDF data from the database."""
    res = requests.delete(f"{BASE_URL}/vectordb/pdf")
    if res.status_code == 200:
        print("✅", res.json().get("message", "All PDF data cleared."))
    else:
        print("Error:", res.json().get("error", "Failed to clear PDF data."))

def clear_pdf_by_name():
    """Clear PDF data for a specific source name."""
    try:
        res = requests.get(f"{BASE_URL}/vectordb/pdf/sources")
        if res.status_code == 200:
            sources = res.json().get("sources", [])
            if sources:
                print("Available PDF sources in vectordb:")
                for i, source in enumerate(sources, 1):
                    print(f"{i}. {os.path.basename(source)}")
                print()
            else:
                print("No PDF sources found in vectordb.")
        else:
            print("Failed to fetch available PDF sources.")
    except Exception as e:
        print(f"Error fetching available PDF sources: {e}")
    
    source_name = input("Enter the file name of the PDF to clear (as shown above): ").strip()
    if not source_name:
        print("Source name cannot be empty.")
        return
    res = requests.delete(f"{BASE_URL}/vectordb/pdf/{source_name}")
    if res.status_code == 200:
        print("✅", res.json().get("message", f"PDF data cleared for source {source_name}."))
    else:
        print("Error:", res.json().get("error", f"Failed to clear PDF data for source {source_name}."))

def clear_all_vectordb_memory():
    """Clear all PDF data and all chat history memory from the database."""
    clear_all_pdf()
    clear_all_chat_history()

def list_available_users():
    res = requests.get(f"{BASE_URL}/users")
    if res.status_code == 200:
        users = res.json().get("user_ids", [])
        if users:
            print("Available users:")
            for i, user in enumerate(users, 1):
                print(f"{i}. {user}")
        else:
            print("No users found.")
    else:
        print("Error fetching users.")

def list_pdfs_in_chroma():
    res = requests.get(f"{BASE_URL}/vectordb/pdf/sources")
    if res.status_code == 200:
        sources = res.json().get("sources", [])
        if sources:
            print("Available PDFs in vectordb:")
            for i, source in enumerate(sources, 1):
                print(f"{i}. {os.path.basename(source)}")
        else:
            print("No PDFs found in vectordb.")
    else:
        print("Error fetching PDFs from vectordb.")


def show_menu():
    print("\n=== Memory and PDF Management ===")
    print("1. Clear chat history for all users")
    print("2. Clear chat history for specific user")
    print("3. Clear all PDF data")
    print("4. Clear PDF data by filename")
    print("5. Clear all vectordb memory")
    print("6. List available users")
    print("7. List available PDFs in vectordb (ChromaDB)")
    print("8. Exit")
    choice = input("\nEnter your choice (1-8): ").strip()
    if choice == "1":
        clear_all_chat_history()
    elif choice == "2":
        clear_chat_history_by_user()
    elif choice == "3":
        clear_all_pdf()
    elif choice == "4":
        clear_pdf_by_name()
    elif choice == "5":
        clear_all_vectordb_memory()
    elif choice == "6":
        list_available_users()
    elif choice == "7":
        list_pdfs_in_chroma()
    elif choice == "8":
        print("Exiting...")
        return False
    else:
        print("Invalid choice. Please try again.")
    return True


if __name__ == "__main__":
    while True:
        if not show_menu():
            break