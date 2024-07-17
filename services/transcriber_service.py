import assemblyai as aai
from dotenv import load_dotenv
import os
import requests
import pytz
import datetime
from utils import load_from_dynamo

load_dotenv()


ASSEMBLY_CALLBACK_URL = os.getenv('ASSEMBLY_CALLBACK_URL')
api_key = os.getenv('ASSEMBLY_API_KEY')


aai.settings.api_key = api_key
config = aai.TranscriptionConfig(
    dual_channel=True,
    summarization="conversational",
    webhook_url=ASSEMBLY_CALLBACK_URL,
    speech_model=aai.SpeechModel.best
)


class TranscriberService:
    def __init__(self):
        self.transcriber = aai.Transcriber()

    def time_in_est(self):
        utc_now = datetime.datetime.now(pytz.utc)
        est_now = utc_now.astimezone(pytz.timezone('US/Eastern'))
        return est_now.strftime("%Y-%m-%d %I:%M %p")

    def get_audio_length_in_minute(self, seconds):
        seconds = seconds % (24 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60

        return "%d:%02d:%02d" % (hour, minutes, seconds)

    def time_to_seconds(self, time_str):
        hours, minutes, seconds = map(int, time_str.split(':'))
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds

    def format_time(self, input_time, call_duration):

        input_seconds = self.time_to_seconds(input_time)
        call_seconds = self.time_to_seconds(call_duration)

        if call_seconds == 0:
            return "Call duration cannot be zero"

        percentage = (input_seconds / call_seconds) * 100

        hours, remainder = divmod(input_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours == 0:
            formatted_time = f"{minutes} minutes {seconds} seconds"
        else:
            formatted_time = f"{hours} hours {minutes} minutes {seconds} seconds"

        return f"{formatted_time} ({percentage:.2f}%)"

    def transcribe(self, audio_url):
        transcript = self.transcriber.transcribe(audio_url, config=config)
        summary = transcript.json_response['summary']
        labeled_text = ""
        for utterance in transcript.utterances:
            labeled_text += f"Speaker {utterance.speaker}: {utterance.text}\n"

        full_text = transcript.json_response['text']
        audio_duration = self.get_audio_length_in_minute(
            transcript.audio_duration)

        return [full_text, labeled_text, summary, audio_duration]

    def transcribe_async(self, audio_url, webhook_url, contact_id, caller_name, contact_name):
        # Define the headers for the API request
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

        # Define the payload with only the specified parameters
        payload = {
            "audio_url": audio_url,
            "dual_channel": True,
            "webhook_url": f"{webhook_url}?contact_id={contact_id}",
            "language_detection": True,
            "punctuate": True,

        }
        print(payload['webhook_url'])
        # Send the POST request to the API endpoint
        response = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            headers=headers,
            json=payload
        )

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            response_data = response.json()
            # Return the transcript ID
            return response_data['id']
        else:
            # Handle errors (raise an exception or return None)
            return response.status_code

    def get_transcribed_audio(self, id):
        # Define the headers for the API request
        headers = {
            "Authorization": api_key
        }

        # Send the GET request to the API endpoint
        response = requests.get(
            f"https://api.assemblyai.com/v2/transcript/{id}",
            headers=headers
        )

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            response_data = response.json()
            # Return the transcript text
            return response_data
        else:
            # Handle errors (raise an exception or return None)
            response.raise_for_status()

    def milliseconds_to_hhmmss(self, ms):
        seconds = ms // 1000
        minutes = seconds // 60
        hours = minutes // 60
        return f"{hours:02}:{minutes % 60:02}:{seconds % 60:02}"

    def format_transcript(self, transcript_data, caller_name, contact_name):
        try:
            label_dict = {
                '1': caller_name,
                '2': contact_name

            }
            labeled_text = ""
            speaker_times = {}
            utterance_data = []
            for utterance in transcript_data:
                speaker = utterance.get("speaker", "")
                start_time = self.milliseconds_to_hhmmss(
                    utterance.get("start", 0))
                end_time = self.milliseconds_to_hhmmss(utterance.get("end", 0))
                text = utterance.get("text", "")
                utterance_data.append(
                    {
                        "start": start_time,
                        "end": end_time,
                        "speaker": [speaker, label_dict[speaker]],
                        "text": text
                    }
                )

                # loop through the words in the utterance, get end - start add them to the total talk time
                for word in utterance.get("words", []):
                    duration = word.get("end", 0) - word.get("start", 0)
                    if speaker in speaker_times:
                        speaker_times[speaker] += duration
                    else:
                        speaker_times[speaker] = duration
                # Calculate duration of the utterance
                duration = utterance.get("end", 0) - utterance.get("start", 0)
                if label_dict[speaker] == caller_name:
                    labeled_text += f"{start_time} - {end_time}  Speaker {label_dict[speaker]}  {text}\n"
                else:
                    labeled_text += f"{start_time} - {end_time}  Speaker {speaker}  {text}\n"
            # Convert total talk time to hh:mm:ss format
            total_talk_times = {
                speaker: self.milliseconds_to_hhmmss(duration)
                for speaker, duration in speaker_times.items()
            }

            return labeled_text, total_talk_times, utterance_data
        except Exception as e:
            print(e)
            return
