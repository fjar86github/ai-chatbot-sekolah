from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

print("Memulai proses init database...")

# ==============================

# AUTO BUAT FOLDER

# ==============================

os.makedirs("docs", exist_ok=True)
os.makedirs("db", exist_ok=True)

# ==============================

# LOAD PDF

# ==============================

loader = PyPDFDirectoryLoader("docs")
documents = loader.load()

if not documents:
print("Folder docs kosong. Silakan isi PDF terlebih dahulu.")
exit()

print(f"Jumlah halaman ditemukan: {len(documents)}")

# ==============================

# SPLIT DOKUMEN

# ==============================

splitter = RecursiveCharacterTextSplitter(
chunk_size=500,
chunk_overlap=50
)

docs = splitter.split_documents(documents)

print(f"Jumlah chunk: {len(docs)}")

# ==============================

# EMBEDDING

# ==============================

embedding = HuggingFaceEmbeddings(
model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ==============================

# BUAT DATABASE

# ==============================

db = Chroma.from_documents(
docs,
embedding,
persist_directory="db"
)

db.persist()

print("Database awal siap ✅")
