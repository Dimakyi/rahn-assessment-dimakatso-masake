# SRS: FitDesk Enquiry Assistant (CLI)

## 1. Business objective
The studio owner wants staff to answer package-price and Saturday-availability enquiries faster, without ever sending an invented price or availability claim. The assistant drafts replies from approved data; a staff member approves every reply.

## 2. Stakeholders
- **Studio owner:** sets the approved data and the rules.
- **Staff member:** runs the tool, approves or rejects each draft.
- **Customer:** receives accurate replies (indirectly; nothing is sent automatically).
- **RAHN:** builds and maintains the tool.

## 3. Scope
**In scope:** read one typed customer message; classify it with Gemini into structured JSON; look up facts in a local data file; draft a reply from those facts; ask staff `Send? (y/n)`; record the outcome in a status log.

**Out of scope:** WhatsApp, bookings, payments, calendar, client history, any fact not in the data file.

## 4. Functional requirements
- **FR-01:** The program accepts a customer message typed at the command line.
- **FR-02:** The message is sent to Gemini, which must return JSON containing `intent`, `details`, `requires_human_approval`, `packages` and `asks_saturday`.
- **FR-03:** The JSON is validated against a Pydantic model. Invalid JSON is rejected.
- **FR-04:** Facts (prices, Saturday slots) are looked up by code in `data/studio_data.json`, never supplied by the AI.
- **FR-05:** The reply is built only from looked-up facts. If nothing in the enquiry can be answered from the data, the reply is exactly: "I'll check with the owner and come back to you." If only part of the enquiry is missing, the known parts are answered and the same phrase is added for the missing part.
- **FR-06:** The draft is printed and staff are asked `Send? (y/n)`.
- **FR-07:** Every outcome is appended to `status_log.json` with timestamp, message, draft and status.
- **FR-08:** The status `sent` is recorded only when staff answer `y` and the draft is valid (see section 7).

## 5. Non-functional requirements
- **NFR-01 Security:** The API key lives in `.env` (git-ignored); only `.env.example` is committed.
- **NFR-02 Reliability:** An AI timeout, error or invalid output never crashes the program and never produces a `sent` record. Temporary AI errors (429, 500, 503, 504) are retried with backoff, then a fallback model is tried, before the program gives up.
- **NFR-03 Cost:** Free tools only (Python, Gemini free tier). Tests run with the Gemini call mocked, so no key or paid call is needed.

## 6. Data inputs and outputs
**Inputs:** customer message (text); `data/studio_data.json` (single R180, 5 sessions R800, 12 sessions R1,680; Saturday 09:00 available, 10:00 full, 11:00 available); `.env` with `GEMINI_API_KEY`.
**Outputs:** printed draft reply; `status_log.json` entry.

## 7. Approval and failure rules
| Situation | Behaviour | Status logged |
|---|---|---|
| Staff answer `y` on a valid draft | Draft treated as sent | `sent` |
| Staff answer `n` | Nothing sent | `rejected` |
| Gemini returns invalid JSON | Show error, no draft | `error_invalid_ai_output` |
| Gemini fails or times out | Show error, no draft | `error_ai_unavailable` |
| Fact missing | Draft is the exact escalation phrase; staff still asked `y/n` | `sent` only if staff say `y`, otherwise `rejected` |
| Staff enter anything other than `y`/`n` | Ask again; never default to `y` | none until answered |

## 8. Acceptance criteria
- **AC-01:** Given "How much is the 12-session pack?", the draft contains R1,680 and the status is `sent` only after `y`.
- **AC-02:** Given a question about a package not in the data file, the draft is exactly "I'll check with the owner and come back to you." and no price appears.
- **AC-03:** Given Gemini returns malformed JSON, the log contains no `sent` entry for that message.
- **AC-04:** Given Gemini raises an error, the log contains no `sent` entry and the program exits cleanly.
- **AC-05:** Given staff answer `n`, the log status is `rejected`.
- **AC-06:** Given the test suite is run with no `GEMINI_API_KEY`, all automated tests pass.

## 9. Ambiguities and assumptions
| # | Unclear in the brief | Question for the owner | Assumption made |
|---|---|---|---|
| 1 | Which Saturday does "Saturday availability" mean? | Is the file always for the coming Saturday? | The file covers one upcoming Saturday; no dates are handled. |
| 2 | What does "sent" mean when nothing is really sent? | Do staff paste the reply into WhatsApp themselves? | `sent` means staff approved the draft; staff send it manually. |
| 3 | What if a message asks about several things, one of which is missing? | Should the reply partly answer? | Answer the known parts and add the escalation phrase for the missing part; staff review it. |
| 4 | Are session prices per-package totals or per session? | Is R1,680 for all 12? | Prices are package totals in rand. |