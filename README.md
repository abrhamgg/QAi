# QAi

QAI is an AI-powered coaching and quality assurance tool designed to improve the QA process for call centers. It automates call transcription, summarization, key information extraction, and CRM updates, significantly speeding up the QA process and enhancing lead generation and company reputation.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Testing](#Testing)
## Features

- **Call Transcription**: Automatically transcribes call recordings using AssemblyAI.
- **Summarization**: Generates call summaries and extracts key information.
- **CRM Integration**: Updates custom fields in Highlevel CRM with extracted information.
- **Coaching**: Provides coaching feedback based on call transcriptions and sales books.
- **DynamoDB Integration**: Stores transcription and summary data in DynamoDB.
- **Token Refresh**: Refreshes tokens for Highlevel CRM integration.
- **Async Processing**: Supports asynchronous transcription and processing.

## Architecture

The project consists of the following main components:

- **Flask**: Serves as the web framework for the API.
- **Services**: Contains various services like DynamoService, HighlevelService, QaiUsersDynamoService, etc., to handle different functionalities.
- **Blueprints**: Organizes the routes into modular blueprints for better structure and maintainability.
- **Environment Variables**: Manages configuration settings using environment variables.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo url>
   cd <repo dir>
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the root directory and add the required environment variables (refer to [Environment Variables](#environment-variables) section).

## Testing
```
$ pytest
```

## Usage

1. **Run the Flask application**:
   ```bash
   python3 app.py
   ```

2. **Access the API**:
   The API will be available at `http://localhost:5000`.

## API Endpoints

### Dynamo Routes

- **POST /dynamo/summary**: Updates call summary.
- **POST /dynamo/location**: Updates contact location.
- **POST /dynamo/rating**: Updates contact rating.
- **POST /dynamo/admin**: Saves CRM keys.
- **GET /dynamo/admin**: Retrieves CRM keys.

### Coaching Routes

- **POST /start-coaching**: Starts the coaching process.

### Summary Routes

- **POST /start-summary**: Starts the summarization process.

### Transcription Routes

- **POST /transcribe**: Transcribes audio.
- **POST /transcribe/async**: Transcribes audio asynchronously.
- **GET /assembly/callback**: Callback for asynchronous transcription.

## Environment Variables

Create a `.env` file in the root directory and add the following variables:

```env
AUTH_URL=<Your Auth URL>
ASSEMBLY_CALLBACK_URL=<Your Assembly Callback URL>
MY_AWS_ACCESS_KEY_ID=<Your AWS Access Key ID>
MY_AWS_SECRET_ACCESS_KEY=<Your AWS Secret Access Key>
SUMMARY_ASSISTANT_ID=<Your Summary Assistant ID>
PASSWORD=<Your Password>
GPT_API_KEY=
CLIENT_ID
CLIENT_SECRET=
HIGHLEVEL_BASE_URL="https://services.leadconnectorhq.com"
ASSEMBLY_API_KEY=
SUMMARY_ASSISTANT_ID=""

```
