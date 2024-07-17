import os
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv()


def test_env_variables():

    assert os.getenv('GPT_API_KEY') != ''
    assert os.getenv('AUTH_URL') == 'https://ai.reicb.com'
    assert os.getenv(
        'ASSEMBLY_CALLBACK_URL') == 'https://ai.reicb.com/assembly/callback'
    assert os.getenv('AWS_ACCESS_KEY_ID') != ''
    assert os.getenv('AWS_SECRET_ACCESS_KEY') != ''
    assert os.getenv(
        'HIGHLEVEL_BASE_URL') == 'https://services.leadconnectorhq.com'
