# RAG Chatbot: Azure Deployment & Local Testing Guide

# Help for RAG Chatbot(version2.0)

A simple Retrieval-Augmented Generation (RAG) chatbot using FastAPI, LangChain, and ChromaDB.

## 1. Local Machine Usage

1. **Clone the repository**
   ```sh
   git clone https://github.com/kittysoftpaw0510/RAG_chatbot
   cd rag_chatbot
   ```
2. **Install requirements**
   ```sh
   pip install -r requirements.txt
   ```
3. **Set Environment of Project**
   ```sh
   mkdir data
   ```
   Copy your pdf files into 'data' directory.
4. **Create .env file**
   ```
   Make new .env file or copy and paste .env.example.
   And type like below.
   OPENAI_API_KEY= sk-proj-xxx
   ```
5. **Run data ingestion**
   ```sh
   python ingest.py (--clear-pdf)
   ```
6. **Start the FastAPI server**
   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
7. **Test with the chat client**
   ```sh
   python chat_client.py
   ```

---

## 2. Deploy on Azure VM (Ubuntu)

1. **Install required Programs**
- **Azure CLI:**  
  [Install instructions (Windows, Mac, Linux)](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)
  - **After install, restart your terminal!**
- **scp/ssh:**  
  - On Windows, use [Git Bash](https://gitforwindows.org/), [WSL](https://docs.microsoft.com/en-us/windows/wsl/), or [PuTTY](https://www.putty.org/).
  - On Mac/Linux, these are pre-installed.

---

2. **Clone the Repository**

```sh
git clone https://github.com/kittysoftpaw0510/RAG_chatbot
cd rag_chatbot
```

---

3. **Prepare Local Data and Environment**

```sh
mkdir data
# Copy your PDF files into the 'data' directory
```

Create a `.env` file (do NOT commit this to git!):
```
OPENAI_API_KEY=sk-proj-xxx
```

---

4. **Provision and Prepare the Azure VM**

```sh
az login
# Follow the browser/device login instructions

az group create --name rag-chatbot-rg --location eastus

az vm create --resource-group rag-chatbot-rg --name rag-vm --image UbuntuLTS --admin-username azureuser --generate-ssh-keys --size Standard_DS2_v2 --output json

az disk create --resource-group rag-chatbot-rg --name rag-disk --size-gb 20 --sku Premium_LRS
az vm disk attach --resource-group rag-chatbot-rg --vm-name rag-vm --name rag-disk

az vm open-port --port 8000 --resource-group rag-chatbot-rg --name rag-vm
```

---

5. **Copy Project Files to the VM**

**Get your VM's public IP:**
```sh
az vm show -d -g rag-chatbot-rg -n rag-vm --query publicIps -o tsv
```
Suppose it returns `20.30.40.50`.

**Copy files (from your local machine):**
```sh
cd ..
# On Windows, use Git Bash or WSL for scp
scp -r -i ./rag_chatbot azureuser@20.30.40.50:/home/azureuser/rag_chatbot
```
> **Troubleshooting:**  
> - If you get a "permission denied" error, make sure you're using the same SSH key as during VM creation.
> - If `scp` is not found, use Git Bash or WSL.

---

6. **Connect to the VM**

```sh
ssh azureuser@20.30.40.50
```
- **If prompted for a password:**  
  - You should NOT need one if you used `--generate-ssh-keys`.  
  - If you do, check your SSH key setup.

---

7. **Prepare the VM Environment**

```sh
sudo apt-get update
sudo apt-get install -y docker.io python3 python3-pip
# sudo mkdir -p /mnt/azuredata
# sudo chown azureuser:azureuser /mnt/azuredata
cd /home/azureuser/rag_chatbot
```
---
8. **Mount External Disk**
```sh
# Create a new partition (n), write (w)
sudo fdisk /dev/sdc

# Format the new partition
sudo mkfs.ext4 /dev/sdc1

# Create the mount point
sudo mkdir -p /mnt/azuredata

# Mount the disk
sudo mount /dev/sdc1 /mnt/azuredata
```

---

9. **Build and Run the Docker Container**

```sh
docker build -t ragbot .
docker run -d -p 8000:8000 -v /mnt/azuredata:/mnt/azuredata \
  -e CHROMA_PERSIST_DIR=/mnt/azuredata \
  --name rag_container ragbot
docker ps
```
> **Troubleshooting:**  
> - If you get a "permission denied" error, try `sudo docker ...` or add your user to the `docker` group.

---

10. **Test the App from Your Local Machine**

**Use the provided script:**
```sh
python chat_client_of_Azure.py
```
- This script will automatically fetch your VM's public IP and connect to the chatbot.
- **Make sure you have the Azure CLI installed and are logged in locally.**

---

## **Troubleshooting & Tips**

- **SSH/`scp` issues:**  
  - Use the same user (`azureuser`) and SSH key as during VM creation.
  - On Windows, use Git Bash or WSL for `scp` and `ssh`.

- **Docker issues:**  
  - Use `sudo` if you get permission errors.
  - Make sure Docker is running: `sudo systemctl start docker`

- **API Key issues:**  
  - Double-check your `.env` file and never commit it to git.

- **Firewall/Port issues:**  
  - Ensure port 8000 is open in Azure and not blocked by your local firewall.

- **Python version:**  
  - Use `python3` if `python` points to Python 2.x.

---

## **Summary Table**

| Step                | Common Issues & Fixes                                 |
|---------------------|------------------------------------------------------|
| Azure CLI           | Restart terminal after install                        |
| SSH/scp             | Use correct user/key, use Git Bash/WSL on Windows    |
| Docker              | Use `sudo` if needed, ensure Docker is running       |
| .env                | Must exist, never commit to git                      |
| chat_client_of_Azure.py | Needs Azure CLI locally, VM must be running      |

---

Enjoy chatting with your RAG-powered bot! 