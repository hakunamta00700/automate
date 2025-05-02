from youtube_transcript_api import YouTubeTranscriptApi


def get_transcript(video_id: str):
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return transcript


def summarize(transcript: list):
    return transcript