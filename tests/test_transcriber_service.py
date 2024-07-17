import pytest
import os
from services.transcriber_service import TranscriberService

@pytest.fixture
def transcriber_service():
    return TranscriberService()

def test_transcribe_async(transcriber_service):
    # Use a real audio file URL for testing from assembly ai github repo
    audio_url = "https://github.com/AssemblyAI-Examples/audio-examples/raw/main/20230607_me_canadian_wildfires.mp3"
    webhook_url = "https://example.com/webhook"
    contact_id = "test_contact_123"
    caller_name = "Test Caller"
    contact_name = "Test Contact"

    result = transcriber_service.transcribe_async(
        audio_url,
        webhook_url,
        contact_id,
        caller_name,
        contact_name
    )

    # Check if we got a valid transcript ID
    assert isinstance(result, str)
    assert len(result) > 0

def test_get_transcribed_audio(transcriber_service):
    # First, start a transcription
    audio_url = "https://github.com/AssemblyAI-Examples/audio-examples/raw/main/20230607_me_canadian_wildfires.mp3"
    webhook_url = "https://example.com/webhook"
    contact_id = "test_contact_123"
    caller_name = "Test Caller"
    contact_name = "Test Contact"

    transcript_id = transcriber_service.transcribe_async(
        audio_url,
        webhook_url,
        contact_id,
        caller_name,
        contact_name
    )

    # getting the transcribed audio
    result = transcriber_service.get_transcribed_audio(transcript_id)

    # Check if we got a valid response
    assert isinstance(result, dict)
    assert 'id' in result
    assert result['id'] == transcript_id
    
    # The transcription might not be completed immediately
    assert result['status'] in ['queued', 'processing', 'completed']

    # If the status is 'completed', we can check for the presence of the 'text' field
    if result['status'] == 'completed':
        assert 'text' in result
        assert isinstance(result['text'], str)

if __name__ == "__main__":
    pytest.main()