import requests
import os

BASE_URL = "http://127.0.0.1:8000"


def upload_pdfs():
    pdf_paths = input("Enter PDF file paths to upload (comma separated): ").split(",")
    pdf_paths = [p.strip() for p in pdf_paths if p.strip()]
    files = [("files", (os.path.basename(path), open(path, "rb"), "application/pdf")) for path in pdf_paths if os.path.isfile(path)]
    if not files:
        print("No valid PDF files provided.")
        return
    res = requests.post(f"{BASE_URL}/pdf/upload", files=files)
    if res.status_code == 200:
        print("Uploaded:", res.json().get("uploaded", []))
    else:
        print("Error:", res.json().get("error", "Failed to upload PDFs."))


def remove_all_pdfs():
    res = requests.delete(f"{BASE_URL}/pdf")
    if res.status_code == 200:
        print("Deleted:", res.json().get("deleted", []))
    else:
        print("Error:", res.json().get("error", "Failed to delete all PDFs."))


def remove_pdf_by_filename():
    res = requests.get(f"{BASE_URL}/pdf")
    if res.status_code == 200:
        pdfs = res.json().get("pdfs", [])
        if pdfs:
            print("Available PDFs:")
            for i, pdf in enumerate(pdfs, 1):
                print(f"{i}. {pdf}")
        else:
            print("No PDFs found.")
    else:
        print("Error fetching available PDFs.")

    filename = input("Enter PDF filename to delete: ").strip()
    if not filename:
        print("Filename cannot be empty.")
        return
    res = requests.delete(f"{BASE_URL}/pdf/{filename}")
    if res.status_code == 200:
        print("Deleted:", res.json().get("deleted", filename))
    else:
        print("Error:", res.json().get("error", f"Failed to delete {filename}."))


def ingest_all_pdfs():
    res = requests.post(f"{BASE_URL}/pdf/ingest")
    if res.status_code == 200:
        print("Ingested:", res.json())
    else:
        print("Error:", res.json().get("error", "Failed to ingest all PDFs."))


def ingest_pdf_by_filename():
    res = requests.get(f"{BASE_URL}/pdf")
    if res.status_code == 200:
        pdfs = res.json().get("pdfs", [])
        if pdfs:
            print("Available PDFs:")
            for i, pdf in enumerate(pdfs, 1):
                print(f"{i}. {pdf}")
        else:
            print("No PDFs found.")
    else:
        print("Error fetching available PDFs.")

    filename = input("Enter PDF filename to ingest: ").strip()
    if not filename:
        print("Filename cannot be empty.")
        return
    res = requests.post(f"{BASE_URL}/pdf/ingest/{filename}")
    if res.status_code == 200:
        print("Ingested:", res.json())
    else:
        print("Error:", res.json().get("error", f"Failed to ingest {filename}."))


def show_menu():
    print("\n=== PDF Data Management ===")
    print("1. Upload PDF(s)")
    print("2. Remove all PDFs")
    print("3. Remove PDF by filename")
    print("4. Ingest all PDFs")
    print("5. Ingest PDF by filename")
    print("6. Exit")
    choice = input("\nEnter your choice (1-6): ").strip()
    if choice == "1":
        upload_pdfs()
    elif choice == "2":
        remove_all_pdfs()
    elif choice == "3":
        remove_pdf_by_filename()
    elif choice == "4":
        ingest_all_pdfs()
    elif choice == "5":
        ingest_pdf_by_filename()
    elif choice == "6":
        print("Exiting...")
        return False
    else:
        print("Invalid choice. Please try again.")
    return True


if __name__ == "__main__":
    while True:
        if not show_menu():
            break
