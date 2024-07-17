from flask import Blueprint, request, jsonify
from requests import post, get
from services.dynamo_service import DynamoService, QaiUsersDynamoService
from services.highlevel_service import HighlevelService
from utils import extract_dynamic_key_value_pairs, CONSTANTS, REVERSED_CONSTANTS
from dotenv import load_dotenv
from flask_login import current_user
import os
from models.reicb_user import ReicbUser, ReicbUserSetting

load_dotenv()

AUTH_URL = os.getenv('AUTH_URL')


dynamo_service = DynamoService()
dynamo_bp = Blueprint('dynamo', __name__)
highlevel_service = HighlevelService()
qai_service = QaiUsersDynamoService()


@dynamo_bp.route('/dynamo/summary', methods=['POST'])
def update_summary():
    calldi_user = qai_service.get_user_by_location_id('2Q02CtA3t4WM7BjDCi98')
    if not calldi_user:
        return jsonify({'error': 'Access to Highlevel CRM Not Found for the user'}), 400
    highlevel_service = HighlevelService(
        calldi_user['token'], calldi_user['location_id'])
    # check if the token is valid
    result = highlevel_service.get_custom_fields()
    if not result:
        # refresh token by sending request to endpoint /auth/refresh
        resp = post(
            f'{AUTH_URL}/auth/refresh?location_id={calldi_user["location_id"]}&refresh_token={calldi_user["refresh"]}&code=1')
        highlevel_service = HighlevelService(
            resp.json()['access_token'], calldi_user['location_id'])
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    if 'contact_id' not in data or 'QA AI Call Summary' not in data:
        return jsonify({'error': 'No contact_id provided'}), 400

    contact_id = data['contact_id']
    summary = data['QA AI Call Summary']
    data = {
        "summary": summary
    }
    keys = extract_dynamic_key_value_pairs(summary)

    to_be_updated_fields = []
    for key in keys:
        if key in CONSTANTS:
            to_be_updated_fields.append(CONSTANTS[key])

    custom_fields_with_id = {}
    for key in to_be_updated_fields:
        field_id = highlevel_service.get_custom_field_id_by_name(key)
        if field_id:
            custom_fields_with_id[field_id] = key
        else:
            print(f"Field {key} not found")
    request_data = {
        "customFields": []
    }
    for key, value in custom_fields_with_id.items():
        if REVERSED_CONSTANTS[value] in keys:
            new_obj = {
                "id": key,
                "value": keys[REVERSED_CONSTANTS[value]],
                "field_name": custom_fields_with_id[key]
            }
            request_data["customFields"].append(new_obj)
    print(f"Request data: {request_data}")
    # TODO: The summary will be in the json content, and those json value be used when populating the data into individual boxes.

    # Update highlevel with the extracted information
    highlevel_service.update_custom_fields_by_id(
        contact_id, request_data)
    result = dynamo_service.update_item_by_contact_id(contact_id, data)

    if result:
        return jsonify({"message": "Sumamary added", "updated_fields": custom_fields_with_id})
    return jsonify({"error": "Unable to add summary"})


@dynamo_bp.route('/dynamo/location', methods=['POST'])
def update_contact_location():
    data = request.get_json()
    if not data or 'customData' not in data:
        return jsonify({'error': 'No data provided'}), 400

    custom_data = data['customData']

    try:
        current_contact_id = custom_data['current_contact_id']
        location_id = custom_data['location_id']
        original_contact_id = custom_data['original_contact_id']

        # update contact by adding location_id
        item = {
            "location_id": location_id,
            'sub_account_contact_id': current_contact_id,
            'pushed_to': custom_data['location_name']
        }
        result = dynamo_service.update_item_by_contact_id(
            original_contact_id, item)
        if result:
            return jsonify({"message": "Location updated"}), 201
        return jsonify({"error": "Unable to update location"}), 400
    except Exception as e:
        print(f"Error updating location: {e}")
        return jsonify({"error": str(e)}), 400


