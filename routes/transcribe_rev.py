from flask import Blueprint, request, jsonify, render_template
from services.highlevel_service import HighlevelService
from services.dynamo_service import DynamoService
from services.rev_service import RevService
import datetime


rev_bp = Blueprint('rev', __name__)
highlevel = HighlevelService()
dynamo = DynamoService()
rev_service = RevService()


@rev_bp.route('/rev', methods=['GET'])
def home():
    try:
        contacts = dynamo.get_all_data()
        return render_template('index.html', contacts=contacts)
    except Exception as e:
        return render_template('error.html', error=e)


@rev_bp.route('/rev/transcribe', methods=['POST'])
def transcribe():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No audio_url provided'}), 400
        required_fields = [
            'Call Recording Link', 'Caller Name (TM)', 'QA Call Transcription', 'QA OpenAI Prompt', 'contact_id', 'QA AI Call Summary', 'Call Duration', 'Coaching Opportunity', 'QA Notes', 'QA Automation Status',
        ]
        to_be_updated_fields = [
            'QA Call Transcription', 'QA AI Call Summary', 'Call Duration'
        ]
        filtered_request_obj = {key: data[key]
                                for key in required_fields if key in data}

        contact_id = filtered_request_obj['contact_id']

        automation_status_id = highlevel.get_custom_field_id_by_name(
            'QA Automation Status')

        audio_url = filtered_request_obj['Call Recording Link']

        item_data = {
            'contact_id': contact_id,
            'contact_full_name': data['full_name'],
            'property_address_full': data['Property Address Map'],
            'call_recording_link': audio_url,
            'call_duration': "",
            'transcription_status': 'Processing',
            'transcription': "",
            'summary': "",
            'phone': data['phone'],
            'prompt': data['QA OpenAI Prompt'],
            'model_type': 'Rev_AI',
            'caller_name': data['Caller Name (TM)'],
            'created_at': datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            'updated_at': datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        }
        dynamo.add_item(item_data)

        callback_url = f"https://ai.reicb.com/rev/callback?contact_id={contact_id}"
        transcript_id = rev_service.transcribe(audio_url, callback_url)

        return jsonify({'transcript': transcript_id})
    except Exception as e:
        print(e)
        return jsonify({"message": "An error occured"}), 500


@rev_bp.route('/rev/callback', methods=['POST'])
def callback():
    data = request.get_json()
    # print request query
    contact_id = request.args.get("contact_id")
    try:
        id = data['job']['id']
        duration = data['job']['duration_seconds']
        transcription = rev_service.get_transcribed_audio(id)

        # update highlevel_contact_id
        to_be_updated_fields = [
            'QA Call Transcription', 'Call Duration'
        ]
        automation_status_id = highlevel.get_custom_field_id_by_name(
            'QA Automation Status')

        item_data = {
            'contact_id': contact_id,
            "call_duration": rev_service.get_audio_length_in_minute(int(duration)),
            "transcription": transcription,
            'transcription_status': 'Finished',
            'transcribed_at': datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        }

        dynamo.update_item_by_contact_id(contact_id, item_data)

        custom_fields_with_id = {}
        for key in to_be_updated_fields:
            field_id = highlevel.get_custom_field_id_by_name(key)
            if field_id:
                custom_fields_with_id[field_id] = key

        request_data = {
            "customField": {}
        }
        for key, value in custom_fields_with_id.items():
            if value == 'QA Call Transcription':
                request_data['customField'][key] = transcription
            if value == 'Call Duration':
                request_data['customField'][key] = str(duration)
        request_data['customField'][automation_status_id] = "Finished"
        highlevel.update_custom_fields_by_id(
            contact_id, request_data)

        return jsonify(transcription)
    except:
        return jsonify({})
