# RAPLH Log

RAPLH = Requirements, Analyse, Plan, Loop, Human review.

## Honesty note

- **Before this log:** I used Claude to generate the first versions of `main.py`, `assistant.py` and `tests/test_assistant.py`, so I could finish quickly and then debug and extend them myself. I did not keep a record of those prompts, so I am not presenting them as iteration entries.
- **Entries 1 to 3 below are genuine records** of work done in a Claude chat session on 24 November 2026. They are not illustrative examples. There are no illustrative entries in this log.

## Requirements and analysis (from the brief)

- **R:** Command-line assistant. Gemini returns structured JSON checked by Pydantic. Replies use only facts from the local data file. Missing facts give the exact phrase "I'll check with the owner and come back to you." Staff approve with y/n. `sent` is never recorded after `n`, invalid JSON, AI failure, or unapproved escalation.
- **A (risks):** Gemini could be unavailable or return bad JSON. The AI could invent prices. Staff could type something other than y/n. The API key could leak to GitHub.
- **P (plan):** Small tasks, each checkable with a test: build, test with a mocked AI, handle AI failure, document, review.

## Entry 1 (genuine): Gemini 503 errors, retry and fallback model

- **Task / expected:** Running `python main.py` should print a draft reply. Instead, several runs in a row showed `503 UNAVAILABLE` ("high demand") and recorded `error_ai_unavailable`.
- **Prompts to the AI tool (summary):** (1) Pasted the terminal output and asked why this was happening. (2) Pasted `call_gemini` and asked for a fix. (3) Asked for step-by-step PowerShell instructions, and pasted my `assistant.py` because I was not sure which function to replace.
- **What the AI proposed:** The 503 came from Google's side, not my code. Retry temporary errors (429, 500, 503, 504) with backoff, then try a fallback model. Do not retry other errors such as a bad request.
- **Files changed:** `assistant.py` (added `import random` and `import time`, added retry constants, split `call_gemini` into `_make_client`, `_generate`, `_is_retryable` and `call_gemini`); `tests/test_retry.py` (new, 3 tests).
- **Tests run and result:** `python -m pytest` gave 10 passed (the 7 existing tests plus 3 new ones). `python main.py` with "How much is the 5 pack?" returned `5 sessions: R800` and recorded `sent`.
- **What I corrected:** First I pasted only the new function and missed the step that creates the test file. I ran `Select-String` to confirm there was exactly one `def call_gemini` plus the two imports, then created the test file. I also changed the test file's module name to `assistant`, which is my real file name.
- **Attempts:** 1 code change. The new tests passed on the first run, so no repeated failed fix.
- **Human review and decision:** I read the diff, ran the tests and a live run, and approved. Committed and pushed to GitHub.

## Entry 2 (genuine): README update and push

- **Task / expected:** Update the README with setup, run, test and error-handling steps, then push it to GitHub.
- **Prompts to the AI tool (summary):** Asked for an updated README. Asked which part I must write myself (the Working style section, which the brief says must be written without AI). Asked for the full README with that section left for me.
- **Files changed:** `README.md`.
- **Tests run and result:** No automated test applies. I committed (`5cf654a`) and ran `git push`, which failed with "Could not resolve hostname github.com". I checked my connection with `nslookup github.com` and `Test-NetConnection github.com -Port 22` (both worked), and the next `git push` succeeded.
- **What I corrected:** After reading the full assessment brief, I found the README draft was still missing the hours spent, an "AI use" section, a "What doesn't work yet" section, and my Working style answers, and it still had a placeholder line. These are fixed in a later commit.
- **Human review and decision:** I checked the README against the code and the brief, kept the AI-drafted technical sections, and will write the Working style section myself. Approved and pushed.

## Entry 3 (genuine): Repo review, `.env.example` fix and regression test document

- **Task / expected:** Check the whole repo against the brief's checklist, and create `docs/REGRESSION_TESTS.md`.
- **Prompts to the AI tool (summary):** Uploaded the repo zip and the assessment PDFs and asked the AI to compare them. Then pasted the output of `python -m pytest -v` and asked for the regression test document built from it.
- **Files changed:** `.env.example` (the review found a typo: `GENINI_API_KEY` instead of `GEMINI_API_KEY`); `docs/REGRESSION_TESTS.md` (new, 10 automated tests plus 3 manual tests, each linked to a requirement ID).
- **Tests run and result:** `python -m pytest -v` gave 10 passed. I then renamed `.env` and ran `python -m pytest` again: 10 passed, which proves the tests do not need an API key.
- **What I corrected:** Fixed the `.env.example` variable name. Added the no-API-key run to the regression document as test M3.
- **Human review and decision:** I checked the document against my real test output and approved it. Committed (`c1faee8`) and pushed.

## Reflection questions

**1. How would I stop an AI coding agent from changing unrelated files or exposing my API key?**
Before each task I would list the files the AI is allowed to change and tell it to touch only those. Before committing I check `git status` and `git diff`, and I add files by name instead of `git add .`, so nothing unexpected is committed. I keep backups of files before big edits. The API key lives only in `.env`, which is in `.gitignore`. Only `.env.example` is committed. I never paste the key into a prompt or into code, and I check that `git log --all -- .env` shows nothing. If a key is ever exposed, I revoke it and create a new one.

**2. How would I stop the loop if the agent keeps repeating the same failed fix?**
I set a limit before starting. If the same fix fails twice, I stop the loop. Before any further attempt I read the full error myself and look for the cause instead of asking for the same change again. Then I change the approach or ask a mentor for help. I restore the last working version (from git or a backup) so the failed changes do not pile up, and I record the failure in this log.
