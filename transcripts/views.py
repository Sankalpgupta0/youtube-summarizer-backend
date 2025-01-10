from django.http import JsonResponse
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import VideoUnavailable, NoTranscriptFound, TranscriptsDisabled
import re

import google.generativeai as genai
from django.conf import settings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

prompt="""You are Yotube video summarizer. You will be taking the transcript text
and summarizing the entire video and providing the important summary in points
within 500 words. Please provide the summary of the text given here:  """

def extract_transcript(request):
    youtube_video_url = request.GET.get('youtube_video_url')
    if not youtube_video_url:
        return JsonResponse({"error": "youtube_video_url parameter is required"}, status=400)

    try:
        # Extract the video ID using regex for robustness
        video_id_match = re.search(r"(?:v=|youtu\.be/|embed/)([a-zA-Z0-9_-]+)", youtube_video_url)
        if not video_id_match:
            return JsonResponse({"error": "Invalid YouTube URL"}, status=400)

        video_id = video_id_match.group(1)

        # Fetch the transcript
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([item["text"] for item in transcript_text])
        # print("transcript", transcript)
        
        summary = generate_gemini_content(transcript, prompt)

        return JsonResponse({"summary": summary}, status=200)

    except VideoUnavailable:
        return JsonResponse({"error": "The video is unavailable or does not exist."}, status=404)
    except NoTranscriptFound:
        return JsonResponse({"error": "No transcript found for the video."}, status=404)
    except TranscriptsDisabled:
        return JsonResponse({"error": "Transcripts are disabled for this video."}, status=403)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)




def generate_gemini_content(transcript_text, prompt):
    model=genai.GenerativeModel("gemini-pro")
    response=model.generate_content(prompt+transcript_text)
    return response.text

