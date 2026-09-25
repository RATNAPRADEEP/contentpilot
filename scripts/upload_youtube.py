#!/usr/bin/env python3
import json
import os
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "generated", "latest.json")
VIDEO = os.path.join(ROOT, "generated", "contentpilot-latest.mp4")

CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("YOUTUBE_REFRESH_TOKEN")
PRIVACY = os.environ.get("YOUTUBE_PRIVACY", "private")

if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
    print("YouTube upload not configured; skipping.")
    sys.exit(0)

data = json.load(open(DATA, encoding="utf-8"))
source = data.get("source", {})
title = data.get("source", {}).get("title", "Today's tech discovery")
title = title[:95].rstrip()
description = (
    "A practical tech discovery from ContentPilot.\n\n"
    + "Source: " + source.get("link", "") + "\n\n"
    + "This video was automatically generated from a public source. "
      "Verify the original source before relying on any claim."
)

credentials = Credentials(
    token=None,
    refresh_token=REFRESH_TOKEN,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scopes=["https://www.googleapis.com/auth/youtube.upload"],
)
credentials.refresh(Request())

youtube = build("youtube", "v3", credentials=credentials)
body = {
    "snippet": {
        "title": title,
        "description": description,
        "categoryId": "28",
        "tags": ["technology", "AI", "automation", "developer tools", "ContentPilot"],
    },
    "status": {
        "privacyStatus": PRIVACY,
        "selfDeclaredMadeForKids": False,
    },
}

request = youtube.videos().insert(
    part="snippet,status",
    body=body,
    media_body=MediaFileUpload(VIDEO, mimetype="video/mp4", resumable=True),
)

response = None
while response is None:
    status, response = request.next_chunk()
    if status:
        print(f"Upload progress: {int(status.progress() * 100)}%")

video_id = response["id"]
print(f"YouTube upload complete: https://youtu.be/{video_id}")
