import re
from collections import OrderedDict
from flask_login import current_user
from flask import redirect, url_for
import time


def check_access_token():
    expired_at = current_user.expires_at
    if expired_at < str(time.time()):
        print(expired_at, time.time())
        return redirect(url_for('auth.connect'))
    return True


# Function to count words in a strings


def count_words(text):
    words = text.split()
    return len(words)


def load_from_dynamo():
    try:
        import boto3
        import os

        db = boto3.resource('dynamodb', region_name='us-east-1',
                            aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        table = db.Table('qai-crm-key')
        response = table.scan()
        data = response['Items'][0]
        if data:
            return data
        return {"error": "No keys found"}
    except Exception as e:
        print(f"Unable to get data: {e}")
        return None


def format_time(input_time, call_duration):

    def time_to_seconds(time_str):
        hours, minutes, seconds = map(int, time_str.split(':'))
        return hours * 3600 + minutes * 60 + seconds

    input_seconds = time_to_seconds(input_time)
    call_seconds = time_to_seconds(call_duration)

    if call_seconds == 0:
        return "Call duration cannot be zero"

    percentage = (input_seconds / call_seconds) * 100

    hours, remainder = divmod(input_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours == 0:
        formatted_time = f"{minutes} minutes {seconds} seconds"
    else:
        formatted_time = f"{hours} hours {minutes} minutes {seconds} seconds"

    return f"{formatted_time} ({percentage:.2f}%)"


def calculate_silence_time(speaker_a, speaker_b, duration):
    """
    format for speaker_A IS 00:00:45
    """
    speaker_a = speaker_a.split(':')
    speaker_b = speaker_b.split(':')
    duration = duration.split(':')
    print(speaker_a, speaker_b, duration)

    speaker_a_seconds = (
        int(speaker_a[0]) * 3600) + (int(speaker_a[1]) * 60) + int(speaker_a[2])
    speaker_b_seconds = int(
        speaker_b[0]) * 3600 + int(speaker_b[1]) * 60 + int(speaker_b[2])
    duration_seconds = int(duration[0]) * 3600 + \
        int(duration[1]) * 60 + int(duration[2])

    silent = duration_seconds - speaker_a_seconds - speaker_b_seconds
    percentage_of_silent = (silent / duration_seconds) * 100
    percentage_of_silent = round(percentage_of_silent, 2)
    # convert to hh:mm:ss
    hours, remainder = divmod(silent, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours == 0:
        formatted_time = f"{minutes} minutes {seconds} seconds"
    else:
        formatted_time = f"{hours} hours {minutes} minutes {seconds} seconds"

    return formatted_time, percentage_of_silent


def remove_to_discuss(text):
    """Removes the text starting from "TO BE DISCUSSED" (inclusive) from the input text.

    Args:
      text: The input text string.

    Returns:
      The modified text string with the "TO BE DISCUSSED" section removed.
    """
    cutoff_index = text.find("TO BE DISCUSSED")
    if cutoff_index != -1:
        return text[:cutoff_index]
    else:
        return text


def extract_dynamic_key_value_pairs(text):
    # Define a dictionary to hold the extracted information
    extracted_info = OrderedDict()
    text = remove_to_discuss(text)

    # Define a general pattern to match key-value pairs
    pattern = re.compile(r"([\w\s\(\)\/]+):\s*(\"[^\"]*\"|[^:\n]+)")

    # Find all matches in the text
    matches = pattern.findall(text)

    # Process each match and add it to the dictionary
    for match in matches:
        key = match[0].strip()
        value = match[1].strip().strip('"')
        extracted_info[key] = value

    # Try to fetch the left text from the raw summary text file

    return extracted_info


def text_to_json(text):
    """Converts the input text to a JSON object with exact key names and empty strings for missing values.

    Args:
      text: The input text string.

    Returns:
      A dictionary representing the JSON object.
    """
    text = remove_to_discuss(text)
    lines = text.splitlines()  # Split text into lines
    data = {}
    for line in lines:
        # Split line by colon, but handle cases with missing values
        key = line.strip().split(":", 1)[0]  # Get only the key (index 0)
        value = line.strip().split(":", 1)[1] if len(
            line.strip().split(":")) > 1 else ""
        # Set empty string for missing value
        data[key] = value.strip() if value else "TO BE DISCUSSED"

    return data


# Sample text
text = """PROPERTY ADDRESS ON FILE: 5854 SW 61 St Miami FL 33143  
PROPERTY ADDRESS FOR SALE: 5854 SW 61 St Miami FL 33143  
ASKING PRICE: "Between $900,000 to $1.1 million"  
VALUATION: TO BE DISCUSSED  
WIGGLE ROOM: Yes  
MOTIVATION: Renovating to potentially sell and move out of Miami  
CONDITION (To make it a 10/10): Renovations underway, including bathroom, kitchen, exterior paint, and roof. Not specified but implies significant work being done.  
TIMEFRAME: 4-5 months for completion of renovations  
OCCUPANCY: Owner Occupied  
MORTGAGES/BACK TAXES: Mentioned a reverse mortgage and back taxes issues which have been resolved. Owes $200,000 to the bank which will be cleared upon sale.  
DECISION MAKER: Jose Dhar (Seller)  
OWN ANY OTHER PROPERTIES FOR SALE: TO BE DISCUSSED  
Additional information: Jose Dhar inherited the property from his father and has stopped foreclosure proceedings. He is currently renovating the property with an estimated cost of $200,000 for the renovations. Jose is 99% sure he will sell the property after renovations are complete and plans to move out of Miami. He is not interested in hiring a real estate agent or selling to an investor who will not meet his asking price. He has received numerous calls from interested buyers but is focused on completing renovations before making any sale decisions."""


CONSTANTS = {
    "MOTIVATION": "Motivation",
    "PROPERTY ADDRESS ON FILE": "Property Address Map",
    "PROPERTY ADDRESS FOR SALE": "Property Address for Sale",
    "ASKING PRICE": "Asking Price",
    "CONDITION (To make it a 10/10)": "Condition",
    "TIMEFRAME": "TimeFrame",
    "OCCUPANCY": "Occupancy ",
    "MORTGAGES/BACK TAXES": "Mortgage Amount",
    "DECISION MAKER": "Decision Maker",
    "OWN ANY OTHER PROPERTIES FOR SALE": "Other Properties",
    "VALUATION": "Valuation",
    "WIGGLE ROOM": "Wiggle Room",
    "Additional information": "Additional Information",
    "ARREARS": "Arrears",
    "SELL OR KEEP": "Sell or Keep",
    "SELL or KEEP": "Sell or Keep",
    "CALLER SPOKE TO": "Caller Spoke To",
    "MORGAGE BALANCE": "Mortgage Balance",
    "ORIGINAL PROPERTY ADDRESS ON FILE": "Orginal Property Address In File",
    "AUCTION DATE": "Auction Date",
    "ADDITIONAL INFO": "Additional Info",
    "OPTIONS PROVIDED BY THE CALLER": "Options Provided by the Caller",
    "CONDITION OF THE PROPERTY": "Condition",
    "FOLLOW UP DATE": "Follow Up Date",
    "BEST TIME TO CALL BACK": "Best Time to Call Back",
    "BEST PHONE NUMBER TO CALL BACK": "Best Phone Number to Call Back",
    "SELLER DID TO GET OUT OF FORECLOSURE": "Seller did to get out of foreclosure",
}
REVERSED_CONSTANTS = {
    "Property Address Map": "PROPERTY ADDRESS ON FILE",
    "Property Address for Sale": "PROPERTY ADDRESS FOR SALE",
    "Asking Price": "ASKING PRICE",
    "Motivation": "MOTIVATION",
    "Condition": "CONDITION (To make it a 10/10)",
    "TimeFrame": "TIMEFRAME",
    "Occupancy ": "OCCUPANCY",
    "Mortgage Amount": "MORTGAGES/BACK TAXES",
    "Decision Maker": "DECISION MAKER",
    "Other Properties": "OWN ANY OTHER PROPERTIES FOR SALE",
    "Valuation": "VALUATION",
    "Wiggle Room": "WIGGLE ROOM",
    "Additional Information": "Additional information",
    "Arrears": "ARREARS",
    "Original Property Address On File": "ORIGINAL PROPERTY ADDRESS ON FILE",
    "Sell or Keep": "SELL OR KEEP",
    "Caller Spoke To": "CALLER SPOKE TO",
    "Mortgage Balance": "MORGAGE BALANCE",
    "Auction Date": "AUCTION DATE",
    "Additional Info": "ADDITIONAL INFO",
    "Options Provided by the Caller": "OPTIONS PROVIDED BY THE CALLER",
    "Condition of the Property": "CONDITION OF THE PROPERTY",
    "Follow Up Date": "FOLLOW UP DATE",
    "Best Time to Call Back": "BEST TIME TO CALL BACK",
    "Best Phone Number to Call Back": "BEST PHONE NUMBER TO CALL BACK",
    "Seller did to get out of foreclosure": "SELLER DID TO GET OUT OF FORECLOSURE",
}


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


data = {
    "ORIGINAL PROPERTY ADDRESS ON FILE": "78 60 Mary Post Avenue, Citrus Heights",
    "PROPERTY ADDRESS FOR SALE": {"value": "7785 Spring Valley Avenue, Citrus Heights, 95610", "time": "00:00:48"},
    "ASKING PRICE": {"value": "$345,000", "time": "00:01:21"},
    "VALUATION": {"value": "$332,005", "time": "00:02:30"},
    "WIGGLE ROOM": {"value": "Not discussed", "time": ""},
    "MOTIVATION": {"value": "Rebecca expressed interest in selling the property", "time": "00:13:37"},
    "CONDITION (To make it a 10/10)": {"value": "Cosmetic work needed, no structural damage", "time": "00:06:00"},
    "TIMEFRAME": {"value": "Rebecca is off on Mondays and Tuesdays, available after 1:00 p.m. during the week and weekends", "time": "00:05:15"},
    "OCCUPANCY": {"value": "Not discussed", "time": ""},
    "MORTGAGES/BACK TAXES": {"value": "Reverse mortgage on the property", "time": "00:02:43"},
    "DECISION MAKER": {"value": "Rebecca Duran", "time": "00:13:44"},
    "OWN ANY OTHER PROPERTIES FOR SALE": {"value": "Rebecca mentioned another property in probate for sale", "time": "00:00:48"},
    "Additional information": "Rebecca provided details about the property's history, repairs done, and current condition. Jay will pass the information to a property specialist for due diligence."
}
