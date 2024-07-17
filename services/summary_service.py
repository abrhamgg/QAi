from openai import OpenAI
import os
from openai import AssistantEventHandler


SUMMARY_ASSISTANT_ID = os.getenv("SUMMARY_ASSISTANT_ID")
GPT_API_KEY = os.getenv("GPT_API_KEY")

client = OpenAI(api_key=GPT_API_KEY)


class SummaryService:
    def __init__(self, client, assistant_id):
        self.client = client
        self.assistant_id = assistant_id

    def create_thread(self):
        response = self.client.beta.threads.create()
        if hasattr(response, 'id'):
            return response.id
        else:
            raise ValueError(
                "Thread response does not have an 'id' attribute.")

    def add_message_to_thread(self, thread_id, role, transcription):
        message_content = f"""
        Call Transcription:
        {transcription}
        """
        response = self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role=role,
            content=message_content
        )
        return response.id

    def run_assistant(self, thread_id):
        with self.client.beta.threads.runs.stream(
            thread_id=thread_id,
            assistant_id=self.assistant_id,
            event_handler=AssistantEventHandler()
        ) as stream:
            print("Running assistant...")
            stream.until_done()

    def create_and_poll_run(self, thread_id):
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=self.assistant_id,
        )
        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id)
            return {"response": messages.data[0].content[0].text.value,
                    "id": messages.data[0].id,
                    "assistant_id": messages.data[0].assistant_id,
                    }
        else:
            raise RuntimeError("Run did not complete successfully.")
