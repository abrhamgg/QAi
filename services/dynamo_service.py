import boto3
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv
import os
import time
from botocore.exceptions import ClientError


load_dotenv()
# import AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from .env file

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
MY_AWS_ACCESS_KEY_ID = os.getenv('MY_AWS_ACCESS_KEY_ID')
MY_AWS_SECRET_ACCESS_KEY = os.getenv('MY_AWS_SECRET_ACCESS_KEY')


class DynamoService:
    def __init__(self, region_name='us-east-2', table_name="qai-calls"):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name,
                                       aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        self.table_name = table_name

    def create_table(self):
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'contact_id',
                        'KeyType': 'HASH'},  # Partition key
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'contact_id', 'AttributeType': 'S'},
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            table.wait_until_exists()
            print(f"Created table {self.table_name}")
        except Exception as e:
            print(f"Unable to create table: {e}")

    def get_all_data(self):
        try:
            print("started to fetch data")
            table = self.dynamodb.Table(self.table_name)
            response = table.scan()
            data = response['Items']

            # Loop through paginated results
            while 'LastEvaluatedKey' in response:
                print("fetching more data")
                response = table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey'])
                data.extend(response['Items'])

            # Sort the data based on the 'created_at' field
            data = sorted(
                data, key=lambda x: time.strptime(x['created_at'], "%Y-%m-%d %I:%M %p"), reverse=True
            )

            return data
        except Exception as e:
            print(f"Unable to find records: {e}")
            return None

    def get_all_by_columns(self, location_id=None, columns=['contact_id', 'phone', 'contact_full_name', 'property_address_full', 'call_recording_link', 'call_duration', 'transcription_status', 'created_at', 'transcribed_at', 'caller_name', 'location_id']):
        try:
            table = self.dynamodb.Table(self.table_name)
            scan_kwargs = {}

            # Add ProjectionExpression if columns are specified
            if columns:
                scan_kwargs['ProjectionExpression'] = ", ".join(columns)

            # Add FilterExpression for location_id if provided
            if location_id:
                scan_kwargs['FilterExpression'] = Key(
                    'location_id').eq(location_id)

            response = table.scan(**scan_kwargs)
            data = response['Items']

            # Loop through paginated results
            while 'LastEvaluatedKey' in response:
                response = table.scan(
                    ExclusiveStartKey=response['LastEvaluatedKey'], **scan_kwargs)
                data.extend(response['Items'])

            # Sort the data based on the 'created_at' field
            data = sorted(
                data, key=lambda x: time.strptime(x['created_at'], "%Y-%m-%d %I:%M %p"), reverse=True
            )

            return data

        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

    def get_item_by_contact_id(self, contact_id, location_id=''):
        try:
            table = self.dynamodb.Table(self.table_name)
            response = table.get_item(
                Key={'contact_id': contact_id})
            return response.get('Item')
        except Exception as e:
            print(f"Unable to get item: {e}")
        return None

    def add_item(self, data):
        try:
            print("adding item")
            table = self.dynamodb.Table(self.table_name)
            table.put_item(Item=data)
            print("Item added successfully")
        except Exception as e:
            print(f"Unable to add item: {e}")

    def delete_item_by_contact_id(self, contact_id, location_id):
        try:
            table = self.dynamodb.Table(self.table_name)
            table.delete_item(
                Key={'contact_id': contact_id})
            print("Item deleted successfully")
            return True
        except Exception as e:
            print(f"Unable to delete item: {e}")
            return False

    # add summary field to the item
    def update_item_by_contact_id(self, contact_id, data):
        try:
            table = self.dynamodb.Table(self.table_name)

            # Prepare the update expression and attribute values
            update_expression = "SET "
            expression_attribute_values = {}

            for key, value in data.items():
                if key != 'contact_id':  # Skip the primary key
                    update_expression += f"{key} = :{key}, "
                    expression_attribute_values[f":{key}"] = value

            # Remove trailing comma and space
            update_expression = update_expression.rstrip(", ")

            # Perform the update
            table.update_item(
                Key={'contact_id': contact_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )

            return True
        except Exception as e:
            print(f"Error updating item: {e}")
            return None


class QaiUsersDynamoService:
    def __init__(self, region_name='us-east-2', table_name="qai_users"):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name,
                                       aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        self.table_name = table_name

    def add_user(self, data):
        try:
            table = self.dynamodb.Table(self.table_name)
            table.put_item(Item=data)
            print("User added successfully")
        except Exception as e:
            print(f"Unable to add user: {e}")

    def get_user_by_location_id(self, location_id):
        try:
            table = self.dynamodb.Table(self.table_name)
            response = table.get_item(
                Key={'location_id': location_id})
            return response.get('Item')
        except Exception as e:
            print(f"Unable to get user: {e}")
        return None

    def get_all_scripts(self, location_id):
        try:
            user = self.get_user_by_location_id(location_id)
            if not user:
                return None
            print(user)
            return user.get('settings').get('coach')
        except Exception as e:
            print(f"Unable to get scripts: {e}")
            return None

    # def update_script(self, location_id, script_name, script_content):
    #     try:
    #         table = self.dynamodb.Table(self.table_name)
    #         # Ensure the settings and coach objects exist
    #         response = table.update_item(
    #             Key={
    #                 'location_id': location_id
    #             },
    #             UpdateExpression="SET #settings = if_not_exists(#settings, :default_settings)",
    #             ExpressionAttributeNames={
    #                 '#settings': 'settings'
    #             },
    #             ExpressionAttributeValues={
    #                 ':default_settings': {'coach': {}}
    #             }
    #         )

    #         # Update the specific script in settings.coach
    #         response = table.update_item(
    #             Key={
    #                 'location_id': location_id
    #             },
    #             UpdateExpression="SET settings.coach.#script_name = :script_content",
    #             ExpressionAttributeNames={
    #                 '#script_name': script_name
    #             },
    #             ExpressionAttributeValues={
    #                 ':script_content': script_content
    #             },
    #             ReturnValues="UPDATED_NEW"
    #         )
    #         return response
    #     except ClientError as e:
    #         print(e.response['Error']['Message'])
    #         return None


# Example usage:
if __name__ == '__main__':
    service = DynamoService()

    # print("getting all data")
    # data = service.get_all_data()
    # print("starting")
    # for d in data:
    #     if d['rating']:
    #         print(d['contact_id'])
    #         exit()

    # create a knowledge_base.json file
    # import json
    # contacts = {"data": []}
    # for d in data:
    #     obj = {
    #         'contact_id': d['contact_id'],
    #     }
    #     contacts['data'].append(obj)
    # with open('knowledge_base.json', 'w') as f:
    #     json.dump(contacts, f)

    # destination_service = boto3.resource('dynamodb', region_name='us-east-2',
    #                                      aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    # dest_table = destination_service.Table('qai-calls')
    # count = 0
    # for item in data:
    #     print(item['contact_id'])
    #     count += 1
    #     item['location_id'] = '2Q02CtA3t4WM7BjDCi98'
    #     # service.update_item_by_contact_id(item['contact_id'], item)
    #     # dest_table.put_item(Item=item)
    # print(count)

    # Create the table (run this only once)
    # service.create_table()

    # Add an item
    # item_data = {
    #     'contact_id': '123',
    #     'contact_full_name': 'John Doe',
    #     'property_address_full': '123 Elm Street',
    #     'call_recording_link': 'http://example.com/recording',
    #     'call_duration': '300',
    #     'transcription_status': 'completed'
    # }
    # d = service.update_item_by_contact_id('123', summary)
    # # service.add_item(item_data)
    # print(d)
    # # Update item by contact_id
    # # service.update_item_by_contact_id('123', 'This is a summary')
    # # # Get all items
    # # all_data = service.get_all_data()
    # # print(all_data)

    # # # Get item by contact_id
    # # item = service.get_item_by_contact_id(123)
    # # print(item)

    # # # Delete item by contact_id
    # # service.delete_item_by_contact_id(123)

    # # get all data from dynamodb and create new columns like created at, updated at ,  model type, caller name
    # # add these columns to the existing data

    # # data = service.get_all_data()
    # # for item in data:
    # #     # create new columns
    # #     item['created_at'] = "2024-06-1"
    # #     item['updated_at'] = "2024-06-1"
    # #     item['model_type'] = "AssemblyAI"
    # #     item['caller_name'] = ""
    # #     item['transcribed_at'] = str(int(time.time()))

    # #     service.update_item_by_contact_id(item['contact_id'], item)

    # # print("Data updated successfully")

    # # the time format isn't readable, I want it in est time zone
    # # I will use the datetime module to convert the time to a readable format

    # # import datetime
    # # # get the current time
    # # current_time = datetime.datetime.now()
    # # print(current_time)
    # # # make it in PM AM, In EST time zone
    # # print(current_time.strftime("%Y-%m-%d %I:%M %p"))

    # # data = service.get_all_data()
    # # for item in data:
    # #     # create new columns
    # #     item['created_at'] = current_time.strftime("%Y-%m-%d %I:%M %p")
    # #     item['updated_at'] = current_time.strftime("%Y-%m-%d %I:%M %p")
    # #     item['transcribed_at'] = current_time.strftime("%Y-%m-%d %I:%M %p")

    # #     service.update_item_by_contact_id(item['contact_id'], item)
    # # print("Data updated successfully")
