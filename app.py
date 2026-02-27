from flask import Flask, request, jsonify, render_template, session, redirect
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import ollama
import os
from functools import wraps
from collections import Counter

app = Flask(**name**)
app.secret_key = "sekolah-secret"

# ==============================

# SETUP VECTOR DB

# ==============================

embedding = HuggingFaceEmbeddings(
model_name="sentence-transformers/all-MiniLM-L6-v2"
)

db = Chroma(
persist_directory="db",
embedding_function=embedding
)

# ==============================

# MEMORY USER CHAT

# ==============================

memory_store = {}

# ==============================

# STATISTIK PERTANYAAN

# ==============================

question_log = []

# ==============================

# LOGIN ADMIN

# ==============================

ADMIN_USER = "admin"
ADMIN_PASS = "sekolah123"

def login_required(f):
@wraps(f)
def decorated(*args, **kwargs):
if not session.get("admin"):
return redirect("/login")
return f(*args, **kwargs)
return decorated

# ==============================

# LOGIN ROUTE

# ==============================

@app.route("/login", methods=["GET","POST"])
def login():
if request.method == "POST":
u = request.form["username"]
p = request.form["password"]

```
    if u == ADMIN_USER and p == ADMIN_PASS:
        session["admin"] = True
        return redirect("/admin")

return render_template("login.html")
```

# ==============================

# TAMBAH PDF KE DB

# ==============================

def add_pdf_to_db(filepath):
loader = PyPDFLoader(filepath)
documents = loader.load()

```
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

docs = splitter.split_documents(documents)
ids = [filepath + str(i) for i in range(len(docs))]

db.add_documents(docs, ids=ids)
db.persist()
```

# ==============================

# HOME

# ==============================

@app.route("/")
def home():
return render_template("index.html")

# ==============================

# CHAT AI

# ==============================

@app.route("/chat", methods=["POST"])
def chat():
user_id = session.get("id")

```
if not user_id:
    user_id = os.urandom(8).hex()
    session["id"] = user_id

if user_id not in memory_store:
    memory_store[user_id] = []

question = request.json["question"]

docs = db.similarity_search(question, k=3)
context = "\n".join([d.page_content for d in docs])

history = "\n".join(memory_store[user_id][-6:])

prompt = f"""
```

Kamu adalah AI asisten sekolah.

Gunakan konteks:
{context}

Riwayat:
{history}

Jika jawaban tidak ada di dokumen, katakan tidak ditemukan.

Pertanyaan:
{question}
"""

```
response = ollama.chat(
    model="phi",
    messages=[{"role":"user","content":prompt}]
)

answer = response["message"]["content"]

memory_store[user_id].append(f"User: {question}")
memory_store[user_id].append(f"AI: {answer}")

question_log.append(question)

return jsonify({"answer": answer})
```

# ==============================

# ADMIN PANEL

# ==============================

@app.route("/admin")
@login_required
def admin():
return render_template("admin.html")

# ==============================

# UPLOAD PDF

# ==============================

@app.route("/upload", methods=["POST"])
@login_required
def upload():
file = request.files["file"]

```
os.makedirs("docs", exist_ok=True)

path = os.path.join("docs", file.filename)
file.save(path)

add_pdf_to_db(path)

return "Upload sukses & AI langsung update!"
```

# ==============================

# STATISTIK

# ==============================

@app.route("/stats")
@login_required
def stats():
data = Counter(question_log)
return jsonify(data)

# ==============================

# LOGOUT

# ==============================

@app.route("/logout")
@login_required
def logout():
session.clear()
return redirect("/login")

# ==============================

# RUN SERVER

# ==============================

if **name** == "**main**":
app.run(host="0.0.0.0", port=5000)
