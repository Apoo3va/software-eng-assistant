import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN")
response = requests.get(
    "https://api.github.com/user",
    headers={"Authorization": f"Bearer {token}"}
)
print(response.json().get("login"))