import pytest
from flask import Flask
from routes.coaching import coaching_bp
from services.coaching_service import AssistantHandler, client, ASSISTANT_ID

# Initialize handler
handler = AssistantHandler(client, ASSISTANT_ID)

# Flask app setup
@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(coaching_bp, url_prefix='/')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_start_coaching_success(client):
    # Define valid input data
    data = {
        "transcription": "This is a sample transcription",
        "sales_books": ["Sales Book 1", "Sales Book 2"],
        "call_scripts": ["Call Script 1"]
    }

    # Post request to /start-coaching
    response = client.post('/start-coaching', json=data)

    # Check for successful response
    assert response.status_code == 200
    assert 'messages' in response.json

def test_start_coaching_missing_transcription(client):
    # Define input data missing transcription
    data = {
        "sales_books": ["Sales Book 1", "Sales Book 2"],
        "call_scripts": ["Call Script 1"]
    }

    # Post request to /start-coaching
    response = client.post('/start-coaching', json=data)

    # Check for error response
    assert response.status_code == 400
    assert response.json == {'error': 'Transcription and sales books are required'}


if __name__ == '__main__':
    pytest.main()