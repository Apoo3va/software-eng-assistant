from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()  # reads .env file

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "Say hello and tell me one fact about software engineering."}
    ]
)

print(response.choices[0].message.content)