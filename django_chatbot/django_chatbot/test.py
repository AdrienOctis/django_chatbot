from openai import Client
from dotenv import load_dotenv
import os

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
client = Client(api_key=openai_api_key)

def ask_openai_stream(message: str, model: str = "gpt-3.5-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}],
        stream=True  # Enable streaming
    )
    for chunk in response:
        if "choices" in chunk and len(chunk["choices"]) > 0:
            delta = chunk["choices"][0]["delta"]
            if "content" in delta:
                yield delta["content"]

from django.http import StreamingHttpResponse

def chatbot_streaming(message):
    for chunk in ask_openai_stream(message, model="gpt-3.5-turbo"):
        yield chunk
        yield "\n"  # Add a newline character between chunks

if __name__ == "__main__":
    response = client.chat.completions.create(
        model="gpt-4",  # Assure-toi que ton modèle est bien spécifié
        messages=[{"role": "user", "content": "Bonjour, comment vas-tu ?"}],
        stream=True  # Activation du streaming
    )

    for chunk in response:
        print(chunk, "\n")
