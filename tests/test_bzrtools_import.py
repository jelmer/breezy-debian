#    test_bzrtools_import.py -- Testsuite for bzrtool's import code
#    Copyright (C) 2010 James Westby <jw+debian@jameswestby.net>
#
#    This file is part of bzr-builddeb.
#
#    bzr-builddeb is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    bzr-builddeb is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with bzr-builddeb; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

from __future__ import absolute_import

from ..bzrtools_import import import_dir
from .. import tests


class ImportArchiveTests(tests.TestCaseWithTransport):

    def test_strips_common_prefix(self):
        tree = self.make_branch_and_tree(".")
        tree.lock_write()
        self.addCleanup(tree.unlock)
        self.build_tree(["source/", "source/a/", "source/a/a", "source/a/b"])
        import_dir(tree, "source")
        self.assertEqual(["", "a", "a/a", "a/b"],
            sorted([tree.id2path(i) for i in tree.all_file_ids()]))

    def test_removes_files(self):
        tree = self.make_branch_and_tree(".")
        tree.lock_write()
        self.build_tree(["a", "b"])
        tree.add(["a", "b"])
        self.addCleanup(tree.unlock)
        self.build_tree(["source/", "source/a"])
        import_dir(tree, "source")
        self.assertEqual(["", "a"],
            sorted([tree.id2path(i) for i in tree.all_file_ids()]))

    def test_takes_file_id_from_another_tree(self):
        tree = self.make_branch_and_tree(".")
        tree.lock_write()
        self.addCleanup(tree.unlock)
        file_ids_tree = self.make_branch_and_tree("fileids")
        self.build_tree(["fileids/a"])
        file_ids_tree.add(["a"], ["a-id"])
        self.build_tree(["source/", "source/a"])
        import_dir(tree, "source", file_ids_from=[file_ids_tree])
        self.assertEqual("a-id", tree.path2id("a"))

    def test_takes_file_id_from_first_of_several_trees(self):
        tree = self.make_branch_and_tree(".")
        tree.lock_write()
        self.addCleanup(tree.unlock)
        file_ids_tree = self.make_branch_and_tree("fileids")
        file_ids_tree2 = self.make_branch_and_tree("fileids2")
        self.build_tree(["fileids/a", "fileids2/a"])
        file_ids_tree.add(["a"], ["a-id"])
        file_ids_tree2.add(["a"], ["other-a-id"])
        self.build_tree(["source/", "source/a"])
        import_dir(tree, "source",
                file_ids_from=[file_ids_tree, file_ids_tree2])
        self.assertEqual("a-id", tree.path2id("a"))

    def test_takes_file_ids_from_last_of_several_trees_if_needed(self):
        tree = self.make_branch_and_tree(".")
        tree.lock_write()
        self.addCleanup(tree.unlock)
        file_ids_tree = self.make_branch_and_tree("fileids")
        file_ids_tree2 = self.make_branch_and_tree("fileids2")
        self.build_tree(["fileids/b", "fileids2/a"])
        file_ids_tree.add(["b"], ["b-id"])
        file_ids_tree2.add(["a"], ["other-a-id"])
        self.build_tree(["source/", "source/a"])
        import_dir(tree, "source",
                file_ids_from=[file_ids_tree, file_ids_tree2])
        self.assertEqual("other-a-id", tree.path2id("a"))

    def test_takes_file_id_from_target_tree(self):
        tree = self.make_branch_and_tree(".")
        tree.lock_write()
        self.addCleanup(tree.unlock)
        file_ids_tree = self.make_branch_and_tree("fileids")
        file_ids_tree2 = self.make_branch_and_tree("fileids2")
        self.build_tree(["fileids/a", "fileids2/a"])
        file_ids_tree.add(["a"], ["a-id"])
        file_ids_tree2.add(["a"], ["other-a-id"])
        self.build_tree(["source/", "source/a"])
        import_dir(tree, "source", file_ids_from=[file_ids_tree2],
                target_tree=file_ids_tree)
        self.assertEqual("a-id", tree.path2id("a"))

    def test_leaves_file_id_of_existing_file(self):
        tree = self.make_branch_and_tree(".")
        tree.lock_write()
        self.build_tree(["a"])
        tree.add(["a"], ["a-id"])
        self.addCleanup(tree.unlock)
        file_ids_tree = self.make_branch_and_tree("fileids")
        self.build_tree(["fileids/a"])
        file_ids_tree.add(["a"], ["other-a-id"])
        self.build_tree(["source/", "source/a"])
        import_dir(tree, "source", file_ids_from=[file_ids_tree])
        self.assertEqual("a-id", tree.path2id("a"))

    def test_replaces_file_id_of_existing_file_with_target_tree(self):
        tree = self.make_branch_and_tree(".")
        tree.lock_write()
        self.build_tree(["a"])
        tree.add(["a"], ["a-id"])
        self.addCleanup(tree.unlock)
        file_ids_tree = self.make_branch_and_tree("fileids")
        self.build_tree(["fileids/a"])
        file_ids_tree.add(["a"], ["other-a-id"])
        self.build_tree(["source/", "source/a"])
        import_dir(tree, "source", target_tree=file_ids_tree)
        self.assertEqual("other-a-id", tree.path2id("a"))

    def test_rename_of_file_in_target_tree(self):
        tree = self.make_branch_and_tree(".")
        tree.lock_write()
        self.build_tree(["a"])
        tree.add(["a"], ["a-id"])
        self.addCleanup(tree.unlock)
        file_ids_tree = self.make_branch_and_tree("fileids")
        self.build_tree(["fileids/a", "fileids/b"])
        # We give b the same id as a above, to simulate a rename
        file_ids_tree.add(["a", "b"], ["other-a-id", "a-id"])
        self.build_tree(["source/", "source/a", "source/b"])
        import_dir(tree, "source", target_tree=file_ids_tree)
        self.assertEqual("other-a-id", tree.path2id("a"))
        self.assertEqual("a-id", tree.path2id("b"))

    def test_rename_of_file_in_target_tree_with_unversioned_replacement(self):
        tree = self.make_branch_and_tree(".")
        tree.lock_write()
        self.build_tree(["a"])
        tree.add(["a"], ["a-id"])
        self.addCleanup(tree.unlock)
        file_ids_tree = self.make_branch_and_tree("fileids")
        self.build_tree(["fileids/b"])
        # We give b the same id as a above, to simulate a rename
        file_ids_tree.add(["b"], ["a-id"])
        # We continue to put "a" in the source, even though we didn't
        # put it in file_ids_tree
        self.build_tree(["source/", "source/a", "source/b"])
        import_dir(tree, "source", target_tree=file_ids_tree)
        self.assertEqual("a-id", tree.path2id("b"))
        # a should get a random file id, so we just check the obvious
        # things it shouldn't be
        self.assertNotEqual("a-id", tree.path2id("a"))
        self.assertNotEqual(None, tree.path2id("a"))

    def test_dir_rename_in_target_tree(self):
        tree = self.make_branch_and_tree(".")
        tree.lock_write()
        self.build_tree(["a/", "a/b"])
        tree.add(["a", "a/b"], ["a-id", "b-id"])
        self.addCleanup(tree.unlock)
        file_ids_tree = self.make_branch_and_tree("fileids")
        self.build_tree(["fileids/b/", "fileids/b/b"])
        # We give b the same id as a above, to simulate a rename
        file_ids_tree.add(["b", "b/b"], ["a-id", "b-id"])
        self.build_tree(["source/", "source/b/", "source/b/b"])
        import_dir(tree, "source", target_tree=file_ids_tree)
        self.assertEqual("a-id", tree.path2id("b"))
        self.assertEqual("b-id", tree.path2id("b/b"))

    def test_nonascii_filename(self):
        self.requireFeature(tests.UnicodeFilenameFeature)
        tree = self.make_branch_and_tree(".")
        tree.lock_write()
        self.addCleanup(tree.unlock)
        self.build_tree(["source/", u"source/\xa7"])
        import_dir(tree, "source")
        self.assertEqual(["", u"\xa7"],
            sorted([tree.id2path(i) for i in tree.all_file_ids()]))
