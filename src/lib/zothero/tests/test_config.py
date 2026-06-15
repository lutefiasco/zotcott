# encoding: utf-8
#
# MIT Licence.
#

"""Unit tests for config.py profile detection.

The original ``find_prefs`` only matched a profile whose ``Name`` was
exactly ``default``. Modern Firefox/Zotero ``profiles.ini`` files instead
mark the active profile with ``Default=1`` on the ``[ProfileN]`` section,
or with a ``Default=<path>`` key in an ``[InstallXXXX]`` section. If profile
detection returns ``None``, *every* linked-file attachment silently drops,
so this needs to be robust across all those layouts.
"""

import os

import pytest

from zothero.config import find_default_profile


def _write(tmp_path, text):
    """Write a profiles.ini under tmp_path and make its profile dirs."""
    ini = tmp_path / 'profiles.ini'
    ini.write_text(text)
    return str(ini), str(tmp_path)


def test_name_default_with_default_flag(tmp_path):
    """The real layout on this machine: Name=default AND Default=1."""
    (tmp_path / 'Profiles' / 'jllhbq2u.default').mkdir(parents=True)
    ini, confdir = _write(tmp_path, (
        "[Profile0]\n"
        "Name=default\n"
        "IsRelative=1\n"
        "Path=Profiles/jllhbq2u.default\n"
        "Default=1\n"
        "\n"
        "[General]\n"
        "StartWithLastProfile=1\n"
        "Version=2\n"
    ))
    got = find_default_profile(ini, confdir)
    assert got == os.path.join(confdir, 'Profiles', 'jllhbq2u.default')


def test_default_flag_wins_over_name(tmp_path):
    """A profile whose Name isn't 'default' is still chosen via Default=1."""
    (tmp_path / 'Profiles' / 'abc.dev').mkdir(parents=True)
    (tmp_path / 'Profiles' / 'xyz.default').mkdir(parents=True)
    ini, confdir = _write(tmp_path, (
        "[Profile0]\n"
        "Name=default\n"
        "IsRelative=1\n"
        "Path=Profiles/xyz.default\n"
        "\n"
        "[Profile1]\n"
        "Name=dev\n"
        "IsRelative=1\n"
        "Path=Profiles/abc.dev\n"
        "Default=1\n"
    ))
    got = find_default_profile(ini, confdir)
    assert got == os.path.join(confdir, 'Profiles', 'abc.dev')


def test_install_section_takes_priority(tmp_path):
    """An [InstallXXXX] Default= path wins over Profile Name/Default flags."""
    (tmp_path / 'Profiles' / 'name-default').mkdir(parents=True)
    (tmp_path / 'Profiles' / 'install-default').mkdir(parents=True)
    ini, confdir = _write(tmp_path, (
        "[Install4F96D1932A9F858E]\n"
        "Default=Profiles/install-default\n"
        "Locked=1\n"
        "\n"
        "[Profile0]\n"
        "Name=default\n"
        "IsRelative=1\n"
        "Path=Profiles/name-default\n"
        "Default=1\n"
    ))
    got = find_default_profile(ini, confdir)
    assert got == os.path.join(confdir, 'Profiles', 'install-default')


def test_single_profile_odd_name(tmp_path):
    """One profile, no Default flag, non-'default' name -> use it anyway."""
    (tmp_path / 'Profiles' / 'q1w2e3.zotero').mkdir(parents=True)
    ini, confdir = _write(tmp_path, (
        "[Profile0]\n"
        "Name=Zotero\n"
        "IsRelative=1\n"
        "Path=Profiles/q1w2e3.zotero\n"
    ))
    got = find_default_profile(ini, confdir)
    assert got == os.path.join(confdir, 'Profiles', 'q1w2e3.zotero')


def test_absolute_path_profile(tmp_path):
    """IsRelative=0 means Path is already absolute; don't join confdir."""
    abs_dir = tmp_path / 'custom' / 'profile'
    abs_dir.mkdir(parents=True)
    ini, confdir = _write(tmp_path, (
        "[Profile0]\n"
        "Name=default\n"
        "IsRelative=0\n"
        "Path=%s\n"
        "Default=1\n"
    ) % str(abs_dir))
    got = find_default_profile(ini, confdir)
    assert got == str(abs_dir)


def test_no_profiles_returns_none(tmp_path):
    """No profile sections at all -> None, not a crash."""
    ini, confdir = _write(tmp_path, (
        "[General]\n"
        "StartWithLastProfile=1\n"
        "Version=2\n"
    ))
    assert find_default_profile(ini, confdir) is None


def test_missing_ini_returns_none(tmp_path):
    """A nonexistent profiles.ini -> None, not a crash."""
    missing = str(tmp_path / 'nope.ini')
    assert find_default_profile(missing, str(tmp_path)) is None
