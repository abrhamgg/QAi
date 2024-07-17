from flask_login import UserMixin
from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, MapAttribute, DynamicMapAttribute, JSONAttribute, ListAttribute, BooleanAttribute, UnicodeSetAttribute
from dotenv import load_dotenv
import os

load_dotenv()

QAI_USERS_DB = os.getenv('QAI_USERS_DB')


# class ReicbUser(UserMixin):
#     def __init__(self, token, refresh, expires_at, location_name, location_id, email):
#         self.token = token
#         self.refresh = refresh
#         self.expires_at = expires_at
#         self.location_name = location_name
#         self.location_id = location_id
#         self.email = email
#         self.id = location_id  # This is required for Flask-Login
#         self.settings = {
#             "coach": {
#                 "scripts": {}
#             }
#         }


class ReicbUser(Model, UserMixin):
    class Meta:
        table_name = QAI_USERS_DB
        region = 'us-east-2'
    location_id = UnicodeAttribute(hash_key=True)
    token = UnicodeAttribute()
    refresh = UnicodeAttribute()
    expires_at = UnicodeAttribute()
    location_name = UnicodeAttribute()
    email = UnicodeAttribute()

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.location_id


class Coach(MapAttribute):
    scripts = JSONAttribute(null=True)  # Use JSONAttribute for dynamic content


class ReicbUserSetting(Model):
    class Meta:
        table_name = 'qai_user_setting'
        region = 'us-east-2'
    location_id = UnicodeAttribute(hash_key=True)
    coach = MapAttribute(of=Coach)
