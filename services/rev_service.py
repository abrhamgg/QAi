
from time import sleep
from rev_ai import apiclient
from dotenv import load_dotenv
from rev_ai.models import CustomVocabulary, CustomerUrlData
import os
from utils import load_from_dynamo
load_dotenv()

token = "02R6JxxwApzty3rIv_yBy8uetYvdZGmZxZ0AYw7z6J_H7__09hxNlkyS3m8U2CI3SE8cEwkRr_sGbfbjvS4zOdR0BJHr4"
REV_API_KEY = os.getenv('REV_API_KEY')
KEYS = load_from_dynamo()
REV_API_KEY = KEYS.get("rev_key", "")


class RevService:
    def __init__(self):
        self.client = apiclient.RevAiAPIClient(REV_API_KEY)

    def get_audio_length_in_minute(self, seconds):
        seconds = seconds % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60

        return "%d:%02d:%02d" % (hour, minutes, seconds)

    def transcribe(self, url, callback):
        notification_url = callback
        job = self.client.submit_job_url(
            url,
            speakers_count=2,
            notification_config=CustomerUrlData(url=notification_url)
        )
        return job.id

    def get_transcribed_audio(self, id):
        if not id:
            return None

        client = apiclient.RevAiAPIClient(token)

        # Get job details
        job_details = client.get_transcript_json(id)
        transcript_text = client.get_transcript_text(id)
        return transcript_text

