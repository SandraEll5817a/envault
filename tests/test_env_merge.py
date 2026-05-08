"""Tests for envault.env_merge."""

import pytest

from envault.env_merge import (
    ConflictStrategy,
    MergeConflict,
    MergeResult,
    merge_env,
    _parse_env,
    _render_env,
)


# ---------------------------------------------------------------------------
# _parse_env
# ---------------------------------------------------------------------------

def test_parse_env_basic():
    text = "FOO=bar\nBAZ=qux\n"
    assert _parse_env(text) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_ignores_comments_and_blanks():
    text = "# comment\n\nFOO=bar\n"
    assert _parse_env(text) == {"FOO": "bar"}


def test_parse_env_handles_equals_in_value():
    text = "URL=http://example.com?a=1"
    assert _parse_env(text) == {"URL": "http://example.com?a=1"}


# ---------------------------------------------------------------------------
# _render_env
# ---------------------------------------------------------------------------

def test_render_env_sorted_and_newline():
    data = {"Z": "last", "A": "first"}
    rendered = _render_env(data)
    assert rendered == "A=first\nZ=last\n"


# ---------------------------------------------------------------------------
# merge_env — no conflicts
# ---------------------------------------------------------------------------

def test_merge_identical_envs():
    env = "FOO=bar\nBAZ=qux\n"
    result, rendered = merge_env(env, env)
    assert not result.has_conflicts
    assert result.merged == {"FOO": "bar", "BAZ": "qux"}
    assert "FOO=bar" in rendered


def test_merge_adds_remote_key():
    local = "FOO=bar\n"
    remote = "FOO=bar\nNEW=value\n"
    result, _ = merge_env(local, remote)
    assert "NEW" in result.added_from_remote
    assert result.merged["NEW"] == "value"
    assert not result.has_conflicts


def test_merge_keeps_local_only_key():
    local = "FOO=bar\nLOCAL_ONLY=yes\n"
    remote = "FOO=bar\n"
    result, _ = merge_env(local, remote)
    assert "LOCAL_ONLY" in result.added_from_local
    assert result.merged["LOCAL_ONLY"] == "yes"


# ---------------------------------------------------------------------------
# merge_env — conflict strategies
# ---------------------------------------------------------------------------

def test_merge_conflict_error_strategy_raises():
    local = "FOO=local\n"
    remote = "FOO=remote\n"
    with pytest.raises(ValueError, match="Merge conflict on key 'FOO'"):
        merge_env(local, remote, strategy=ConflictStrategy.ERROR)


def test_merge_conflict_ours_strategy():
    local = "FOO=local\n"
    remote = "FOO=remote\n"
    result, rendered = merge_env(local, remote, strategy=ConflictStrategy.OURS)
    assert result.has_conflicts
    assert result.merged["FOO"] == "local"
    assert "FOO=local" in rendered


def test_merge_conflict_theirs_strategy():
    local = "FOO=local\n"
    remote = "FOO=remote\n"
    result, rendered = merge_env(local, remote, strategy=ConflictStrategy.THEIRS)
    assert result.has_conflicts
    assert result.merged["FOO"] == "remote"
    assert "FOO=remote" in rendered


def test_merge_conflict_list_populated():
    local = "FOO=local\nBAR=same\n"
    remote = "FOO=remote\nBAR=same\n"
    result, _ = merge_env(local, remote, strategy=ConflictStrategy.OURS)
    assert len(result.conflicts) == 1
    assert result.conflicts[0].key == "FOO"
    assert result.conflicts[0].local_value == "local"
    assert result.conflicts[0].remote_value == "remote"


# ---------------------------------------------------------------------------
# MergeResult.summary
# ---------------------------------------------------------------------------

def test_summary_no_changes():
    result = MergeResult(merged={"FOO": "bar"})
    assert "No changes" in result.summary()


def test_summary_shows_conflict_keys():
    conflict = MergeConflict(key="SECRET", local_value="abc", remote_value="xyz")
    result = MergeResult(merged={"SECRET": "abc"}, conflicts=[conflict])
    summary = result.summary()
    assert "SECRET" in summary
    assert "local" in summary
    assert "remote" in summary


def test_summary_shows_added_from_remote():
    result = MergeResult(merged={"NEW": "v"}, added_from_remote=["NEW"])
    assert "Added from remote" in result.summary()
    assert "NEW" in result.summary()
