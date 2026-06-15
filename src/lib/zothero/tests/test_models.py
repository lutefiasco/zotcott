# encoding: utf-8
#
# MIT Licence.
#

"""Unit tests for models.py."""

import os

import pytest

from zothero.models import Attachment


def test_exists_true_for_real_file(tmp_path):
    """A path pointing at a file on disk -> exists is True."""
    f = tmp_path / 'paper.pdf'
    f.write_text('pdf')
    att = Attachment(key='ABC', name='paper.pdf', path=str(f), url=None)
    assert att.exists is True


def test_exists_false_for_missing_file(tmp_path):
    """A path that resolves nowhere (e.g. an orphaned absolute path) -> False."""
    att = Attachment(key='ABC', name='gone.pdf',
                     path='/Users/matthew/Documents/TooBigForBox/gone.pdf',
                     url=None)
    assert att.exists is False


def test_exists_false_for_url_only(tmp_path):
    """A web attachment (url, no path) -> exists is False, no crash."""
    att = Attachment(key='ABC', name='link', path=None,
                     url='https://example.com')
    assert att.exists is False


def test_exists_false_for_empty_path(tmp_path):
    """Missing/empty path -> exists is False, no crash."""
    att = Attachment(key='ABC', name='x', path='', url=None)
    assert att.exists is False
