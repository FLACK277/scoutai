import os
import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
print("API KEY:", "present" if api_key else "missing")

if not api_key:
    print("API KEY missing")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "model": "mixtral-8x7b-32768",
    "messages": [{"role": "user", "content": "Hello"}],
}

try:
    resp = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
    print("STATUS:", resp.status_code)
    print("RESPONSE:", resp.text)
except Exception as e:
    print("ERROR:", e)
