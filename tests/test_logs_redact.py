from __future__ import annotations

from ci_triage.logs import clean_lines, extract_error_region, failing_tests, key_lines
from ci_triage.redact import REDACTED, redact
from ci_triage.state import history_text, prepare_state

from .conftest import PYTEST_LOG


def test_clean_lines_strips_timestamps_and_colours() -> None:
    lines = clean_lines("2026-10-01T10:00:00.1234567Z \x1b[31mred\x1b[0m text")
    assert lines == ["red text"]


def test_extract_keeps_the_failing_step_and_first_failure() -> None:
    ex = extract_error_region(PYTEST_LOG)
    assert ex.failed_step == "pytest -q"
    assert ex.text.startswith("[step] pytest -q")
    assert "E       assert 14 == 15" in ex.text
    assert "Syncing repository" not in ex.text  # an earlier, passing step
    assert "upload-artifact" not in ex.text  # a later step
    assert ex.exit_codes == ["Process completed with exit code 1."]
    assert "shell: /usr/bin/bash" not in ex.text


def test_extract_without_error_annotation_keeps_the_tail() -> None:
    raw = "\n".join(f"line {i}" for i in range(200)) + "\nThe operation was canceled."
    ex = extract_error_region(raw)
    assert "The operation was canceled." in ex.text
    assert len(ex.text) < 2000


def test_extract_caps_the_size() -> None:
    raw = "##[group]Run make\n" + "\n".join("Error: boom " + "x" * 300 for _ in range(500)) + "\n##[error]Process completed with exit code 2."
    ex = extract_error_region(raw, max_chars=3000)
    assert len(ex.text) < 3300
    assert ex.text.endswith("exit code 2.")


def test_key_lines_pick_the_assertion_and_exit_code() -> None:
    text = extract_error_region(PYTEST_LOG).text
    lines = key_lines(text, 3)
    assert len(lines) == 3
    assert any("FAILED tests/test_refunds.py" in line for line in lines)
    assert any("exit code 1" in line for line in lines)


def test_failing_tests_across_frameworks() -> None:
    text = "\n".join(
        [
            "FAILED tests/test_a.py::test_one - assert 1 == 2",
            "--- FAIL: TestCheckout (0.01s)",
            "  ● Cart › adds an item",
            "test parser::tests::nested ... FAILED",
            " FAIL  src/cart.test.ts > Cart > totals",
            "AppTest > startsUp() FAILED",
        ]
    )
    assert failing_tests(text) == [
        "tests/test_a.py::test_one",
        "TestCheckout",
        "Cart › adds an item",
        "parser::tests::nested",
        "src/cart.test.ts > Cart > totals",
        "AppTest > startsUp()",
    ]


def test_redact_tokens_assignments_urls_and_emails() -> None:
    gh_token = "ghp" + "_" + "A1b2C3d4" * 5
    text = (
        f"token {gh_token}\nexport API_KEY=" + "not-a-real-key-42" + "\nAuthorization: Bearer " + "not-a-real-bearer-value" + "\n"
        "git clone https://bot:" + "not-a-real-password9" + "@example.com/repo.git\nauthor: Jane <jane.doe@example.org>\n"
        "password: ${{ secrets.DB_PASSWORD }}\n"
    )
    out, n = redact(text)
    assert gh_token not in out
    assert "not-a-real-key-42" not in out and "not-a-real-bearer-value" not in out
    assert "not-a-real-password9" not in out
    assert "jane.doe@example.org" not in out and "[EMAIL]" in out
    assert "${{ secrets.DB_PASSWORD }}" in out  # references are kept
    assert out.count(REDACTED) == n >= 4


def test_redact_keeps_ordinary_log_text() -> None:
    text = "FAILED tests/test_a.py::test_token_refresh - assert 'expired' == 'valid'\ncommit 4f1c2e9d8b7a6c5d4e3f2a1b0c9d8e7f6a5b4c3d"
    out, n = redact(text)
    assert out == text and n == 0


def test_state_is_redacted_and_explains_history(failure) -> None:  # type: ignore[no-untyped-def]
    failure.excerpt += "\nDB_PASSWORD=supersecretvalue1"
    failure.history_checked, failure.history_failed = 10, 3
    state, n = prepare_state(failure)
    assert "supersecretvalue1" not in state["log_excerpt"] and n == 1
    assert state["default_branch_history"].startswith("often: the same job failed in 3 of the last 10 runs on main")
    assert state["branch_type"] == "pull request (branch fix-refunds)"
    failure.history_checked = 0
    assert history_text(failure).startswith("unknown")


def test_redaction_stays_on_one_line() -> None:
    text = "  NX_CLOUD_ACCESS_TOKEN:\n##[error]Process completed with exit code 1.\nauth token\nSomethingLongEnoughHere"
    out, n = redact(text)
    assert out == text and n == 0


def test_private_key_without_end_marker_and_digests() -> None:
    key = "-----BEGIN RSA PRIVATE" + " KEY-----\nMIIEowIBAAKCAQEA" + "q" * 40
    out, _ = redact(f"leaked:\n{key}")
    assert "MIIEow" not in out
    digest = "sha256:" + "ab12" * 16
    assert redact(f"docker pull alpine@{digest}")[0].endswith(digest)
