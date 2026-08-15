# Email Classifier Agent 1.0.0
This is the initial MYP of a production-minded email agent: it reads
your unread inbox, classifies each email with an LLM of your choice (can be replaced with higher models specific to the app's core requirements),
logs records to SQLite, and ends the process. **No drafting or sending for this version yet**
That comes in later stages once this stage has its foundation secured.

## What this version brings

- OAuth integration with an external API (Gmail)
- Structured LLM output using Pydantic schema
- Idempotency (the agent doesn't reprocess the same email twice)
- Persistent logging mechanism
- A model-agnostic LLM interface — swap Gemini for Claude later with minimal code changes

## Prerequisites

- Python3.10 or above
- Poetry (optional but recommended for easier package managing)
- Gmail Oauth and Gmail API access
- Gemini API Key (for Gemini models)

## Setup

### 1. Install dependencies

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 2. Get a free Gemini API key

Go to https://aistudio.google.com/app/apikey, and create a key

### 3. Set up Gmail API access

This step needs to run only once but requires some careful handling and accuracy.

1. Go to https://console.cloud.google.com/ and create a new project (or
   use an existing one).
2. Go to **APIs & Services > Library**, search for "Gmail API", click
   **Enable**.
3. Go to **APIs & Services > OAuth consent screen**.
   - User type: External (unless you have a Workspace account).
   - Fill in app name, your email, save through the steps.
   - Under **Test users**, add your own Gmail address. (While the app
     is unpublished, only up to 100 test users can authenticate)
4. Go to **APIs & Services > Credentials > Create Credentials > OAuth
   client ID**.
   - Application type: **Desktop app**.
   - Download the resulting JSON file from the dialog box that pops up, rename it `credentials.json`, and put it in the project root.
5. Copy `.env.example` to `.env` and fill in `GEMINI_API_KEY`

## Usage

### 1. Activating the environment

You need to activate the virual environment every time before you start the agent.

For regular virtualenv
```bash
source .venv/bin/activate
python src/email_agent/main.py
```
For poetry 
```bash
poetry shell
python src/email_agent/main.py
```

The first run will open a browser window asking you to log in and approve read-only Gmail access. After your approval, a `token.json` file is saved in the project's root directory so future runs don't ask again (until the token expires).


Each run pulls up to `MAX_EMAILS_PER_RUN` unread emails (default 10),
classifies any it hasn't seen before, and prints the results.
Nothing is delivered or modified in your actual Gmail inbox — this stage is
read-only by design (see `SCOPES` in `gmail_client.py`).

## Running the eval

```bash
python eval/run_eval.py
```

This scores the classifier against `eval/test_emails.json` — 5 examples is just a placeholder to test if the expected harness works. Run this eval every time you change the prompt or
switch models, and keep a note of accuracy over time.

## Known limitations of this stage

- Read-only: doesn't draft or send anything yet
- No web UI integrated
- Single account, single run (no scheduling/polling loop yet)
- Rate-limited by Gemini's free tier (fine for personal inbox volume,
  see `time.sleep(1)` in the eval script)
