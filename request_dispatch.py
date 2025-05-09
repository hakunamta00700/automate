import os
import argparse
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Parse command line arguments
parser = argparse.ArgumentParser(description='Dispatch GitHub workflow for video transcription')
parser.add_argument('url', help='YouTube video URL to transcribe')
args = parser.parse_args()

# Get environment variables
token = os.getenv('GITHUB_TOKEN')
owner = os.getenv('GITHUB_OWNER')
repo = os.getenv('GITHUB_REPO')

print("url:", args.url)

if not all([token, owner, repo]):
    raise ValueError("Missing required environment variables. Please check GITHUB_TOKEN, GITHUB_OWNER, and GITHUB_REPO in .env")

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}"
}

data = {
    "event_type": "transcribe_from_url",
    "client_payload": {
        "url": args.url
    }
}

response = requests.post(
    f"https://api.github.com/repos/{owner}/{repo}/dispatches",
    headers=headers,
    data=json.dumps(data)
)