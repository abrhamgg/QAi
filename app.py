from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from models.reicb_user import ReicbUser
from routes.transcribe import transcribe_bp
from routes.coaching import coaching_bp
from config import Config
from services.dynamo_service import DynamoService
from routes.highlevel import highlevel_bp
from routes.dynamo import dynamo_bp
from routes.transcribe_rev import rev_bp
from routes.reicb_auth import auth_bp
from routes.summary import summary_bp
import time
from datetime import timedelta
from utils import extract_dynamic_key_value_pairs, CONSTANTS, check_access_token, format_time, calculate_silence_time, text_to_json
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(hours=23)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.connect'


@login_manager.user_loader
def load_user(location_id):
    user_info = [i for i in ReicbUser.query(location_id, limit=1)]
    if len(user_info) > 0:
        return user_info[0]
    return None


app.register_blueprint(transcribe_bp)
app.register_blueprint(highlevel_bp)
app.register_blueprint(dynamo_bp)
app.register_blueprint(rev_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(coaching_bp)
app.register_blueprint(summary_bp)
app.config.from_object(Config)
dynamo = DynamoService()


@app.route('/', methods=['GET'])
@login_required
def hello():
    check_access_token()
    try:
        contacts = dynamo.get_all_by_columns(current_user.location_id)
        return render_template('index.html', contacts=contacts)
    except Exception as e:
        print(e)
        return render_template('error.html', error=e)


@app.route('/prompt', methods=['GET'])
@login_required
def prompt():
    try:
        if request.args.get('contact_id'):
            contact = dynamo.get_item_by_contact_id(
                request.args.get('contact_id'), current_user.location_id)
            if contact['location_id'] == current_user.location_id:
                if contact['utterances'][0]['speaker'] == 'A' or contact['utterances'][0]['speaker'] == 'B':
                    data = calculate_silence_time(
                        contact['talk_time']['A'], contact['talk_time']['B'], contact['call_duration'])
                    contact['percentage_of_silence'] = data[1]
                    contact['silent_time'] = data[0]
                    contact['highlevel_url'] = f"https://crm.reicb.com/v2/location/{current_user.location_id}/contacts/detail/" + contact['contact_id']
                    if current_user.location_id != '2Q02CtA3t4WM7BjDCi98':
                        try:
                            contact['highlevel_url'] = f"https://crm.reicb.com/v2/location/{current_user.location_id}/contacts/detail/" + \
                                contact['sub_account_contact_id']
                        except:
                            contact['highlevel_url'] = "No highlevel url found"
                    contact['talk_time']['A'] = format_time(
                        contact['talk_time']['A'], contact['call_duration'])
                    contact['talk_time']['B'] = format_time(
                        contact['talk_time']['B'], contact['call_duration'])

                    summary = contact['summary']
                    summary_fields = extract_dynamic_key_value_pairs(summary)

                    # make the summary fields ordered dict
                    # Generate UUID to make the url never cache
                    unique_id = int(time.time())
                    return render_template('prompt.html', contact=contact, summary_fields=summary_fields, CONSTANTS=CONSTANTS, unique_id=unique_id, dual=False)
                else:
                    data = calculate_silence_time(
                        contact['talk_time']['1'], contact['talk_time']['2'], contact['call_duration'])
                    contact['percentage_of_silence'] = data[1]
                    contact['silent_time'] = data[0]
                    contact['highlevel_url'] = "https://crm.reicb.com/v2/location/2Q02CtA3t4WM7BjDCi98/contacts/detail/" + contact['contact_id']
                    if current_user.location_id != '2Q02CtA3t4WM7BjDCi98':
                        try:
                            contact['highlevel_url'] = f"https://crm.reicb.com/v2/location/{current_user.location_id}/contacts/detail/" + \
                                contact['sub_account_contact_id']
                        except:
                            contact['highlevel_url'] = "No highlevel url found"
                    contact['talk_time']['1'] = format_time(
                        contact['talk_time']['1'], contact['call_duration'])
                    contact['talk_time']['2'] = format_time(
                        contact['talk_time']['2'], contact['call_duration'])

                    summary = contact['summary']
                    # summary_fields = extract_dynamic_key_value_pairs(summary)
                    summary_fields = text_to_json(summary)
                    # make the summary fields ordered dict
                    # Generate UUID to make the url never cache
                    unique_id = int(time.time())
                    return render_template('prompt.html', contact=contact, summary_fields=summary_fields, CONSTANTS=CONSTANTS, unique_id=unique_id, dual=True)
        else:
            return render_template('error.html')
    except Exception as e:
        print(e)
        return render_template('error.html')


@app.route('/setting', methods=['GET'])
@login_required
def setting():
    conatct_id = request.args.get('contact_id')
    if not conatct_id:
        return jsonify({'error': 'No contact_id provided'}), 400
    custom_values = ['Cold Call Prompt', 'SEAL Foreclosure Prompt']
    return render_template('setting.html', custom_values=custom_values, id=conatct_id, time=int(time.time()))


# @app.route('/login', methods=['GET'])
# def login():
#     return render_template('login.html')


@app.route('/profile')
@login_required
def profile():
    # print sesssion expiry in seconds
    print()
    return f'Hello, {current_user.location_name}\n! Your location ID is {current_user.location_id} \n \n {current_user.refresh}'


@app.route('/admin', methods=['GET'])
@login_required
def admin():
    return render_template('admin.html')


@app.route('/status', methods=['GET'])
@login_required
def status():
    expires = current_user.expires_at
    # convert to human readable time
    expires = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(expires)))
    return f'Hello, {current_user.location_name}\n! Your location ID is {current_user.location_id} \n \n Token will expire at\n \n {expires}'


