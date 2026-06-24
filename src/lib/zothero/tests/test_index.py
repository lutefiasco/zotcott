# encoding: utf-8
#
# MIT Licence.
#

"""Tests for the search index (index.py).

Characterisation + migration guard for the FTS3 -> FTS5 change. The search
behaviour tests must stay green across the migration; ``test_index_uses_fts5``
is the migration's red-to-green driver.
"""

import os
import sqlite3

import pytest

from zothero.index import Index
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


def _build_zot(tmp_path, items):
    """items: list of (itemID, key, title, abstract)."""
    dbpath = str(tmp_path / 'zotero.sqlite')
    con = sqlite3.connect(dbpath)
    con.executescript(SCHEMA)
    con.execute("INSERT INTO itemTypes VALUES (1, 'journalArticle')")
    con.execute("INSERT INTO fields VALUES (1,'title'),(2,'date'),(3,'abstractNote')")
    vid = 1
    for (iid, key, title, abstract) in items:
        con.execute("INSERT INTO items VALUES (?, '2020-01-01 12:00:00', ?, 1, 1)",
                    (iid, key))
        con.execute("INSERT INTO itemDataValues VALUES (?, ?)", (vid, title))
        con.execute("INSERT INTO itemData VALUES (?, 1, ?)", (iid, vid)); vid += 1
        con.execute("INSERT INTO itemDataValues VALUES (?, '2020-01-01 2020')", (vid,))
        con.execute("INSERT INTO itemData VALUES (?, 2, ?)", (iid, vid)); vid += 1
        con.execute("INSERT INTO itemDataValues VALUES (?, ?)", (vid, abstract))
        con.execute("INSERT INTO itemData VALUES (?, 3, ?)", (iid, vid)); vid += 1
    con.commit()
    con.close()
    os.environ['alfred_workflow_cache'] = str(tmp_path)
    return Zotero(str(tmp_path), dbpath, None)


@pytest.fixture
def index(tmp_path):
    zot = _build_zot(tmp_path, [
        (1, 'AAAA1111', 'Medieval Manuscripts', 'A focused study.'),
        (2, 'BBBB2222', 'Roman History', 'Mentions manuscripts only in passing.'),
        (3, 'CCCC3333', "O'Brien on Ireland", 'A study of (medieval) Irish law: part one.'),
    ])
    idx = Index(str(tmp_path / 'search.sqlite'))
    idx.update(zot)
    return idx


def test_search_finds_entry_by_title(index):
    res = index.search('Medieval')
    assert [e.title for e in res] and \
        any(e.title == 'Medieval Manuscripts' for e in res)


def test_search_no_match_is_empty(index):
    assert index.search('Byzantine') == []


def test_title_match_ranks_above_abstract_match(index):
    """An entry matching in its title outranks one matching only in abstract."""
    res = index.search('manuscripts')
    titles = [e.title for e in res]
    assert titles, 'expected results'
    assert titles[0] == 'Medieval Manuscripts'


def test_search_with_apostrophe_does_not_crash(index):
    """An apostrophe is FTS5's string delimiter; it must not reach MATCH raw."""
    res = index.search("O'Brien")
    assert any(e.title == "O'Brien on Ireland" for e in res)


@pytest.mark.parametrize('query', [
    "O'Brien",          # apostrophe -> FTS5 string delimiter
    '(medieval)',       # parentheses -> FTS5 grouping
    'law: part',        # colon -> FTS5 column filter
    'medieval-irish',   # hyphen -> FTS5 NOT/negation
    '"unbalanced',      # lone double quote
    '*',                # bare wildcard
    '',                 # empty
])
def test_search_special_characters_never_crash(index, query):
    """No user input should raise an FTS5 syntax error."""
    # Should return a list (possibly empty), never raise.
    assert isinstance(index.search(query), list)


def test_index_uses_fts5(index):
    """The search virtual table is backed by FTS5 (migration guard)."""
    row = index.conn.execute(
        "SELECT sql FROM sqlite_master WHERE name='search'").fetchone()
    assert row is not None
    assert 'fts5' in row[0].lower()
