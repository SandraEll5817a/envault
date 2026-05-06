"""Tests for envault.share token creation and verification."""

import time

import pytest

from envault.share import ShareToken, create_token, verify_token

SECRET = "super-secret-signing-key"
BUCKET = "my-bucket"
KEY = "project/.env.production"


def test_create_token_returns_string():
    token = create_token(BUCKET, KEY, SECRET)
    assert isinstance(token, str)
    assert "." in token


def test_verify_valid_token_returns_share_token():
    token = create_token(BUCKET, KEY, SECRET)
    result = verify_token(token, SECRET)
    assert result is not None
    assert isinstance(result, ShareToken)


def test_verify_token_correct_fields():
    token = create_token(BUCKET, KEY, SECRET, ttl=600)
    result = verify_token(token, SECRET)
    assert result.bucket == BUCKET
    assert result.key == KEY
    assert result.expires_at > result.issued_at


def test_verify_wrong_secret_returns_none():
    token = create_token(BUCKET, KEY, SECRET)
    result = verify_token(token, "wrong-secret")
    assert result is None


def test_verify_tampered_payload_returns_none():
    token = create_token(BUCKET, KEY, SECRET)
    parts = token.split(".")
    # Corrupt the payload
    tampered = "dGFtcGVyZWQ" + parts[0][10:]
    bad_token = tampered + "." + parts[1]
    assert verify_token(bad_token, SECRET) is None


def test_verify_expired_token_returns_none():
    token = create_token(BUCKET, KEY, SECRET, ttl=-1)
    result = verify_token(token, SECRET)
    assert result is None


def test_is_expired_false_for_fresh_token():
    token_str = create_token(BUCKET, KEY, SECRET, ttl=3600)
    token = verify_token(token_str, SECRET)
    assert token is not None
    assert not token.is_expired()


def test_to_dict_contains_expected_keys():
    token_str = create_token(BUCKET, KEY, SECRET)
    token = verify_token(token_str, SECRET)
    d = token.to_dict()
    assert set(d.keys()) == {"bucket", "key", "issued_at", "expires_at", "token_id"}


def test_each_token_has_unique_token_id():
    t1 = create_token(BUCKET, KEY, SECRET)
    t2 = create_token(BUCKET, KEY, SECRET)
    r1 = verify_token(t1, SECRET)
    r2 = verify_token(t2, SECRET)
    assert r1.token_id != r2.token_id


def test_verify_garbage_input_returns_none():
    assert verify_token("not.a.valid.token", SECRET) is None
    assert verify_token("", SECRET) is None
    assert verify_token("abc", SECRET) is None
