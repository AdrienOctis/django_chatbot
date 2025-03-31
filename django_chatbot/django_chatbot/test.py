from openai import Client
from dotenv import load_dotenv
import os

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
client = Client(api_key=openai_api_key)

def ask_openai_stream(message: str, model: str = "gpt-4o"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}],
        stream=True  # Enable streaming
    )
    print(response)
    return response

# Stream responses from the OpenAI API
def stream_response(message):
    for chunk in ask_openai_stream(message, model="gpt-3.5-turbo"):
        if chunk.choices[0].finish_reason == "stop":
            return
        content_chunk = chunk.choices[0].delta.content
        yield content_chunk

from django.http import StreamingHttpResponse

def chatbot_streaming(message):
    for chunk in ask_openai_stream(message, model="gpt-3.5-turbo"):
        yield chunk
        yield "\n"  # Add a newline character between chunks

def count_up_to(n):
    i=0
    while i <= n:
        i+=1
        yield i

if __name__ == "__main__":
    # response = client.chat.completions.create(
    #     model="gpt-4",  # Assure-toi que ton modèle est bien spécifié
    #     messages=[{"role": "user", "content": "Bonjour, comment vas-tu ?"}],
    #     stream=True  # Activation du streaming
    # )

    # for chunk in response:
    #     print(chunk, "\n")
    # message="Who is Winston Churchill?"
    # gen = stream_response(message)
    # for value in gen:
    #     print(value)
    gen = count_up_to(5)
    for value in gen:
        print(value)


        

