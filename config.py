# Copyright (C) 2007 Jelmer Vernooij <jelmer@samba.org>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""Stores per-repository settings."""

from bzrlib import osutils, urlutils
from bzrlib.config import IniBasedConfig, config_dir, ensure_config_dir_exists

import os

# Settings are stored by UUID. 
# Data stored includes default branching scheme and locations the repository 
# was seen at.

def subversion_config_filename():
    """Return per-user configuration ini file filename."""
    return osutils.pathjoin(config_dir(), 'subversion.conf')

class SvnRepositoryConfig(IniBasedConfig):
    """Per-repository settings."""

    def __init__(self, uuid):
        name_generator = subversion_config_filename
        super(SvnRepositoryConfig, self).__init__(name_generator)
        self.uuid = uuid
        if not self.uuid in self._get_parser():
            self._get_parser()[self.uuid] = {}

    def set_branching_scheme(self, scheme):
        self.set_user_option('branching-scheme', scheme)

    def get_branching_scheme(self):
        try:
            return self._get_parser()[self.uuid]['branching-scheme']
        except KeyError:
            return None

    def get_locations(self):
        try:
            return set(self._get_parser()[self.uuid]['locations'].split(";"))
        except KeyError:
            return set()

    def add_location(self, location):
        locations = self.get_locations()
        locations.add(location)
        self.set_user_option('locations', ";".join(list(locations)))

    def set_user_option(self, name, value):
        conf_dir = os.path.dirname(self._get_filename())
        ensure_config_dir_exists(conf_dir)
        self._get_parser()[self.uuid][name] = value
        f = open(self._get_filename(), 'wb')
        self._get_parser().write(f)
        f.close()