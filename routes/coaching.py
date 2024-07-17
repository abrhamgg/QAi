from flask import Blueprint, request, jsonify
from services.coaching_service import AssistantHandler, client, ASSISTANT_ID

coaching_bp = Blueprint('qai', __name__)
handler = AssistantHandler(client, ASSISTANT_ID)


@coaching_bp.route('/start-coaching', methods=['POST'])
def start_coaching():
    data = request.json
    transcription = data.get('transcription')
    sales_books = data.get('sales_books')
    call_scripts = data.get('call_scripts')

    if not transcription:
        return jsonify({'error': 'Transcription and sales books are required'}), 400

    # Create thread
    thread_id = handler.create_thread()
    print(f"Thread ID: {thread_id}")
    # thread_id = "thread_PU8cijUI6pUBSz2CfdQ9Wbrp"

    # Add message to thread
    message_id = handler.add_message_to_thread(
        thread_id, "user", transcription, sales_books, call_scripts)
    print(f"Message ID: {message_id}")

    # Run assistant and poll for result
    try:
        messages = handler.create_and_poll_run(thread_id)
        # print(messages[0]['id'])
        return jsonify({'messages': messages}), 200
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500
