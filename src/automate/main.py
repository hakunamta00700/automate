from typing import Union

from fastapi import FastAPI
from .youtube_lib import get_transcript, summarize
import uvicorn

app = FastAPI()


@app.get("/summarize")
def summarize_youtube_video(url: str):
    # 1. Get the video id
    video_id = url.split("v=")[1]
    # 2. Get the video transcript
    transcript = get_transcript(video_id)
    # 3. Summarize the transcript
    summary = summarize(transcript)
    return {"summary": summary}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


def run():
    uvicorn.run("automate.main:app", host="0.0.0.0", port=8000, reload=True)
