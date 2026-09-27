# encoding: utf-8
#
# MIT Licence.
#

"""Integration tests for zotero.py against a minimal Zotero-shaped DB.

These build a throwaway SQLite file with just the tables ``_load_entry``
touches, so we can exercise entry loading without a real Zotero install and
without any Better BibTeX database present.
"""

import os
import sqlite3

import pytest

from zothero.zotero import Zotero


SCHEMA = """
CREATE TABLE itemTypes (itemTypeID INTEGER PRIMARY KEY, typeName TEXT);
CREATE TABLE items (itemID INTEGER PRIMARY KEY, dateModified TEXT, key TEXT,
                    libraryID INTEGER, itemTypeID INTEGER);
CREATE TABLE deletedItems (itemID INTEGER, dateDeleted TEXT);
CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT);
CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value TEXT);
CREATE TABLE itemData (itemID INTEGER, fieldID INTEGER, valueID INTEGER);
CREATE TABLE creators (creatorID INTEGER PRIMARY KEY, firstName TEXT, lastName TEXT);
CREATE TABLE creatorTypes (creatorTypeID INTEGER PRIMARY KEY, creatorType TEXT);
CREATE TABLE itemCreators (itemID INTEGER, creatorID INTEGER,
                           creatorTypeID INTEGER, orderIndex INTEGER);
CREATE TABLE collections (collectionID INTEGER PRIMARY KEY, collectionName TEXT, key TEXT);
CREATE TABLE collectionItems (collectionID INTEGER, itemID INTEGER);
CREATE TABLE itemAttachments (itemID INTEGER, parentItemID INTEGER, path TEXT);
CREATE TABLE itemNotes (itemID INTEGER, parentItemID INTEGER, note TEXT);
CREATE TABLE tags (tagID INTEGER PRIMARY KEY, name TEXT);
CREATE TABLE itemTags (tagID INTEGER, itemID INTEGER);
"""


@pytest.fixture
def zot(tmp_path):
    """A Zotero instance backed by a one-item fixture database."""
    datadir = tmp_path
    dbpath = str(datadir / 'zotero.sqlite')
    con = sqlite3.connect(dbpath)
    con.executescript(SCHEMA)
    con.execute("INSERT INTO itemTypes VALUES (1, 'journalArticle')")
    con.execute("INSERT INTO items VALUES (1, '2020-01-01 12:00:00', 'ABCD1234', 1, 1)")
    con.execute("INSERT INTO fields VALUES (1, 'title'), (2, 'date')")
    con.execute("INSERT INTO itemDataValues VALUES (1, 'Test Article'), (2, '2020-01-01 2020')")
    con.execute("INSERT INTO itemData VALUES (1, 1, 1), (1, 2, 2)")
    con.commit()
    con.close()
    # alfred_workflow_cache is read in __init__; give it a real dir.
    os.environ['alfred_workflow_cache'] = str(tmp_path)
    return Zotero(str(datadir), dbpath, None)


def test_entry_loads(zot):
    """A basic entry loads with correct title and year."""
    e = zot.entry('ABCD1234')
    assert e is not None
    assert e.title == 'Test Article'
    assert e.year == 2020


def test_entry_has_no_citekey(zot):
    """After dropping Better BibTeX, entries carry no citekey attribute."""
    e = zot.entry('ABCD1234')
    assert 'citekey' not in e


def test_no_betterbibtex_db_required(zot, tmp_path):
    """Entry loading must not require a better-bibtex.sqlite on disk."""
    assert not os.path.exists(str(tmp_path / 'better-bibtex.sqlite'))
    e = zot.entry('ABCD1234')  # must not raise
    assert e.title == 'Test Article'


def test_modified_since_skips_orphaned_attachment_parent(zot):
    """An attachment whose parent is gone must not crash an incremental update.

    Upstream ZotHero 7b6bc78: ``entry(key)`` returns None for a missing or
    deleted parent, and ``None["id"]`` raised TypeError.
    """
    import datetime
    con = sqlite3.connect(zot.dbpath)
    # Attachment 2 hangs off item 99, which does not exist.
    con.execute("INSERT INTO items VALUES (2, '2030-01-01 12:00:00', 'ATTACH02', 1, 1)")
    con.execute("INSERT INTO itemAttachments VALUES (2, 99, 'storage:a.pdf')")
    # Attachment 4 hangs off item 3, which is in the trash.
    con.execute("INSERT INTO items VALUES (3, '2020-01-01 12:00:00', 'DELETED3', 1, 1)")
    con.execute("INSERT INTO deletedItems VALUES (3, '2021-01-01 12:00:00')")
    con.execute("INSERT INTO items VALUES (4, '2030-01-01 12:00:00', 'ATTACH04', 1, 1)")
    con.execute("INSERT INTO itemAttachments VALUES (4, 3, 'storage:b.pdf')")
    con.commit()
    con.close()
    entries = list(zot.modified_since(datetime.datetime(2025, 1, 1)))
    assert None not in entries