@app.route('/test', methods=['GET'])
@login_required
def test():
    from services.transcriber_service import TranscriberService
    service = TranscriberService()
    data = [{"confidence": 0.42101, "speaker": "B", "start": 10934, "end": 11714, "text": "Yeah."}, {"confidence": 0.9372320000000001, "speaker": "A", "start": 12574, "end": 18714, "text": "Alrighty. Now, what's your goal? Are you looking to keep the property, or do you have something else in mind?"}, {"confidence": 0.9468899999999999, "speaker": "B", "start": 19614, "end": 22314,
                                                                                                                                                                                                                                                                                                                "text": "I'm looking to rent it out."}, {"confidence": 0.9907514285714285, "speaker": "A", "start": 23534, "end": 25634, "text": "You want to rent the property out?"}, {"confidence": 0.65898, "speaker": "B", "start": 26074, "end": 26854, "text": "Yeah."}, {"confidence": 0.94648625, "speaker": "A", "start": 28594, "end": 32494, "text": "And we're talking about 331 hibiscus drive, right?"}]
    da = [{'speaker': '2', 'text': 'Hello?', 'start': 3160, 'end': 3740}, {'speaker': '1', 'text': 'Hey, Valerie. Hello? Valerie? Hello?', 'start': 4640, 'end': 10874}, {'speaker': '2', 'text': 'Sri Vega.', 'start': 11734, 'end': 12794}, {'speaker': '1', 'text': 'Yeah, this is Enzo. I am a homeowner, advocate. I just wanted to. Someone has reached out to you to see if you need help stopping or delaying the foreclosure.', 'start': 13454, 'end': 23514}, {
        'speaker': '2', 'text': 'No. Excuse me.', 'start': 17174, 'end': 27854}, {'speaker': '1', 'text': 'I just wanted to make sure that someone has reached out to you to see if you need help stopping or delaying the foreclosure on your property.', 'start': 29514, 'end': 36814}, {'speaker': '2', 'text': "Oh, no, we don't need that.", 'start': 36194, 'end': 37554}, {'speaker': '1', 'text': "You don't need any help? I.", 'start': 39474, 'end': 40954}]
    for d in da:
        d['start'] = service.milliseconds_to_hhmmss(d['start'])
        d['end'] = service.milliseconds_to_hhmmss(d['end'])

    return render_template('test.html', data=da)


if __name__ == '__main__':
    app.run()
