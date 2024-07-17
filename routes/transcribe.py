from flask import Blueprint, request, jsonify
from services.transcriber_service import TranscriberService
from services.highlevel_service import HighlevelService
from services.dynamo_service import DynamoService, QaiUsersDynamoService
import datetime
from requests import post, get
from flask_login import current_user
import os
from dotenv import load_dotenv

load_dotenv()

ASSEMBLY_CALLBACK_URL = os.getenv('ASSEMBLY_CALLBACK_URL')
AUTH_URL = os.getenv('AUTH_URL')


transcribe_bp = Blueprint('transcribe', __name__)
transcriber = TranscriberService()
highlevel = HighlevelService()
dynamo = DynamoService()
qai_service = QaiUsersDynamoService()


@transcribe_bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    # data = request.data
    # data = data.decode('utf-8')
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No audio_url provided'}), 400
        required_fields = [
            'Call Recording Link', 'Caller Name (TM)', 'QA Call Transcription', 'QA OpenAI Prompt', 'contact_id', 'QA AI Call Summary', 'Call Duration', 'Coaching Opportunity', 'QA Notes', 'QA Automation Status',
        ]
        to_be_updated_fields = [
            'QA Call Transcription', 'QA AI Call Summary', 'Call Duration', 'Caller Name (TM)'
        ]
        filtered_request_obj = {key: data[key]
                                for key in required_fields if key in data}

        contact_id = filtered_request_obj['contact_id']

        automation_status_id = highlevel.get_custom_field_id_by_name(
            'QA Automation Status')

        audio_url = filtered_request_obj['Call Recording Link']

        transcript = transcriber.transcribe(audio_url)
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
                request_data['customField'][key] = transcript[1]
            if value == 'QA AI Call Summary':
                request_data['customField'][key] = transcript[2]
            if value == 'Call Duration':
                request_data['customField'][key] = transcript[3]
            if value == 'Caller Name (TM)':
                request_data['customField'][key] = data['Caller Name (TM)']
        request_data['customField'][automation_status_id] = "Finished"
        highlevel.update_custom_fields_by_id(
            contact_id, request_data)

        # Save to DynamoDB
        item_data = {
            'contact_id': contact_id,
            'contact_full_name': data['full_name'],
            'property_address_full': data['Property Address Map'],
            'call_recording_link': audio_url,
            'call_duration': transcript[3],
            'transcription_status': 'Finished',
            'transcription': transcript[1],
            'summary': transcript[2],
            'phone': data['phone'],
            'prompt': data['QA OpenAI Prompt'],
            'model_type': 'AssemblyAI',
            'created_at': datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            'updated_at': datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            'transcribed_at': datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p"),
            'caller_name': data['Caller Name (TM)']

        }
        dynamo.add_item(item_data)

        return jsonify({'message': 'Transcription successful', "duration": transcript[3], 'transcript': transcript[1], 'summary': transcript[2]})
    except Exception as e:
        return jsonify({'message': 'Transcription failed', 'error': str(e)})


@transcribe_bp.route('/transcribe/async', methods=['POST'])
def transcribe_audio_async():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No audio_url provided'}), 400
        audio_url = data['Call Recording Link']

        item_data = {
            'contact_id': data['contact_id'],
            'contact_full_name': data['full_name'],
            'property_address_full': data['Property Address Map'],
            'call_recording_link': audio_url,
            'call_duration': "",
            'transcription_status': 'Processing',
            'transcription': "",
            'summary': "",
            'phone': data['phone'],
            'prompt': data['QA OpenAI Prompt'],
            'model_type': 'AssemblyAI',
            'caller_name': data['Caller Name (TM)'],
            'created_at': transcriber.time_in_est(),
            'updated_at': transcriber.time_in_est(),
            'location_id': '2Q02CtA3t4WM7BjDCi98'
        }
        dynamo.add_item(item_data)
        id = transcriber.transcribe_async(
            audio_url, ASSEMBLY_CALLBACK_URL, data['contact_id'], data['Caller Name (TM)'], data['full_name'])
        return jsonify({'transcript': id})
    except Exception as e:
        print(e)
        return jsonify({'message': 'An error occured'}), 500


