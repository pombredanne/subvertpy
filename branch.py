# Copyright (C) 2005-2006 Jelmer Vernooij <jelmer@samba.org>

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

from bzrlib.branch import Branch, BranchFormat, BranchCheckResult, BzrBranch
from bzrlib.delta import compare_trees
from bzrlib.errors import (NotBranchError, NoWorkingTree, NoSuchRevision, 
                           NoSuchFile)
from bzrlib.inventory import (Inventory, InventoryFile, InventoryDirectory, 
                              ROOT_ID)
from bzrlib.revision import Revision, NULL_REVISION
from bzrlib.tree import Tree, EmptyTree
from bzrlib.trace import mutter, note
from bzrlib.workingtree import WorkingTree

import os

import svn.core, svn.ra
from svn.core import SubversionException

from tree import SvnBasisTree

svn.ra.initialize()

class FakeControlFiles(object):
    def get_utf8(self, name):
        raise NoSuchFile(name)

    def get(self, name):
        raise NoSuchFile(name)


class SvnBranch(Branch):
    """Maps to a Branch in a Subversion repository """
    def __init__(self, repos, branch_path):
        """Instantiate a new SvnBranch.

        :param repos: SvnRepository this branch is part of.
        :param branch_path: Relative path inside the repository this
            branch is located at.
        """
        self.repository = repos
        self.branch_path = branch_path
        self.control_files = FakeControlFiles()
        self._generate_revision_history()
        self.base = "%s/%s" % (repos.url, branch_path)
        self._format = SvnBranchFormat()
        mutter("Connected to branch at %s" % branch_path)

    def basis_tree(self):
        return SvnBasisTree(self)

    def check(self):
        """See Branch.Check.

        Doesn't do anything for Subversion repositories at the moment (yet).
        """
        return BranchCheckResult(self)
        
    def _generate_revision_history(self):
        def rcvr((paths, rev)):
            return self.repository.generate_revision_id(rev, self.branch_path)
        self._revision_history = map(rcvr, 
                self.repository._log.follow_history(self.branch_path, 
                    svn.ra.get_latest_revnum(self.repository.ra)))
        self._revision_history.reverse()

    def set_root_id(self, file_id):
        raise NotImplementedError(self.set_root_id)
            
    def get_root_id(self):
        inv = self.repository.get_inventory(self.last_revision())
        return inv.root.file_id

    def _get_nick(self):
        try:
            return "/".split(self.branch_path)[-1]
        except ValueError:
            return None

    nick = property(_get_nick)

    def abspath(self, name):
        return self.base+"/"+name

    def push_stores(self, branch_to):
        raise NotImplementedError(self.push_stores)

    def set_revision_history(self, rev_history):
        raise NotImplementedError(self.set_revision_history)

    def set_push_location(self, location):
        raise NotImplementedError(self.set_push_location)

    def get_push_location(self):
        # get_push_location not supported on Subversion
        return None

    def revision_history(self):
        return self._revision_history

    def pull(self, source, overwrite=False):
        raise NotImplementedError(self.pull)

    def update_revisions(self, other, stop_revision=None):
        raise NotImplementedError(self.update_revisions)

    def pullable_revisions(self, other, stop_revision):
        raise NotImplementedError(self.pullable_revisions)
        
    # The remote server handles all this for us
    def lock_write(self):
        pass
        
    def lock_read(self):
        pass

    def unlock(self):
        pass

    def get_parent(self):
        return None

    def set_parent(self, url):
        raise NotImplementedError(self.set_parent, 
                                  'can not change parent of SVN branch')

    def get_transaction(self):
        raise NotImplementedError(self.get_transaction)

    def append_revision(self, *revision_ids):
        # FIXME: raise NotImplementedError(self.append_revision)
        pass

    def get_physical_lock_status(self):
        return False

    def sprout(self, to_bzrdir, revision_id=None):
        result = BranchFormat.get_default_format().initialize(to_bzrdir)
        self.copy_content_into(result, revision_id=revision_id)
        result.set_parent(self.bzrdir.root_transport.base)
        return result

    def copy_content_into(self, destination, revision_id=None):
        new_history = self.revision_history()
        if revision_id is not None:
            try:
                new_history = new_history[:new_history.index(revision_id) + 1]
            except ValueError:
                rev = self.repository.get_revision(revision_id)
                new_history = rev.get_history(self.repository)[1:]
        destination.set_revision_history(new_history)
        parent = self.get_parent()
        if parent:
            destination.set_parent(parent)


class SvnBranchFormat(BranchFormat):
    """ Branch format for Subversion Branches."""
    def __init__(self):
        BranchFormat.__init__(self)

    def get_format_description(self):
        """See Branch.get_format_description."""
        return 'Subversion Smart Server'

    def get_format_string(self):
        return 'Subversion Smart Server'

    def initialize(self, to_bzrdir):
        raise NotImplementedError(self.initialize)

