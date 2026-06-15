# encoding: utf-8
#
# Copyright (c) 2019 Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2019-01-06
#

"""Read Zotero configuration files."""

#from ConfigParser import SafeConfigParser
from configparser import ConfigParser
import logging
import os
import re

from .util import unicodify

CONFDIR = os.path.expanduser(u'~/Library/Application Support/Zotero')
PROFILES = os.path.join(CONFDIR, u'profiles.ini')
DATADIR_KEY = 'extensions.zotero.dataDir'
ATTACH_KEY = 'extensions.zotero.baseAttachmentPath'
# Start of preference lines
PREFIX = 'user_pref("'

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


def read():
    """Load data and attachments directories from Zotero prefs."""
    p = find_prefs()
    if p:
        return parse_prefs(p)

    return None, None


def find_default_profile(profiles_ini, confdir):
    """Return the absolute path of the default Zotero profile directory.

    Resolves the active profile across the layouts Firefox/Zotero have used
    over the years, in priority order:

    1. An ``[InstallXXXX]`` section's ``Default=<path>`` (the modern,
       per-install default; wins over everything else).
    2. A ``[ProfileN]`` section flagged ``Default=1``.
    3. A ``[ProfileN]`` section whose ``Name`` is ``default``.
    4. The sole ``[ProfileN]`` section, if there's exactly one.

    Returns ``None`` (rather than raising) if nothing can be resolved or the
    file is missing/unreadable.

    Args:
        profiles_ini (str): Path to ``profiles.ini``.
        confdir (str): Zotero config dir; base for ``IsRelative`` paths.

    Returns:
        unicode or None: Absolute path to the profile directory, or ``None``.
    """
    conf = ConfigParser()
    try:
        if not conf.read(profiles_ini):  # file missing / unreadable
            return None
    except Exception as err:
        log.error('reading profiles.ini: %s', err)
        return None

    def resolve(path, is_relative):
        if is_relative:
            path = os.path.join(confdir, path)
        return unicodify(path)

    profiles = [s for s in conf.sections() if s.lower().startswith('profile')]

    # 1. [InstallXXXX] Default=<path> (always relative to confdir)
    for section in conf.sections():
        if section.lower().startswith('install') and \
                conf.has_option(section, 'Default'):
            return resolve(conf.get(section, 'Default'), True)

    # 2. A profile explicitly flagged Default=1
    for section in profiles:
        if conf.has_option(section, 'Default') and \
                conf.get(section, 'Default').strip() in ('1', 'true', 'True'):
            return resolve(conf.get(section, 'Path'),
                           conf.getboolean(section, 'IsRelative', fallback=True))

    # 3. A profile named "default"
    for section in profiles:
        if conf.has_option(section, 'Name') and \
                conf.get(section, 'Name') == 'default':
            return resolve(conf.get(section, 'Path'),
                           conf.getboolean(section, 'IsRelative', fallback=True))

    # 4. The only profile, whatever it's called
    if len(profiles) == 1:
        section = profiles[0]
        return resolve(conf.get(section, 'Path'),
                       conf.getboolean(section, 'IsRelative', fallback=True))

    return None


def find_prefs():
    """Find prefs.js by parsing profiles.ini."""
    profile_dir = find_default_profile(PROFILES, CONFDIR)
    if not profile_dir:
        log.error('could not locate default Zotero profile in %s', PROFILES)
        return None

    return unicodify(os.path.join(profile_dir, 'prefs.js'))


def parse_prefs(path):
    """Extract relevant preferences from prefs.js."""
    datadir = attachdir = None

    def extract_value(s):
        m = re.search(r'"(.+)"', s)
        if not m:
            return None

        return unicodify(m.group(1))

    with open(path) as fp:
        for line in fp:
            line = line.strip()
            if not line.startswith(PREFIX):
                continue

            line = line[len(PREFIX):]
            i = line.find('",')
            if i < 0:
                continue

            key = line[:i]
            if key == DATADIR_KEY:
                datadir = extract_value(line[i + 2:])
                log.debug('[config] datadir=%r', datadir)
            elif key == ATTACH_KEY:
                attachdir = extract_value(line[i + 2:])
                log.debug('[config] attachdir=%r', attachdir)

    return datadir, attachdir
