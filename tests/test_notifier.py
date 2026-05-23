"""Tests for procwatch.notifier."""

import json
from unittest.mock import MagicMock, patch

import pytest

from procwatch.notifier import Alert, dispatch, send_desktop, send_webhook


@pytest.fixture()
def sample_alert():
    return Alert(
        pid=1234,
        name="stress",
        cpu_percent=95.0,
        memory_mb=512.5,
        message="stress (pid 1234) cpu=95.0% mem=512.50 MB",
    )


# --- send_webhook ---

def test_send_webhook_success(sample_alert):
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_open:
        result = send_webhook("http://example.com/hook", sample_alert)

    assert result is True
    mock_open.assert_called_once()
    req = mock_open.call_args[0][0]
    body = json.loads(req.data.decode())
    assert body["pid"] == 1234
    assert body["name"] == "stress"
    assert body["cpu_percent"] == 95.0


def test_send_webhook_failure_returns_false(sample_alert):
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        result = send_webhook("http://bad-host/hook", sample_alert)

    assert result is False


# --- send_desktop ---

def test_send_desktop_no_plyer(sample_alert):
    with patch("procwatch.notifier._PLYER_AVAILABLE", False):
        result = send_desktop(sample_alert)
    assert result is False


def test_send_desktop_with_plyer(sample_alert):
    mock_notify = MagicMock()
    with patch("procwatch.notifier._PLYER_AVAILABLE", True), \
         patch("procwatch.notifier.plyer_notification") as mock_plyer:
        mock_plyer.notify = mock_notify
        result = send_desktop(sample_alert)

    assert result is True
    mock_notify.assert_called_once()
    call_kwargs = mock_notify.call_args[1]
    assert "stress" in call_kwargs["title"]


def test_send_desktop_plyer_exception(sample_alert):
    with patch("procwatch.notifier._PLYER_AVAILABLE", True), \
         patch("procwatch.notifier.plyer_notification") as mock_plyer:
        mock_plyer.notify.side_effect = RuntimeError("platform error")
        result = send_desktop(sample_alert)
    assert result is False


# --- dispatch ---

def test_dispatch_calls_both_channels(sample_alert):
    with patch("procwatch.notifier.send_webhook", return_value=True) as wh, \
         patch("procwatch.notifier.send_desktop", return_value=True) as dt:
        dispatch(sample_alert, webhook_url="http://hook", desktop=True)

    wh.assert_called_once_with("http://hook", sample_alert)
    dt.assert_called_once_with(sample_alert)


def test_dispatch_skips_webhook_when_none(sample_alert):
    with patch("procwatch.notifier.send_webhook") as wh, \
         patch("procwatch.notifier.send_desktop", return_value=False):
        dispatch(sample_alert, webhook_url=None, desktop=True)

    wh.assert_not_called()


def test_dispatch_skips_desktop_when_false(sample_alert):
    with patch("procwatch.notifier.send_webhook", return_value=True), \
         patch("procwatch.notifier.send_desktop") as dt:
        dispatch(sample_alert, webhook_url="http://hook", desktop=False)

    dt.assert_not_called()
