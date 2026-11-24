# Regression Tests: FitDesk Enquiry Assistant

All automated tests mock the Gemini response (`call_model` is replaced by a fake function), so they run without an API key, without internet and without paid calls.

**Command:** `python -m pytest -v`
**Run on:** 24 November 2026, Windows, Python 3.15.0, pytest 9.2.0
**Overall result:** 10 passed in 1.18s

## Summary

| ID | Requirement | Scenario | Automated | Result |
|---|---|---|---|---|
| T1 | FR-04, FR-05, FR-08 | Normal enquiry answered from the data | Yes | PASS |
| T2 | FR-05 | Question about something not in the data | Yes | PASS |
| T3 | FR-03, NFR-02 | AI returns broken or invalid JSON | Yes | PASS |
| T4 | NFR-02 | AI service fails | Yes | PASS |
| T5 | FR-06, FR-08 | Staff say `n` | Yes | PASS |
| T6 | FR-07, FR-08 | Staff say `y` | Yes | PASS |
| T7 | FR-06 | Approval prompt re-asks on bad input | Yes | PASS |
| T8 | NFR-02 | Temporary AI error (503) is retried, then succeeds | Yes | PASS |
| T9 | NFR-02 | Primary model keeps failing, fallback model is used | Yes | PASS |
| T10 | NFR-02 | Bad request (400) is not retried | Yes | PASS |
| M1 | FR-01 to FR-08 | Real end-to-end run with the live Gemini API | Manual | PASS |
| M2 | NFR-02 | Live Gemini returns 503 (before retry was added) | Manual | PASS |

## Automated tests (`tests/test_assistant.py`)

### T1: Normal enquiry answered from the data
- **Requirement:** FR-04, FR-05, FR-08 (AC-01)
- **Input / precondition:** Message "12 pack and Saturday?". Gemini mocked to return intent `both`, packages `["12"]`, `asks_saturday` true. Staff approval mocked as `y`.
- **Steps:** Call `process_enquiry`. Read the draft and the returned status.
- **Expected:** Draft contains `12 sessions: R1,680` and `10:00 (Full)`, both taken from the data file. Status is `sent`.
- **Actual:** Draft contained both lines. Status was `sent`.
- **Result:** PASS

### T2: Question about something not in the data
- **Requirement:** FR-05 (AC-02)
- **Input / precondition:** Gemini mocked to return packages `["20"]` (not in the data file). Staff approval mocked as `n`.
- **Steps:** Call `process_enquiry`. Read the draft and status.
- **Expected:** Draft is exactly "I'll check with the owner and come back to you." No price appears. Status is `rejected`, not `sent`.
- **Actual:** Draft equalled the escalation phrase exactly. Status was `rejected`.
- **Result:** PASS

### T3: AI returns broken or invalid JSON
- **Requirement:** FR-03, NFR-02 (AC-03)
- **Input / precondition:** Gemini mocked three times with: truncated JSON, JSON with missing fields, and plain text that is not JSON. The approval function is set to fail the test if it is called.
- **Steps:** Call `process_enquiry` for each bad response. Read the status, the draft and the log.
- **Expected:** Status `error_invalid_ai_output`, empty draft, staff are never asked to approve, and no `sent` entry is in the log.
- **Actual:** All three cases returned `error_invalid_ai_output` with an empty draft. Approval was never called. No `sent` entry in the log.
- **Result:** PASS

### T4: AI service fails
- **Requirement:** NFR-02 (AC-04)
- **Input / precondition:** Gemini mocked to raise `TimeoutError` ("simulated AI outage"). The approval function is set to fail the test if it is called.
- **Steps:** Call `process_enquiry`. Read the status and the log.
- **Expected:** Status `error_ai_unavailable`. No crash. The log holds only that one entry.
- **Actual:** Status was `error_ai_unavailable`. The log contained exactly one entry with that status.
- **Result:** PASS

