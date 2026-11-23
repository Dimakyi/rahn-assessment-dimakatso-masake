# FitDesk Enquiry Assistant (CLI)

**Hours spent:** TODO (fill in the real total at the end)

A small command-line assistant for a Hermanus fitness studio. It reads a customer enquiry, asks Gemini to classify it as structured JSON, looks up prices and Saturday availability in an approved data file, drafts a reply, and waits for staff to approve it (y/n) before anything is recorded as sent. It takes no bookings or payments and never invents facts.

## Setup (Windows PowerShell)

1. Clone the repo and open the folder.
2. Create and activate a virtual environment:

        python -m venv .venv
        .venv\Scripts\activate

   If PowerShell blocks scripts, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

3. Install the packages. Use `python -m pip` (on my machine `pip.exe` was blocked by Application Control):

        python -m pip install -r requirements.txt

4. Create your key file. Get a free key from https://aistudio.google.com/, then:

        copy .env.example .env

   Open `.env` and replace `your-key-here` with your key. Never commit `.env`.

## Run

PROVISIONAL, confirm after the program is built:

    python main.py

Type a customer message when prompted. Example: `How much is the 12-session pack and do you have Saturday slots?`

## Test

PROVISIONAL, confirm after the tests are written. The tests mock Gemini, so they need no API key:

    python -m pytest

## Project layout

    data/studio_data.json     approved prices and Saturday slots
    docs/SRS.md               requirements
    docs/REGRESSION_TESTS.md  test descriptions and results
    docs/RAPLH_LOG.md         record of working with AI tools
    tests/                    automated tests
    .env.example              template for the API key (the real .env is git-ignored)

## AI use

TODO: list the tools used and what each was used for. Draft: Claude was used for the SRS draft, repo setup help, and (add: code, tests, log) as applicable.

## What doesn't work yet

TODO: be specific, fill in once the program and tests exist.

## Working style

Written by me, without AI.

### 1. Stuck on the same error for three hours at 22:00

TODO

### 2. Teammate silent since Monday, presenting together on Friday

TODO

### 3. Mentor says the approach I spent two days on is wrong

TODO

### 4. Monday, Wednesday and Friday sessions from January to March 2027

TODO