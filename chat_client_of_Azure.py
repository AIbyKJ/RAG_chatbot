import subprocess
import requests


def get_azure_vm_ip(resource_group, vm_name):
    try:
        result = subprocess.run(
            [
                "az", "vm", "show", "-d",
                "-g", resource_group,
                "-n", vm_name,
                "--query", "publicIps",
                "-o", "tsv"
            ],
            capture_output=True, text=True, check=True
        )
        ip = result.stdout.strip()
        if not ip:
            print("Could not retrieve VM public IP.")
            exit(1)
        return ip
    except Exception as e:
        print("Error fetching Azure VM IP:", e)
        exit(1)

def chat(api_url):
    user_id = "user1"
    while True:
        msg = input("You: ")
        if msg.lower() in ("exit", "quit"):
            break
        res = requests.post(api_url, json={"user_id": user_id, "message": msg})
        print("🤖:", res.json()["response"])

if __name__ == "__main__":
    # Set your resource group and VM name here
    RESOURCE_GROUP = "rag-chatbot-rg"
    VM_NAME = "rag-vm"

    ip = get_azure_vm_ip(RESOURCE_GROUP, VM_NAME)
    API = f"http://{ip}:8000/chat"
    print(f"Connecting to Azure VM at {API}")
    chat(API) 