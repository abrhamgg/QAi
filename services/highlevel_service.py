from dotenv import load_dotenv
import os
import requests

load_dotenv()


HIGHLEVEL_BASE_URL = os.getenv('HIGHLEVEL_BASE_URL')
print(HIGHLEVEL_BASE_URL)
custom_fields_dict = {
    'username': "username",
}


class HighlevelService:
    def __init__(self, token='', location_id=''):
        self.headers = {
            'Authorization': 'Bearer ' + token,
            'Version': '2021-07-28'
        }
        self.url = HIGHLEVEL_BASE_URL + '/locations/' + location_id

    def get_custom_fields(self):
        try:
            response = requests.get(self.url +
                                    '/customFields', headers=self.headers)
            if response.status_code != 200:
                return None
            return response.json()
        except:
            return None

    def get_contact_by_id(self, contact_id):
        response = requests.get(HIGHLEVEL_BASE_URL +
                                f'/contacts/{contact_id}', headers=self.headers)
        return response.json()

    def get_custom_field_by_id(self, field_id):
        try:
            response = requests.get(self.url +
                                    f'/custom-fields/{field_id}', headers=self.headers)
            return response.json()
        except:
            return None

    def get_custom_field_name(self, field_id):
        response = requests.get(self.url +
                                f'/custom-fields/{field_id}', headers=self.headers)
        return response.json()['name']

    def update_custom_fields_by_id(self, contact_id, data):
        """
        data should be in the form of:
        {
            "customField": {"rmYgH248FwbnPhQwRcND": "Abrham"}   
        }
        """
        response = requests.put(HIGHLEVEL_BASE_URL +
                                f'/contacts/{contact_id}', headers=self.headers, json=data)
        return response.json()

    def get_custom_field_id_by_name(self, field_name):
        custom_fields = self.get_custom_fields()
        custom_fields = custom_fields['customFields']
        for field in custom_fields:
            if field['name'] == field_name:
                return field['id']
        return None

    def get_customValue(self):
        response = requests.get(self.url +
                                '/customValues', headers=self.headers)
        return response.json()

    def update_custom_value(self, data, custom_value_id):
        """
        data should be in the form of:
        {
        "name": "Custom Field",
        "value": "Value"
        }
        """
        response = requests.put(self.url +
                                f'/customValues/{custom_value_id}', headers=self.headers, json=data)
        return response.json()


# highlevel = HighlevelService()
# print(highlevel.get_custom_field_id_by_name('Speaker A Talk Time (Seconds)'))

if __name__ == "__main__":
    # load the knowledge_base.json file
    import json
    highlevel_service = HighlevelService()

    with open('knowledge_base.json') as f:
        data = json.load(f)
        data = data['data']

        for item in data:
            id = item['contact_id']
            cu = highlevel_service.get_contact_by_id(id)
            print(cu)
            exit()
