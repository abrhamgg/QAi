from flask import Blueprint, request, flash, redirect, url_for, jsonify, session
from flask_login import login_required, login_user, logout_user, current_user
from requests.models import PreparedRequest
from requests import post, get
from datetime import datetime as dt
from services.dynamo_service import QaiUsersDynamoService
from models.reicb_user import ReicbUser, ReicbUserSetting, Coach
import os
from dotenv import load_dotenv


load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
AUTH_URL = os.getenv('AUTH_URL')

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
db = QaiUsersDynamoService()


@auth_bp.route('/connect')
def connect():
    base = "https://marketplace.gohighlevel.com/oauth/chooselocation"
    scope = [
        "locations/customValues.write",
        "locations/customFields.write",
        "locations/customFields.readonly",
        "locations.readonly",
        "contacts.readonly",
        "locations/customValues.readonly",
        "contacts.write",
        "contacts.readonly",
    ]

    params = {
        "client_id": CLIENT_ID,
        "scope": " ".join(scope),
        "response_type": "code",
        # url_for("reicb._redirect", _external=True),
        "redirect_uri": f"{AUTH_URL}/auth/redirect"
    }
    req = PreparedRequest()
    req.prepare_url(base, params)

    return redirect(req.url)


@auth_bp.route('/redirect')
def _redirect():
    code = request.args.get("code")
    base = "https://services.leadconnectorhq.com/oauth/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "user_type": "Location",
        "code": code,
    }

    resp = post(base, data=data)
    tokenData = resp.json()

    for i in ["access_token", "refresh_token", "expires_in"]:
        tokenData.get(i)

    # location
    base = "https://services.leadconnectorhq.com/locations"
    headers = {
        "Authorization": f"Bearer {tokenData['access_token']}",
        "Version": "2021-07-28"
    }
    resp = get(f"{base}/{tokenData['locationId']}", headers=headers)
    locationData = resp.json()
    # print(locationData)
    # add connection to db
    dbData = {
        "token": tokenData["access_token"],
        "refresh": tokenData["refresh_token"],
        "expires_at": str(round(dt.now().timestamp() + tokenData["expires_in"])),
        'location_name': locationData['location']['name'],
        "location_id": locationData["location"]["id"],
        'email': locationData['location']['email'],

    }
    # db.add_user(dbData)
    session.permanent = True
    # session['user'] = dbData
    user = ReicbUser(**dbData)
    user.save()

    try:
        # Check if the user already exists
        ReicbUserSetting.get(user.location_id)
    except ReicbUserSetting.DoesNotExist:
        # If the user does not exist, create a new user setting
        settings = ReicbUserSetting(
            location_id=dbData['location_id'], coach=Coach(scripts={}))
        settings.save()

    login_user(user)
    return redirect(url_for('hello'))


@auth_bp.route('/refresh', methods=['GET', 'POST'])
def _refresh():
    try:
        location_id = request.args.get('location_id')
        refresh_token = request.args.get('refresh_token')
        code = request.args.get('code')
        base = "https://services.leadconnectorhq.com/oauth/token"
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": 'refresh_token',
            'refresh_token': refresh_token,
            "user_type": "Location",
            "redirect_uri": f"{AUTH_URL}/auth/redirect",
            "code": code,
        }

        resp = post(base, data=data)
        tokenData = resp.json()
        base = "https://services.leadconnectorhq.com/locations"
        headers = {
            "Authorization": f"Bearer {tokenData['access_token']}",
            "Version": "2021-07-28"
        }
        resp = get(f"{base}/{tokenData['locationId']}", headers=headers)

        locationData = resp.json()
        # print(locationData)
        # add connection to db
        dbData = {
            "token": tokenData["access_token"],
            "refresh": tokenData["refresh_token"],
            "expires_at": str(round(dt.now().timestamp() + tokenData["expires_in"])),
            'location_name': locationData['location']['name'],
            "location_id": locationData["location"]["id"],
            'email': locationData['location']['email'],
        }

        db.add_user(dbData)
        session.permanent = True
        session['user'] = dbData

        user = ReicbUser(**dbData)
        login_user(user)
        return jsonify(tokenData)
    except Exception as e:
        return jsonify({"error": str(e)})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    logout_user()
    session.pop('user', None)
    return redirect(url_for('auth.connect'))
