#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2014 Fabio Niephaus <fabio.niephaus@gmail.com>,
#       Dean Jackson <deanishe@deanishe.net>
#
# MIT Licence. See http://opensource.org/licenses/MIT
#
# Created on 2014-08-16
#

"""Semantic version parsing.

.. note::

   The GitHub self-update machinery that originally lived in this module
   was removed in Zotcott (it was inert and made the workflow capable of
   downloading and installing code from the network). Only the ``Version``
   class is kept, as it is used throughout ``workflow.py`` for version
   parsing and comparison (e.g. ``Workflow.version`` and Alfred-version
   checks). Updates are distributed manually via GitHub Releases.

"""


import re
from itertools import zip_longest


class Version(object):
    """Mostly semantic versioning.

    The main difference to proper :ref:`semantic versioning <semver>`
    is that this implementation doesn't require a minor or patch version.

    Version strings may also be prefixed with "v", e.g.:

    >>> v = Version('v1.1.1')
    >>> v.tuple
    (1, 1, 1, '')

    >>> v = Version('2.0')
    >>> v.tuple
    (2, 0, 0, '')

    >>> Version('3.1-beta').tuple
    (3, 1, 0, 'beta')

    >>> Version('1.0.1') > Version('0.0.1')
    True
    """

    #: Match version and pre-release/build information in version strings
    match_version = re.compile(r"([0-9][0-9\.]*)(.+)?").match

    def __init__(self, vstr):
        """Create new `Version` object.

        Args:
            vstr (basestring): Semantic version string.
        """
        if not vstr:
            raise ValueError("invalid version number: {!r}".format(vstr))

        self.vstr = vstr
        self.major = 0
        self.minor = 0
        self.patch = 0
        self.suffix = ""
        self.build = ""
        self._parse(vstr)

    def _parse(self, vstr):
        vstr = str(vstr)
        if vstr.startswith("v"):
            m = self.match_version(vstr[1:])
        else:
            m = self.match_version(vstr)
        if not m:
            raise ValueError("invalid version number: " + vstr)

        version, suffix = m.groups()
        parts = self._parse_dotted_string(version)
        self.major = parts.pop(0)
        if len(parts):
            self.minor = parts.pop(0)
        if len(parts):
            self.patch = parts.pop(0)
        if not len(parts) == 0:
            raise ValueError("version number too long: " + vstr)

        if suffix:
            # Build info
            idx = suffix.find("+")
            if idx > -1:
                self.build = suffix[idx + 1 :]
                suffix = suffix[:idx]
            if suffix:
                if not suffix.startswith("-"):
                    raise ValueError("suffix must start with - : " + suffix)
                self.suffix = suffix[1:]

    def _parse_dotted_string(self, s):
        """Parse string ``s`` into list of ints and strings."""
        parsed = []
        parts = s.split(".")
        for p in parts:
            if p.isdigit():
                p = int(p)
            parsed.append(p)
        return parsed

    @property
    def tuple(self):
        """Version number as a tuple of major, minor, patch, pre-release."""
        return (self.major, self.minor, self.patch, self.suffix)

    def __lt__(self, other):
        """Implement comparison."""
        if not isinstance(other, Version):
            raise ValueError("not a Version instance: {0!r}".format(other))
        t = self.tuple[:3]
        o = other.tuple[:3]
        if t < o:
            return True
        if t == o:  # We need to compare suffixes
            if self.suffix and not other.suffix:
                return True
            if other.suffix and not self.suffix:
                return False

            self_suffix = self._parse_dotted_string(self.suffix)
            other_suffix = self._parse_dotted_string(other.suffix)

            for s, o in zip_longest(self_suffix, other_suffix):
                if s is None:  # shorter value wins
                    return True
                elif o is None:  # longer value loses
                    return False
                elif type(s) != type(o):  # type coersion
                    s, o = str(s), str(o)
                if s == o:  # next if the same compare
                    continue
                return s < o  # finally compare
        # t > o
        return False

    def __eq__(self, other):
        """Implement comparison."""
        if not isinstance(other, Version):
            raise ValueError("not a Version instance: {0!r}".format(other))
        return self.tuple == other.tuple

    def __ne__(self, other):
        """Implement comparison."""
        return not self.__eq__(other)

    def __gt__(self, other):
        """Implement comparison."""
        if not isinstance(other, Version):
            raise ValueError("not a Version instance: {0!r}".format(other))
        return other.__lt__(self)

    def __le__(self, other):
        """Implement comparison."""
        if not isinstance(other, Version):
            raise ValueError("not a Version instance: {0!r}".format(other))
        return not other.__lt__(self)

    def __ge__(self, other):
        """Implement comparison."""
        return not self.__lt__(other)

    def __str__(self):
        """Return semantic version string."""
        vstr = "{0}.{1}.{2}".format(self.major, self.minor, self.patch)
        if self.suffix:
            vstr = "{0}-{1}".format(vstr, self.suffix)
        if self.build:
            vstr = "{0}+{1}".format(vstr, self.build)
        return vstr

    def __repr__(self):
        """Return 'code' representation of `Version`."""
        return "Version('{0}')".format(str(self))
