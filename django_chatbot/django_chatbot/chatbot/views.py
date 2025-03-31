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
    print(response)
    for chunk in response:
        content_chunk = chunk.choices[0].delta.content
        yield content_chunk  # Yield the content of the chunk

    # for chunk in response:
    #     if hasattr(chunk.choices[0].delta, "content"):
    #         print(chunk.choices[0].delta.content, end="", flush=True)

from django.http import StreamingHttpResponse

@login_required(login_url="login")
def chatbot_streaming(request):
    if request.method == 'POST':
        message = request.POST.get('message')

        # Stream responses from the OpenAI API
        def stream_response():
            for content_chunk in ask_openai_stream(message, model="gpt-3.5-turbo"):
                yield content_chunk

        return StreamingHttpResponse(stream_response(), content_type='text/plain')
    return render(request, 'chatbot_streaming.html')

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