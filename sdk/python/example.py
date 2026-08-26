"""
AWS Bedrock AI Gateway - Python Quickstart
Using standard OpenAI official Python SDK
"""

import os
from openai import OpenAI

# Initialize client with our Gateway endpoint and your API key
client = OpenAI(
    base_url=os.environ.get("BEDROCK_GATEWAY_URL", "http://localhost:8000/v1"),
    api_key=os.environ.get("BEDROCK_API_KEY", "sk-live-sample-key-123")
)

def chat_stream():
    print("Streaming response from AWS Bedrock (Claude 3.5 Sonnet)...")
    response = client.chat.completions.create(
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        messages=[
            {"role": "system", "content": "You are an expert cloud architect."},
            {"role": "user", "content": "Explain the advantages of an AI Gateway abstraction on top of AWS Bedrock."}
        ],
        temperature=0.7,
        stream=True
    )

    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
    print("\n")

def list_models():
    models = client.models.list()
    print("Available Models:")
    for m in models.data:
        print(f" - {m.id} ({getattr(m, 'name', '')})")

if __name__ == "__main__":
    list_models()
    chat_stream()
