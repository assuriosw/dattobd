#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only

#
# Copyright (C) 2022 Elastio Software Inc.
#

import errno
import os
import platform
import subprocess
import time
import unittest
from random import randint

import elastio_snap
import util
from devicetestcase_multipart import DeviceTestCaseMultipart

class TestStorageRedirected(DeviceTestCaseMultipart):
    def setUp(self):
        self.source_part_num = 0
        self.target_part_num = 1

        self.cow_file = "cow.snap"
        self.minor = self.minors[self.source_part_num]
        self.device = self.devices[self.source_part_num]
        self.source_mount = self.mounts[self.source_part_num]
        self.target_mount = self.mounts[self.target_part_num]
        self.cow_full_path = "{}/{}".format(self.target_mount, self.cow_file)

        self.snap_device = "/dev/elastio-snap{}".format(self.minor)
        self.snap_mount = "/tmp/elio-snap-mnt{0:03d}".format(self.minor)
        os.makedirs(self.snap_mount, exist_ok=True)
        self.addCleanup(os.rmdir, self.snap_mount)

    def test_redirected_setup_snapshot(self):
        self.assertEqual(elastio_snap.setup(self.minor, self.device, self.cow_full_path), 0)
        self.addCleanup(elastio_snap.destroy, self.minor)
        self.assertTrue(os.path.exists(self.snap_device))

        snapdev = elastio_snap.info(self.minor)
        self.assertIsNotNone(snapdev)
        self.assertEqual(snapdev["flags"], elastio_snap.Flags.COW_REDIRECTED)
        self.assertEqual(snapdev["cow"], "/{}".format(self.cow_file))

        self.assertEqual(elastio_snap.destroy(self.minor), 0)
        self.assertFalse(os.path.exists(self.snap_device))
        self.assertIsNone(elastio_snap.info(self.minor))
        self.assertFalse(os.path.exists(self.cow_full_path))

    def test_redirected_setup_incremental(self):
        self.assertEqual(elastio_snap.setup(self.minor, self.device, self.cow_full_path), 0)
        self.addCleanup(elastio_snap.destroy, self.minor)
        self.assertTrue(os.path.exists(self.snap_device))

        snapdev = elastio_snap.info(self.minor)
        self.assertIsNotNone(snapdev)
        self.assertEqual(snapdev["flags"], elastio_snap.Flags.COW_REDIRECTED)
        self.assertEqual(snapdev["cow"], "/{}".format(self.cow_file))

        self.assertEqual(elastio_snap.transition_to_incremental(self.minor), 0)
        snapdev = elastio_snap.info(self.minor)
        self.assertIsNotNone(snapdev)
        self.assertEqual(snapdev["flags"], elastio_snap.Flags.COW_REDIRECTED)
        self.assertEqual(snapdev["cow"], "/{}".format(self.cow_file))

        new_cow_on_bdev = "{}/{}".format(self.source_mount, self.cow_file)
        self.assertEqual(elastio_snap.transition_to_snapshot(self.minor, new_cow_on_bdev), 0)
        snapdev = elastio_snap.info(self.minor)
        self.assertIsNotNone(snapdev)
        self.assertEqual(snapdev["flags"], elastio_snap.Flags.COW_ON_BDEV)
        self.assertEqual(snapdev["cow"], "/{}".format(self.cow_file))

    def test_redirected_modify_origin_snap(self):
        testfile = "{}/testfile".format(self.source_mount)
        snapfile = "{}/testfile".format(self.snap_mount)

        with open(testfile, "w") as f:
            f.write("The quick brown fox")

        self.addCleanup(os.remove, testfile)
        os.sync()
        md5_orig = util.md5sum(testfile)

        self.assertEqual(elastio_snap.setup(self.minor, self.device, self.cow_full_path), 0)
        self.addCleanup(elastio_snap.destroy, self.minor)

        with open(testfile, "w") as f:
            f.write("jumps over the lazy dog")

        os.sync()
        # TODO: norecovery option, probably, should not be here after the fix of the elastio/elastio-snap#63
        opts = "nouuid,norecovery,ro" if (self.fs == "xfs") else "ro"
        util.mount(self.snap_device, self.snap_mount, opts)
        self.addCleanup(util.unmount, self.snap_mount)

        md5_snap = util.md5sum(snapfile)
        self.assertEqual(md5_orig, md5_snap)

    def test_redirected_reload_snapshot(self):
        pass

    def test_redirected_reload_incremental(self):
        pass

    def test_redirected_umount_target_snapshot(self):
        pass

    def test_redirected_umount_target_incremental(self):
        pass

    def test_umount_source_snapshot(self):
        pass

    def test_umount_source_incremental(self):
        pass

    def destroy_dormant(self):
        self.assertEqual(elastio_snap.setup(self.minor, self.device, self.cow_full_path), 0)
        util.unmount(self.source_mount)

        self.addCleanup(os.remove, self.cow_full_path)
        self.addCleanup(util.mount, self.device, self.source_mount)

        self.assertEqual(elastio_snap.destroy(self.minor), 0)
        self.assertFalse(os.path.exists(self.snap_device))
        self.assertIsNone(elastio_snap.info(self.minor))
        self.assertFalse(os.path.exists(self.cow_full_path))


if __name__ == "__main__":
    unittest.main()
