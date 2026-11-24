import pytest
from google.genai import errors

import assistant


def _overloaded():
    return errors.ServerError(503, {"error": {"message": "overloaded"}})


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(assistant.time, "sleep", lambda s: None)
    monkeypatch.setattr(assistant, "_make_client", lambda: object())


def test_retries_503_then_succeeds(monkeypatch):
    calls = []

    def fake_generate(client, model, message):
        calls.append(model)
        if len(calls) < 3:
            raise _overloaded()
        return '{"ok": true}'

    monkeypatch.setattr(assistant, "_generate", fake_generate)
    assert assistant.call_gemini("hi") == '{"ok": true}'
    assert len(calls) == 3


def test_falls_back_to_second_model(monkeypatch):
    models_used = []

    def fake_generate(client, model, message):
        models_used.append(model)
        if model == "primary-model":
            raise _overloaded()
        return '{"ok": true}'

    monkeypatch.setenv("GEMINI_MODEL", "primary-model")
    monkeypatch.setenv("GEMINI_FALLBACK_MODEL", "backup-model")
    monkeypatch.setattr(assistant, "_generate", fake_generate)

    assert assistant.call_gemini("hi") == '{"ok": true}'
    assert models_used[-1] == "backup-model"
    assert models_used.count("primary-model") == assistant.MAX_ATTEMPTS


def test_does_not_retry_bad_request(monkeypatch):
    calls = []

    def fake_generate(client, model, message):
        calls.append(model)
        raise errors.ClientError(400, {"error": {"message": "bad request"}})

    monkeypatch.setattr(assistant, "_generate", fake_generate)
    with pytest.raises(errors.ClientError):
        assistant.call_gemini("hi")
    assert len(calls) == 1
