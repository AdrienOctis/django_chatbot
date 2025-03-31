from celery import shared_task
import os
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

VECTOR_DB_PATH = r"C:\Users\AdrienSERVENTI\OneDrive - Ekimetrics\Documents\Dossier dev\django_chatbot\django_chatbot\vectore_store"

@shared_task
def process_pdf_task(file_path):
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    text_chunks = [doc.page_content for doc in documents]
    
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_texts(text_chunks, embeddings)
    
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)
    vector_store.save_local(VECTOR_DB_PATH)
    
    return "Completed"
