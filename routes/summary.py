from flask import Blueprint, request, jsonify
from services.summary_service import SummaryService, client
from dotenv import load_dotenv
import os
import json
from services.dynamo_service import QaiUsersDynamoService, DynamoService
from services.highlevel_service import HighlevelService
from requests import post, get
from utils import CONSTANTS, REVERSED_CONSTANTS
from models.reicb_user import ReicbUser

load_dotenv()

AUTH_URL = os.getenv('AUTH_URL')
qai_service = QaiUsersDynamoService()
highlevel_service = HighlevelService()
dynamo_service = DynamoService()
CUSTOM_FIELDS = {}

SUMMARY_ASSISTANT_ID = os.getenv(
    "SUMMARY_ASSISTANT_ID", "asst_fbrJlxGhqXhm85WDfNGekBnU")
SUMMARY_ASSISTANT_ID = "asst_fbrJlxGhqXhm85WDfNGekBnU"
print(f"SUMMARY_ASSISTANT_ID: {SUMMARY_ASSISTANT_ID}")

summary_bp = Blueprint('summary', __name__)
handler = SummaryService(client, SUMMARY_ASSISTANT_ID)


def check_summary_request():
    calldi_user = qai_service.get_user_by_location_id('2Q02CtA3t4WM7BjDCi98')
    if not calldi_user:
        return False
    highlevel_service = HighlevelService(
        calldi_user['token'], calldi_user['location_id'])
    # check if the token is valid
    result = highlevel_service.get_custom_fields()
    CUSTOM_FIELDS = result
    if not result:
        print("Refreshing token")
        # refresh token by sending request to endpoint /auth/refresh
        resp = post(
            f'{AUTH_URL}/auth/refresh?location_id={calldi_user["location_id"]}&refresh_token={calldi_user["refresh"]}&code=1')
        highlevel_service = HighlevelService(
            resp.json()['access_token'], calldi_user['location_id'])
        calldi_user['token'] = resp.json()['access_token']
    return CUSTOM_FIELDS, calldi_user['token']


@summary_bp.route('/start-summary', methods=['POST'])
def start_summary():
    status = check_summary_request()
    if not status:
        return jsonify({'error': 'Access to Highlevel CRM Not Found for the user'}), 400

    CUSTOM_FIELDS = status[0]
    # print(f"CUSTOM_FIELDS: {CUSTOM_FIELDS['customFields']}")
    data = request.get_json()
    transcription = data.get('transcription')

    if not transcription or not data:
        return jsonify({'error': 'Transcription or Data missing'}), 400

    if 'contact_id' not in data:
        return jsonify({'error': 'No contact_id provided'}), 400
    contact_id = data['contact_id']
    # Create thread
    thread_id = handler.create_thread()

    # Add message to thread
    handler.add_message_to_thread(
        thread_id, "user", transcription)

    # Run assistant and poll for result
    try:
        messages = handler.create_and_poll_run(thread_id)
        response = messages['response']
        # convert response json string to json object
        response = json.loads(response)
        summary = build_summary(response)

        to_be_updated_fields = [CONSTANTS[key]
                                for key in response.keys() if key in CONSTANTS]
        # Get custom fields with id and store them in a dic
        custom_fields_with_id = {}
        for cf in CUSTOM_FIELDS['customFields']:
            if cf['name'] in to_be_updated_fields:
                custom_fields_with_id[cf['id']] = cf['name']

        # Prepare request data
        request_data = {
            "customFields": []
        }
        keys = response.keys()
        for key, value in custom_fields_with_id.items():
            if REVERSED_CONSTANTS[value] in keys:
                new_obj = {
                    "id": key,
                    "value": response[REVERSED_CONSTANTS[value]]['value'],
                    "field_name": custom_fields_with_id[key]
                }
                request_data["customFields"].append(new_obj)

        # Update highlevel with the extracted information
        highlevel_service = HighlevelService(
            token=status[1], location_id='2Q02CtA3t4WM7BjDCi98')
        highlevel_service.update_custom_fields_by_id(
            contact_id, request_data)
        result = dynamo_service.update_item_by_contact_id(contact_id, data)

        if result:
            return jsonify({"message": "Sumamary added", "updated_fields": custom_fields_with_id, "summary": summary})
        return jsonify({"error": "Unable to add summary"})

    except RuntimeError as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


def build_summary(call_data):
    # Initialize parts of the summary
    call_summary = []
    to_be_discussed = []

    # Iterate through the JSON keys and values
    for key, value in call_data.items():
        if isinstance(value, dict) and "value" in value:
            call_summary.append(f"{key}: {value['value']}.")
        elif isinstance(value, str):
            call_summary.append(f"{key}: {value}.")
        else:
            to_be_discussed.append(key)

    # Add the "TO BE DISCUSSED" section if there are items
    if to_be_discussed:
        call_summary.append("\nTO BE DISCUSSED:")
        for item in to_be_discussed:
            call_summary.append(f"- {item}")

    # Join all parts of the summary
    summary = "\n".join(call_summary)

    return summary
