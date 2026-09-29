"""Unit tests for main.py. Google Scholar and Cloud Storage are mocked, so these run offline."""
import json
import logging
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

import main


class FakeRequest:
    """The parts of flask.Request that update_scholar_profile uses."""

    def __init__(self, json_body=None, args=None):
        self._json = json_body
        self.args = args or {}

    def get_json(self, silent=False):
        return self._json


def scholar_author():
    return {
        "scholar_id": "ABC123",
        "name": "Test Author",
        "citedby": 100,
        "publications": [
            {"bib": {"title": "Paper one"}, "num_citations": 60},
            {"bib": {"title": "Paper two"}, "num_citations": 40},
        ],
    }


@pytest.fixture
def scholar():
    with mock.patch.object(main, "scholarly") as fake:
        fake.search_author_id.return_value = {"scholar_id": "ABC123"}
        fake.fill.return_value = scholar_author()
        yield fake


@pytest.fixture
def bucket():
    """A fake bucket that records uploads, in order, as (object name, parsed JSON)."""
    fake_bucket = mock.MagicMock()
    fake_bucket.uploads = []
    fake_bucket.fail_on = None

    def blob(name):
        b = mock.MagicMock()

        def upload(data, content_type=None):
            if name == fake_bucket.fail_on:
                raise RuntimeError("upload failed")
            fake_bucket.uploads.append((name, json.loads(data)))

        b.upload_from_string.side_effect = upload
        return b

    fake_bucket.blob.side_effect = blob
    fake_bucket.get_blob.return_value = None
    with mock.patch.object(main.storage, "Client") as client:
        client.return_value.bucket.return_value = fake_bucket
        yield fake_bucket


def stored_blob(age):
    b = mock.MagicMock()
    b.updated = datetime.now(timezone.utc) - age
    return b


@pytest.mark.parametrize("body", [
    {"filename": "test"},
    {"scholar_id": "ABC123"},
    {"author_name": "Test Author", "filename": "test"},
])
def test_missing_parameters(body, scholar, bucket):
    text, status = main.update_scholar_profile(FakeRequest(body))
    assert status == 400
    scholar.search_author_id.assert_not_called()


@pytest.mark.parametrize("filename", ["../evil", "a/b", "x" * 65, "", 5])
def test_invalid_filename(filename, scholar, bucket):
    text, status = main.update_scholar_profile(FakeRequest({"scholar_id": "ABC123", "filename": filename}))
    assert status == 400
    assert bucket.uploads == []


def test_query_string_parameters(scholar, bucket):
    text, status = main.update_scholar_profile(FakeRequest(args={"scholar_id": "ABC123", "filename": "test"}))
    assert status == 200
    scholar.search_author_id.assert_called_once_with("ABC123")


def test_success_writes_both_files(scholar, bucket):
    text, status = main.update_scholar_profile(FakeRequest({"scholar_id": "ABC123", "filename": "test"}))
    assert status == 200

    # Publications go first, so test.json is only rewritten after both uploads work
    assert [name for name, _ in bucket.uploads] == ["test_pubs.json", "test.json"]
    pubs, author = bucket.uploads[0][1], bucket.uploads[1][1]

    assert "publications" not in author
    assert author["name"] == "Test Author"
    assert isinstance(author["last_updated_ts"], int)
    assert author["last_updated"]

    assert [p["citedby"] for p in pubs] == [60, 40]
    assert all("num_citations" not in p for p in pubs)
    assert all(p["last_updated_ts"] == author["last_updated_ts"] for p in pubs)


def test_scholar_failure_returns_500(scholar, bucket, caplog):
    scholar.search_author_id.side_effect = Exception("Cannot Fetch from Google Scholar.")
    bucket.get_blob.return_value = stored_blob(timedelta(days=1))

    with caplog.at_level(logging.ERROR):
        text, status = main.update_scholar_profile(FakeRequest({"scholar_id": "ABC123", "filename": "test"}))

    assert status == 500
    assert bucket.uploads == []
    assert main.STALE_MARKER not in caplog.text


def test_failed_pubs_upload_keeps_profile_file(scholar, bucket):
    bucket.fail_on = "test_pubs.json"
    bucket.get_blob.return_value = stored_blob(timedelta(days=1))

    text, status = main.update_scholar_profile(FakeRequest({"scholar_id": "ABC123", "filename": "test"}))

    assert status == 500
    assert bucket.uploads == []


@pytest.mark.parametrize("stored, stale", [
    (stored_blob(timedelta(days=1)), False),
    (stored_blob(timedelta(days=8)), True),
    (None, True),
])
def test_log_if_stale(stored, stale, bucket, caplog):
    bucket.get_blob.return_value = stored
    with caplog.at_level(logging.ERROR):
        main.log_if_stale("test")
    assert (main.STALE_MARKER in caplog.text) == stale
