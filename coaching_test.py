from openai import AssistantEventHandler
from typing_extensions import override
import requests
from dotenv import load_dotenv
import os
import openai
from openai import OpenAI

load_dotenv()

GPT_API_KEY = os.getenv("GPT_API_KEY")
# Replace with your OpenAI API key and assistant endpoint
GPT_API_KEY = "sk-proj-SBIPgD1p284RBOLTk0KNT3BlbkFJBymDz6lzeFjWHZzLqO4B"
api_key = GPT_API_KEY
assistant_id = 'asst_XEdJxOMouRiA796r73YQFPnV'

client = OpenAI(api_key=api_key)
print(api_key)


def create_thread():
    response = client.beta.threads.create()
    return response


# Create the thread
thread_response = create_thread()

# Check the type of response object
print(f"Response type: {type(thread_response)}")

# Accessing the thread ID correctly
if hasattr(thread_response, 'id'):
    thread_id = thread_response.id
    print(f"Thread ID: {thread_id}")
else:
    print("Thread response does not have an 'id' attribute.")


def add_message_to_thread(thread_id, role, transcription, sales_books, call_scripts):
    # Format the message content based on the input parameters
    message_content = f"""
    Coach QAI, evaluate the following call transcription based on the provided sales books and call scripts. Provide detailed coaching feedback and suggestions for improvement.

    Call Transcription:
    {transcription}

    Sales Books:
    {sales_books}

    Call Scripts:
    {call_scripts}

    Coaching Feedback:
    """

    # Use the correct method to add a message to the thread
    response = client.beta.threads.messages.create(
        thread_id=thread_id,
        role=role,
        content=message_content
    )

    return response


# Example data
transcription = "Agent: Hello, this is John from XYZ Realty. How can I assist you today? Customer: Hi John, I'm interested in buying a new home."
sales_books = "Title: 'Mastering Real Estate Sales' Chapter 3: Building Rapport with Clients."
call_scripts = "- Greet the client: 'Hello, this is [Your Name] from [Your Company]. How can I assist you today?'"

message_response = add_message_to_thread(
    thread_id, "user", transcription, sales_books, call_scripts)
# print(type(message_response))
# print(f"Message ID: {message_response.id}")


# Define an event handler to process streaming responses

class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > {text}", end="", flush=True)

    @override
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


def run_assistant(thread_id, assistant_id):
    with client.beta.threads.runs.stream(
        thread_id=thread_id,
        assistant_id=assistant_id,
        event_handler=EventHandler()
    ) as stream:
        print("Running assistant...")
        stream.until_done()


# run_assistant(thread_id, assistant_id)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread_id,
    assistant_id=assistant_id,
)
if run.status == 'completed':
    messages = client.beta.threads.messages.list(
        thread_id=thread_id
    )
    print(messages)
else:
    print(run.status)
