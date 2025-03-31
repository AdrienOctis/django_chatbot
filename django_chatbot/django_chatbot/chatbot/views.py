from django.shortcuts import render, redirect
from django.http import JsonResponse
from dotenv import load_dotenv
from django.utils import timezone
import os
from openai import Client

from django.contrib import auth
from django.contrib.auth.models import User
from .models import Chat
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import time

import uuid
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from celery.result import AsyncResult
from .tasks import process_pdf_task


load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
client = Client(api_key=openai_api_key)

def ask_openai(message: str, model: str = "gpt-4o"):
    response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": message}]
    )
    print(response)
    answer = response.choices[0].message.content
    return answer

@login_required(login_url="login")
def chatbot(request):
    if request.user.is_authenticated:
        chats = Chat.objects.filter(user=request.user)
    else:
        chats = []  # No chats for an anonymous user

    if request.method == 'POST':
        message = request.POST.get('message')
        model1 = request.POST.get('model1', 'o3-mini')  # Default to 'o3-mini'
        model2 = request.POST.get('model2', 'gpt-3.5-turbo')  # Default to 'gpt-3.5-turbo'
        
        response1 = ask_openai(message, model=model1)
        response2 = ask_openai(message, model=model2)
        
        return JsonResponse({
            'message': message,
            'response1': response1,
            'response2': response2,
            'model1': model1,
            'model2': model2
        })
    return render(request, 'chatbot.html', {'chats': chats})


def ask_openai_stream(message: str, model: str = "gpt-4o"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}],
        stream=True  # Enable streaming
    )
    return response

# Stream responses from the OpenAI API
def stream_response(message, user_id):
    for chunk in ask_openai_stream(message, model="gpt-3.5-turbo"):
        if stop_signals.get(user_id, False):
            break
        if chunk.choices[0].finish_reason == "stop":
            return
        content_chunk = chunk.choices[0].delta.content
        yield content_chunk
        time.sleep(0.2)

# def stream_response(message):
#     for char in message:
#         time.sleep(0.2)
#         yield f'{char}  '

from django.http import StreamingHttpResponse

stop_signals = {}  # Dictionary to track stop signals per user

# def stream_response(message, user_id):
#     for char in message:
#         if stop_signals.get(user_id, False):
#             break  # Stop streaming if stop signal is received
#         yield char
#         time.sleep(0.2)

@login_required(login_url="login")
def chatbot_streaming(request):
    if request.method == 'POST':
        user_id = request.user.id  # Identify user session
        stop_signals[user_id] = False  # Reset stop signal
        message = request.POST.get('message', '')
        return StreamingHttpResponse(stream_response(message, user_id), content_type='text/plain')
    return render(request, 'chatbot_streaming.html')

@csrf_exempt  # Disable CSRF for this simple stop request
def stop_chatbot(request):
    if request.method == 'POST':
        user_id = request.user.id
        stop_signals[user_id] = True  # Set stop signal
        return StreamingHttpResponse("Stopped", content_type='text/plain')

# @login_required(login_url="login")
# def chatbot_streaming(request):
#     if request.method == 'POST':
#         message = request.POST.get('message')
#         return StreamingHttpResponse(stream_response(message), content_type='text/plain')
    
#     return render(request, 'chatbot_streaming.html')

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect('chatbot')
            except:
                error_message = 'Error creating account'
                return render(request, 'register.html', {'error_message': error_message})
        else:
            error_message = 'Passwords dont match'
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')

def logout(request):
    auth.logout(request)
    return redirect('login')

UPLOAD_DIR = r"C:\Users\AdrienSERVENTI\OneDrive - Ekimetrics\Documents\Dossier dev\django_chatbot\django_chatbot\uploads"
VECTOR_DB_PATH = r"C:\Users\AdrienSERVENTI\OneDrive - Ekimetrics\Documents\Dossier dev\django_chatbot\django_chatbot\vectore_store"

# @csrf_exempt
# def upload_pdf(request):    
#     if request.method == "POST" and request.FILES.get("file"):
#         file = request.FILES["file"]
#         file_path = os.path.join(UPLOAD_DIR, str(uuid.uuid4()) + ".pdf")
        
#         os.makedirs(UPLOAD_DIR, exist_ok=True)
        
#         with default_storage.open(file_path, "wb+") as destination:
#             for chunk in file.chunks():
#                 destination.write(chunk)
        
#         process_pdf(file_path)
#         return JsonResponse({"message": "File uploaded and processed successfully!"})
    
#     return render(request, "upload.html")


# def process_pdf(file_path):
#     loader = PyPDFLoader(file_path)
#     documents = loader.load()
#     text_chunks = [doc.page_content for doc in documents]
    
#     embeddings = OpenAIEmbeddings()
#     vector_store = FAISS.from_texts(text_chunks, embeddings)
    
#     os.makedirs(VECTOR_DB_PATH, exist_ok=True)
#     vector_store.save_local(VECTOR_DB_PATH)

@csrf_exempt
def upload_pdf(request):
    if request.method == "GET":
        return render(request, "upload.html")
    
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        file_path = os.path.join(UPLOAD_DIR, str(uuid.uuid4()) + ".pdf")
        
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        with default_storage.open(file_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        
        task = process_pdf_task.delay(file_path)
        return JsonResponse({"message": "File uploaded successfully!", "task_id": task.id})
    
    return JsonResponse({"error": "Invalid request"}, status=400)

def check_task_status(request, task_id):
    task = AsyncResult(task_id)
    return JsonResponse({"task_id": task_id, "status": task.status})