@dynamo_bp.route('/dynamo/update-script', methods=['POST'])
def update_script():
    try:
        data = request.get_json()
        # location_id = current_user.location_id
        if 'script' not in data:
            return jsonify({'error': 'No location_id provided'}), 400
        script = data['script']
        if not script['script_name'] or not script['script_content']:
            return jsonify({'error': 'No script provided'}), 400
        script_name = script['script_name']
        script_content = script['script_content']

        user_settings = ReicbUserSetting.get(current_user.get_id())
        user_settings.coach.scripts[script_name] = script_content
        user_settings.save()
        return jsonify({"success": "updated"}), 200
    except Exception as e:
        print(f"Error updating script: {e}")
        return jsonify({'error': str(e)}), 400


@dynamo_bp.route('/dynamo/get-scripts', methods=['GET'])
def get_script():
    try:
        user = ReicbUserSetting.get(current_user.get_id())
        return jsonify(user.coach['scripts']), 200
    except Exception as e:
        print(f"Error getting script: {e}")
        return jsonify({"error": "Unable to get script"}), 400

# delete scripts


@dynamo_bp.route('/dynamo/delete-scripts', methods=['POST'])
def delete_script():
    try:
        data = request.get_json()
        print(data)
        script_names = data['script_names']
        # script_names is a list of script names to be deleted
        if not script_names:
            return jsonify({'error': 'No script provided'}), 400
        user_settings = ReicbUserSetting.get(current_user.get_id())

        for script_name in script_names:
            if not script_name:
                return jsonify({'error': 'No script provided'}), 400
            del user_settings.coach.scripts[script_name]
        user_settings.save()

        return jsonify({"success": "deleted"}), 200
    except Exception as e:
        print(f"Error deleting script: {e}")
        return jsonify({'error': str(e)}), 400


@dynamo_bp.route('/dynamo/rating', methods=['POST'])
def update_rating():
    data = request.get_json()
    if not data or 'contact_id' not in data or 'rating' not in data:
        return jsonify({'error': 'No data provided'}), 400

    contact_id = data['contact_id']
    rating = data['rating']
    item = {
        "rating": rating
    }
    result = dynamo_service.update_item_by_contact_id(contact_id, item)

    if result:
        return jsonify({"message": "Rating added"})
    return jsonify({"error": "Unable to add rating"})


@dynamo_bp.route('/dynamo/admin', methods=['POST', 'GET'])
def save_crm_key():
    import boto3
    import os
    MY_AWS_ACCESS_KEY_ID = os.getenv('MY_AWS_ACCESS_KEY_ID')
    MY_AWS_SECRET_ACCESS_KEY = os.getenv('MY_AWS_SECRET_ACCESS_KEY')
    db = boto3.resource('dynamodb', region_name='us-east-1',
                        aws_access_key_id=MY_AWS_ACCESS_KEY_ID, aws_secret_access_key=MY_AWS_SECRET_ACCESS_KEY)
    if request.method == "POST":
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        crm_key = data['crm_key']
        assembly_key = data['assembly_key']
        rev_key = data['rev_key']
        password = data['password']
        PASSWORD = os.getenv('PASSWORD')
        if password != PASSWORD:
            return jsonify({'error': 'Invalid password'}), 400

        data = {
            "crm_key": crm_key,
            "assembly_key": assembly_key,
            "rev_key": rev_key,
            "crm_name": data['name']
        }
        try:
            table = db.Table('qai-crm-key')
            table.put_item(Item=data)
            return jsonify({"message": "Keys added"})
        except Exception as e:
            print(f"Unable to add key: {e}")
            return jsonify({"error": str(e)}), 400

    if request.method == "GET":
        try:
            table = db.Table('qai-crm-key')
            response = table.scan()
            data = response['Items'][0]
            if data:
                return jsonify(data)
            else:
                return jsonify({"error": "No keys found"})
        except Exception as e:
            print(f"Unable to get keys: {e}")
            return jsonify({"error": str(e)}), 400