@transcribe_bp.route('/assembly/callback', methods=['GET', 'POST'])
def transcribe_async():
    try:
        calldi_user = qai_service.get_user_by_location_id(
            '2Q02CtA3t4WM7BjDCi98')
        highlevel = HighlevelService(
            calldi_user['token'], calldi_user['location_id'])

        # check if the token is valid
        result = highlevel.get_custom_fields()
        if not result:
            # refresh token by sending request to endpoint /auth/refresh
            resp = post(
                f'{AUTH_URL}/auth/refresh?location_id={calldi_user["location_id"]}&refresh_token={calldi_user["refresh"]}&code=1')
            highlevel = HighlevelService(
                resp.json()['access_token'], calldi_user['location_id'])

        data = request.get_json()
        contact_id = request.args.get("contact_id")
        contact = dynamo.get_item_by_contact_id(contact_id)
        # update highlevel_contact_id
        to_be_updated_fields = [
            'QA Call Transcription', 'Call Duration', 'Speaker A Talk Time (Seconds)', 'Speaker B Talk Time (Seconds)', 'Speaker A Talk Time (Percentage)', 'Speaker B Talk Time (Percentage)', 'Dead Air (Percentage)', 'Dead Air (Seconds)'
        ]
        automation_status_id = highlevel.get_custom_field_id_by_name(
            'QA Automation Status')
        if data['status'] == 'completed':
            transcript_id = data['transcript_id']
            transcript = transcriber.get_transcribed_audio(transcript_id)
            utterances = transcript['utterances']
            formatted_text = transcriber.format_transcript(
                utterances, contact['caller_name'], contact['contact_full_name'])
            audio_duration = transcriber.get_audio_length_in_minute(
                transcript['audio_duration'])

            confidence = transcript['confidence']
            utterances = formatted_text[2]
            # loop through utterance and get the total number of words
            total_words = 0
            for utterance in utterances:
                total_words += len(utterance['text'].split())

            item_data = {
                'contact_id': contact_id,
                "call_duration": audio_duration,
                "transcription": formatted_text[0],
                'confidence': str(confidence),
                'talk_time': formatted_text[1],
                'transcription_status': 'Finished',
                'transcribed_at': transcriber.time_in_est(),
                'utterances': formatted_text[2],
                'words': total_words
            }
            talk_time = formatted_text[1]
            speaker_a_talk_time = transcriber.time_to_seconds(talk_time['1'])
            speaker_b_talk_time = transcriber.time_to_seconds(talk_time['2'])
            call_duration = transcriber.time_to_seconds(audio_duration)
            silence_time = call_duration - speaker_a_talk_time - speaker_b_talk_time

            # Get the percentage in the following format 0 minutes 11 seconds (23.40%)
            speaker_a_formatted_percentage = transcriber.format_time(
                talk_time['1'], audio_duration)
            speaker_b_formatted_percentage = transcriber.format_time(
                talk_time['2'], audio_duration)
            if silence_time < 0:
                silence_time = 0
            silence_formatted_percentage = transcriber.format_time(
                str(datetime.timedelta(seconds=silence_time)), audio_duration)

            dynamo.update_item_by_contact_id(contact_id, item_data)

            custom_fields_with_id = {}
            for key in to_be_updated_fields:
                field_id = highlevel.get_custom_field_id_by_name(key)
                if field_id:
                    custom_fields_with_id[field_id] = key
                else:
                    print(f"Field {key} not found")
            request_data = {
                "customFields": []
            }
            for key, value in custom_fields_with_id.items():
                if value == 'QA Call Transcription':
                    request_data['customFields'].append(
                        {"id": key, "key": value, "field_value": formatted_text[0]})
                if value == 'Call Duration':
                    request_data['customFields'].append(
                        {"id": key, "key": value, "field_value": audio_duration})
                if value == 'Speaker A Talk Time (Seconds)':
                    request_data['customFields'].append(
                        {"id": key, "key": value, "field_value": speaker_a_talk_time})
                if value == 'Speaker B Talk Time (Seconds)':
                    request_data['customFields'].append(
                        {"id": key, "key": value, "field_value": speaker_b_talk_time})
                if value == 'Speaker A Talk Time (Percentage)':
                    request_data['customFields'].append(
                        {"id": key, "key": value, "field_value": speaker_a_formatted_percentage})
                if value == 'Speaker B Talk Time (Percentage)':
                    request_data['customFields'].append(
                        {"id": key, "key": value, "field_value": speaker_b_formatted_percentage})
                if value == 'Dead Air (Percentage)':
                    request_data['customFields'].append(
                        {"id": key, "key": value, "field_value": silence_formatted_percentage})
                if value == 'Dead Air (Seconds)':
                    request_data['customFields'].append(
                        {"id": key, "key": value, "field_value": silence_time})
            request_data['customFields'].append(
                {"id": automation_status_id, "key": "QA Automation Status", "field_value": "Finished"})
            highlevel.update_custom_fields_by_id(
                contact_id, request_data)

            return jsonify({'transcript': formatted_text})
        else:
            return jsonify({'message': 'Transcription failed'}), 500
    except Exception as e:
        # print full error and line the code broke

        print(e)
        print("Error on line {}".format(e.__traceback__.tb_lineno))
        return jsonify({'message': 'An error occured'}), 500