### T5: Staff say `n`
- **Requirement:** FR-06, FR-08 (AC-05)
- **Input / precondition:** Valid mocked AI response. Staff approval mocked as `n`.
- **Steps:** Call `process_enquiry`. Read the status and the log.
- **Expected:** Status `rejected`. The log contains one entry with status `rejected`.
- **Actual:** Status was `rejected`. The log contained one `rejected` entry.
- **Result:** PASS

### T6: Staff say `y`
- **Requirement:** FR-07, FR-08 (AC-01)
- **Input / precondition:** Message "12 pack?". Valid mocked AI response. Staff approval mocked as `y`.
- **Steps:** Call `process_enquiry`. Read the log.
- **Expected:** One log entry with status `sent`, the draft containing `R1,680`, and the original message.
- **Actual:** One entry. Status `sent`, draft contained `R1,680`, message was "12 pack?".
- **Result:** PASS

### T7: Approval prompt re-asks on bad input
- **Requirement:** FR-06
- **Input / precondition:** Simulated typed answers: `maybe`, an empty line, then `y`. Second case: `x`, then `n`.
- **Steps:** Call `ask_approval` with each sequence.
- **Expected:** Invalid answers are ignored and the question is asked again. It never defaults to yes. First sequence returns True, second returns False.
- **Actual:** First sequence returned True after three prompts. Second returned False.
- **Result:** PASS

## Automated tests for retry and fallback (`tests/test_retry.py`)

These protect the reliability requirement (NFR-02) after the retry and fallback model were added.

### T8: Temporary AI error is retried, then succeeds
- **Requirement:** NFR-02
- **Input / precondition:** The Gemini call is mocked to raise a 503 error twice, then return valid JSON. Waiting is mocked out so the test is fast.
- **Steps:** Call `call_gemini`. Count the attempts.
- **Expected:** The valid JSON is returned after exactly 3 attempts.
- **Actual:** Returned the JSON. 3 attempts were made.
- **Result:** PASS

### T9: Primary model keeps failing, fallback model is used
- **Requirement:** NFR-02
- **Input / precondition:** Primary model mocked to always raise 503. Backup model mocked to succeed.
- **Steps:** Call `call_gemini`. Record which models were tried.
- **Expected:** The primary model is tried the maximum number of times, then the backup model is tried and its result returned.
- **Actual:** The primary model was tried `MAX_ATTEMPTS` times. The last model used was the backup, and the JSON was returned.
- **Result:** PASS

### T10: Bad request is not retried
- **Requirement:** NFR-02
- **Input / precondition:** The Gemini call is mocked to raise a 400 error.
- **Steps:** Call `call_gemini`. Count the attempts.
- **Expected:** The error is raised immediately, with no retry, because retrying cannot fix a bad request.
- **Actual:** The error was raised after 1 attempt.
- **Result:** PASS

## Manual tests (real Gemini API)

### M1: End-to-end run with the live API
- **Requirement:** FR-01 to FR-08
- **Input / precondition:** Valid API key in `.env`. Message typed at the prompt: "How much is the 5 pack?"
- **Steps:** Run `python main.py`. Type the message. Type `y` at `Send? (y/n):`.
- **Expected:** Draft shows the 5-session price from the data file. Status `sent` is recorded.
- **Actual:** Draft was `5 sessions: R800`. Output ended with `Status recorded: sent`.
- **Result:** PASS

### M2: Live Gemini unavailable
- **Requirement:** NFR-02
- **Input / precondition:** Gemini returned `503 UNAVAILABLE` ("high demand"). This was observed before the retry code was added.
- **Steps:** Run `python main.py` with the message "How much is the 12-session pack and do you have Saturday slots?"
- **Expected:** No draft, a clear message, no crash, status `error_ai_unavailable`.
- **Actual:** The program printed "The AI service is unavailable. No draft was made." and `Status recorded: error_ai_unavailable`. This repeated across several runs without a crash.
- **Result:** PASS (this real failure is why the retry and fallback were added; see `docs/RAPLH_LOG.md`)
