from openai import OpenAI
from openai import AssistantEventHandler
import os
import json

# Configuration
GPT_API_KEY = os.getenv("GPT_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID", "asst_XEdJxOMouRiA796r73YQFPnV")

# OpenAI Client Initialization
client = OpenAI(api_key=GPT_API_KEY)


class AssistantHandler:
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

    def add_message_to_thread(self, thread_id, role, transcription, sales_books, call_scripts):
        sales_books_formatted = "\n".join(sales_books)
        print(sales_books_formatted)
        print(sales_books)

        message_content = f"""

        Call Transcription:
        {transcription}

        Sales Books:
        {sales_books_formatted}

        Call Scripts:
        {call_scripts}

        Coaching Feedback:
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
            event_handler=EventHandler()
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

    def _serialize_messages(self, messages):
        serialized = []
        for message in messages:
            serialized.append({
                'id': message.id,
                'role': message.role,
                'content': self._serialize_content(message.content),
                # 'created_at': message.created_at.isoformat() if message.created_at else None
            })
        return serialized

    def _serialize_content(self, content):
        try:
            # If content is already a string, return it directly
            if isinstance(content, str):
                return content
            # If content is not a string, convert it to a JSON string
            return json.dumps(content)
        except (TypeError, ValueError) as e:
            # Handle error in content serialization
            print(f"Error serializing content: {e}")
            return str(content)

# Event Handler


class EventHandler(AssistantEventHandler):
    def on_text_created(self, text) -> None:
        print(f"\nassistant > {text}", end="", flush=True)

    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)

    def on_tool_call_delta(self, delta, snapshot):
        if delta.type == 'code_interpreter':
            if delta.code_interpreter.input:
                print(delta.code_interpreter.input, end="", flush=True)
            if delta.code_interpreter.outputs:
                print(f"\n\noutput >", flush=True)
                for output in delta.code_interpreter.outputs:
                    if output.type == "logs":
                        print(f"\n{output.logs}", flush=True)


def main():
    handler = AssistantHandler(client, ASSISTANT_ID)

    # Create thread
    thread_id = handler.create_thread()
    print(f"Thread ID: {thread_id}")

    # Example data
    transcription = "Agent: Hello, this is John from XYZ Realty. How can I assist you today? Customer: Hi John, I'm interested in buying a new home."
    sales_books = "Title: 'Mastering Real Estate Sales' Chapter 3: Building Rapport with Clients."
    call_scripts = "- Greet the client: 'Hello, this is [Your Name] from [Your Company]. How can I assist you today?'"

    # Add message to thread
    message_id = handler.add_message_to_thread(
        thread_id, "user", transcription, sales_books, call_scripts)
    print(f"Message ID: {message_id}")

    # Run assistant and poll for result
    messages = handler.create_and_poll_run(thread_id)
    print(messages)


if __name__ == '__main__':
    main()
