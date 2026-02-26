from flask import Flask, request, jsonify, render_template, session
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import ollama
import os
#Tambahkan di app.py
from functools import wraps


app = Flask(__name__)
app.secret_key = "sekolah-secret"

embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db = Chroma(persist_directory="db", embedding_function=embedding)

memory_store = {}

#STATISTIK PERTANYAAN
question_log = []

#Tambahkan USER & PASSWORD:
ADMIN_USER = "admin"
ADMIN_PASS = "sekolah123"
#Fungsi proteksi login
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

#Route Login
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u == ADMIN_USER and p == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")

    return render_template("login.html")

def add_pdf_to_db(filepath):
    loader = PyPDFLoader(filepath)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.split_documents(documents)

    ids = [filepath + str(i) for i in range(len(docs))]
    db.add_documents(docs, ids=ids)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_id = session.get("id")

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
    Kamu adalah AI asisten sekolah.

    Gunakan konteks:
    {context}

    Riwayat:
    {history}

    Jika jawaban tidak ada di dokumen, katakan tidak ditemukan.

    Pertanyaan:
    {question}
    """

    response = ollama.chat(
        model="phi",
        messages=[{"role":"user","content":prompt}]
    )

    answer = response["message"]["content"]

    memory_store[user_id].append(f"User: {question}")
    memory_store[user_id].append(f"AI: {answer}")
    #masukan log pertanyaan statistik
    question_log.append(question)
    return jsonify({"answer": answer})

#Route Statistik
@app.route("/stats")
@login_required
def stats():
    from collections import Counter
    data = Counter(question_log)
    return jsonify(data)

@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html")

@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files["file"]
    path = os.path.join("docs", file.filename)
    file.save(path)

    add_pdf_to_db(path)

    return "Upload sukses & AI langsung update!"
    
app.run(host="0.0.0.0", port=5000)
