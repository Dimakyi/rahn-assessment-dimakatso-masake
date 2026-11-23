"""Regression tests. Gemini is mocked, so no API key or internet is needed."""
import json

from assistant import ESCALATION, ask_approval, load_data, process_enquiry

DATA = load_data()

PRICE_12_AND_SATURDAY = {
    "intent": "both",
    "details": "Asks about the 12-session pack and Saturday slots.",
    "requires_human_approval": True,
    "packages": ["12"],
    "asks_saturday": True,
}

UNKNOWN_PACKAGE = {
    "intent": "price",
    "details": "Asks about a 20-session pack.",
    "requires_human_approval": True,
    "packages": ["20"],
    "asks_saturday": False,
}


def fake_ai(payload):
    def _call(message):
        return payload if isinstance(payload, str) else json.dumps(payload)
    return _call


def failing_ai(message):
    raise TimeoutError("simulated AI outage")


def must_not_ask(*args, **kwargs):
    raise AssertionError("Staff should not be asked to approve when the AI failed")


def read_log(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_t1_normal_enquiry_uses_data_file(tmp_path):
    log = tmp_path / "log.json"
    status, draft = process_enquiry(
        "12 pack and Saturday?", DATA,
        call_model=fake_ai(PRICE_12_AND_SATURDAY),
        approve=lambda: True, log_path=log,
    )
    assert "12 sessions: R1,680" in draft
    assert "10:00 (Full)" in draft
    assert status == "sent"


def test_t2_missing_fact_uses_exact_escalation_phrase(tmp_path):
    log = tmp_path / "log.json"
    status, draft = process_enquiry(
        "20 pack?", DATA,
        call_model=fake_ai(UNKNOWN_PACKAGE),
        approve=lambda: False, log_path=log,
    )
    assert draft == ESCALATION
    assert status == "rejected"


def test_t3_invalid_json_never_recorded_as_sent(tmp_path):
    for bad in ['{"intent": "price"', '{"intent": "price"}', "not json at all"]:
        log = tmp_path / "log.json"
        status, draft = process_enquiry(
            "anything", DATA,
            call_model=fake_ai(bad),
            approve=must_not_ask, log_path=log,
        )
        assert status == "error_invalid_ai_output"
        assert draft == ""
    assert all(e["status"] != "sent" for e in read_log(log))


def test_t4_ai_failure_never_recorded_as_sent(tmp_path):
    log = tmp_path / "log.json"
    status, draft = process_enquiry(
        "anything", DATA,
        call_model=failing_ai,
        approve=must_not_ask, log_path=log,
    )
    assert status == "error_ai_unavailable"
    assert [e["status"] for e in read_log(log)] == ["error_ai_unavailable"]


def test_t5_staff_says_no_records_rejected(tmp_path):
    log = tmp_path / "log.json"
    status, _ = process_enquiry(
        "12 pack?", DATA,
        call_model=fake_ai(PRICE_12_AND_SATURDAY),
        approve=lambda: False, log_path=log,
    )
    assert status == "rejected"
    assert [e["status"] for e in read_log(log)] == ["rejected"]


def test_t6_staff_says_yes_records_sent_with_draft(tmp_path):
    log = tmp_path / "log.json"
    process_enquiry(
        "12 pack?", DATA,
        call_model=fake_ai(PRICE_12_AND_SATURDAY),
        approve=lambda: True, log_path=log,
    )
    entries = read_log(log)
    assert len(entries) == 1
    assert entries[0]["status"] == "sent"
    assert "R1,680" in entries[0]["draft"]
    assert entries[0]["message"] == "12 pack?"


def test_t7_approval_reasks_on_bad_input_and_never_defaults_to_yes():
    answers = iter(["maybe", "", "y"])
    assert ask_approval(lambda prompt: next(answers)) is True
    answers = iter(["x", "n"])
    assert ask_approval(lambda prompt: next(answers)) is False