# RAG Chatbot

A simple Retrieval-Augmented Generation (RAG) chatbot using FastAPI, LangChain, and ChromaDB.

## 1. Local Machine Usage

1. **Install requirements**
   ```sh
   pip install -r requirements.txt
   ```
2. **Run data ingestion**
   ```sh
   python ingest.py
   ```
3. **Start the FastAPI server**
   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
4. **Test with the chat client**
   ```sh
   python chat_client.py
   ```

---

## 2. Deploy on Azure VM (Ubuntu)

1. **Clone the repository**
   ```sh
   git clone https://github.com/kittysoftpaw0510/RAG_chatbot
   cd rag_chatbot
   ```
2. **Provision and prepare the VM**
   ```sh
   az login

   az group create --name rag-chatbot-rg --location eastus
   az vm create --resource-group rag-chatbot-rg --name rag-vm --image UbuntuLTS --admin-username azureuser --generate-ssh-keys --size Standard_DS2_v2 --output json

   az disk create --resource-group rag-chatbot-rg --name rag-disk --size-gb 20 --sku Premium_LRS
   az vm disk attach --resource-group rag-chatbot-rg --vm-name rag-vm --name rag-disk

   az vm show -d -g rag-chatbot-rg -n rag-vm --query publicIps -o tsv
   # Copy project files to VM (replace <your_vm_ip> with the actual IP)
   scp -r ./rag_chatbot azureuser@<your_vm_ip>:/home/azureuser/rag_chatbot

   # Or, using Azure CLI:
   scp -r ./rag_chatbot azureuser@$(az vm show -d -g rag-chatbot-rg -n rag-vm --query publicIps -o tsv):/home/azureuser/rag_chatbot
   
   az vm open-port --port 8000 --resource-group rag-chatbot-rg --name rag-vm


   ssh azureuser@<your_vm_ip>

   sudo apt-get update
   sudo apt-get install -y docker.io

   sudo mkdir -p /mnt/azuredata
   sudo chown azureuser:azureuser /mnt/azuredata

   cd /home/azureuser/rag_chatbot
   
   docker build -t ragbot .
   docker run -d -p 8000:8000 -v /mnt/azuredata:/mnt/azuredata --name rag_container ragbot
   docker ps
   ```
3. **Run chat_client.py on your local machine**
   ```sh
   python chat_client.py
   ```
   (Make sure to update the API URL in `chat_client.py` to point to your VM's public IP)

---

## Notes
- The ingestion step (`ingest.py`) must complete before starting the FastAPI server.
- The Dockerfile is set up to run ingestion automatically before launching the server.

---

Enjoy chatting with your RAG-powered bot! 