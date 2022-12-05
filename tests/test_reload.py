#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only

#
# Copyright (C) 2022 Elastio Software Inc.
#

import errno
import os
import unittest
import platform
import elastio_snap
import util
from devicetestcase import DeviceTestCase


class TestReload(DeviceTestCase):
    def setUp(self):
        self.cow_file = "cow.snap"
        self.cow_full_path = "{}/{}".format(self.mount, self.cow_file)
        self.cow_reload_path = "/{}".format(self.cow_file)
        self.snap_device = "/dev/elastio-snap{}".format(self.minor)

    def test_reload_snap_invalid_minor(self):
        self.assertEqual(elastio_snap.reload_snapshot(1000, self.device, self.cow_reload_path), errno.EINVAL)
        self.assertFalse(os.path.exists(self.snap_device))
        self.assertIsNone(elastio_snap.info(self.minor))

    def test_reload_inc_invalid_minor(self):
        self.assertEqual(elastio_snap.reload_incremental(1000, self.device, self.cow_reload_path), errno.EINVAL)
        self.assertFalse(os.path.exists(self.snap_device))
        self.assertIsNone(elastio_snap.info(self.minor))

    def test_reload_snap_volume_path_is_dir(self):
        self.assertEqual(elastio_snap.reload_snapshot(self.minor, self.mount, self.cow_full_path), errno.ENOTBLK)
        self.assertFalse(os.path.exists(self.snap_device))
        self.assertIsNone(elastio_snap.info(self.minor))

    def test_reload_inc_volume_path_is_dir(self):
        self.assertEqual(elastio_snap.reload_incremental(self.minor, self.mount, self.cow_full_path), errno.ENOTBLK)
        self.assertFalse(os.path.exists(self.snap_device))
        self.assertIsNone(elastio_snap.info(self.minor))

    def test_reload_snap_device_no_exists(self):
        self.assertEqual(elastio_snap.reload_snapshot(self.minor, "/dev/not_exist_device", self.cow_full_path), errno.ENOENT)
        self.assertFalse(os.path.exists(self.snap_device))
        self.assertIsNone(elastio_snap.info(self.minor))

    def test_reload_inc_device_no_exists(self):
        self.assertEqual(elastio_snap.reload_incremental(self.minor, "/dev/not_exist_device", self.cow_full_path), errno.ENOENT)
        self.assertFalse(os.path.exists(self.snap_device))
        self.assertIsNone(elastio_snap.info(self.minor))

    def test_reload_unverified_snapshot(self):
        util.unmount(self.mount)
        self.addCleanup(util.mount, self.device, self.mount)

        self.assertEqual(elastio_snap.reload_snapshot(self.minor, self.device, self.cow_reload_path, ignore_snap_errors=True), 0)
        self.addCleanup(elastio_snap.destroy, self.minor)
        self.assertFalse(os.path.exists(self.snap_device))

        snapdev = elastio_snap.info(self.minor)
        self.assertIsNotNone(snapdev)

        self.assertEqual(snapdev["error"], 0)
        self.assertEqual(snapdev["state"], elastio_snap.State.UNVERIFIED | elastio_snap.State.SNAPSHOT)
        self.assertEqual(snapdev["cow"], "/{}".format(self.cow_file))
        self.assertEqual(snapdev["bdev"], self.device)
        self.assertEqual(snapdev["version"], 0)
        self.assertEqual(snapdev["falloc_size"], 0)
        self.assertEqual(snapdev["ignore_snap_errors"], True)

        # Mount and test that the non-existent cow file been handled
        util.mount(self.device, self.mount)
        self.addCleanup(util.unmount, self.device, self.mount)

        snapdev = elastio_snap.info(self.minor)
        self.assertIsNotNone(snapdev)

        self.assertEqual(snapdev["error"], -errno.ENOENT)
        self.assertEqual(snapdev["state"], elastio_snap.State.UNVERIFIED | elastio_snap.State.SNAPSHOT)
        self.assertEqual(snapdev["cow"], "/{}".format(self.cow_file))
        self.assertEqual(snapdev["bdev"], self.device)
        self.assertEqual(snapdev["version"], 0)
        self.assertEqual(snapdev["falloc_size"], 0)
        self.assertEqual(snapdev["ignore_snap_errors"], True)


    def test_reload_unverified_incremental(self):
        util.unmount(self.mount)
        self.addCleanup(util.mount, self.device, self.mount)

        self.assertEqual(elastio_snap.reload_incremental(self.minor, self.device, self.cow_reload_path, ignore_snap_errors=True), 0)
        self.addCleanup(elastio_snap.destroy, self.minor)
        self.assertFalse(os.path.exists(self.snap_device))

        snapdev = elastio_snap.info(self.minor)
        self.assertIsNotNone(snapdev)

        self.assertEqual(snapdev["error"], 0)
        self.assertEqual(snapdev["state"], elastio_snap.State.UNVERIFIED)
        self.assertEqual(snapdev["cow"], "/{}".format(self.cow_file))
        self.assertEqual(snapdev["bdev"], self.device)
        self.assertEqual(snapdev["version"], 0)
        self.assertEqual(snapdev["falloc_size"], 0)
        self.assertEqual(snapdev["ignore_snap_errors"], True)

        # Mount and test that the non-existent cow file been handled
        util.mount(self.device, self.mount)
        self.addCleanup(util.unmount, self.device, self.mount)

        snapdev = elastio_snap.info(self.minor)
        self.assertIsNotNone(snapdev)

        self.assertEqual(snapdev["error"], -errno.ENOENT)
        self.assertEqual(snapdev["state"], elastio_snap.State.UNVERIFIED)
        self.assertEqual(snapdev["cow"], "/{}".format(self.cow_file))
        self.assertEqual(snapdev["bdev"], self.device)
        self.assertEqual(snapdev["version"], 0)
        self.assertEqual(snapdev["falloc_size"], 0)
        self.assertEqual(snapdev["ignore_snap_errors"], True)

    def test_reload_verified_snapshot(self):
        self.assertEqual(elastio_snap.setup(self.minor, self.device, self.cow_full_path, ignore_snap_errors=True), 0)

        util.unmount(self.mount)
        self.addCleanup(util.mount, self.device, self.mount)

        self.kmod.unload()
        self.kmod.load()
        self.assertFalse(os.path.exists(self.snap_device))

        self.assertEqual(elastio_snap.reload_snapshot(self.minor, self.device, self.cow_reload_path), 0)
        self.addCleanup(elastio_snap.destroy, self.minor)
        self.assertFalse(os.path.exists(self.snap_device))

        snapdev = elastio_snap.info(self.minor)
        self.assertIsNotNone(snapdev)

        self.assertEqual(snapdev["error"], 0)
        self.assertEqual(snapdev["state"], elastio_snap.State.UNVERIFIED | elastio_snap.State.SNAPSHOT)
        self.assertEqual(snapdev["cow"], "/{}".format(self.cow_file))
        self.assertEqual(snapdev["bdev"], self.device)
        self.assertEqual(snapdev["version"], 0)
        self.assertEqual(snapdev["falloc_size"], 0)
        self.assertEqual(snapdev["ignore_snap_errors"], False)

        # Mount and test that snapshot is active
        util.mount(self.device, self.mount)
        self.addCleanup(util.unmount, self.device, self.mount)

        self.assertTrue(os.path.exists(self.cow_full_path))
        self.assertTrue(os.path.exists(self.snap_device))

        snapdev = elastio_snap.info(self.minor)
        self.assertIsNotNone(snapdev)

        self.assertEqual(snapdev["error"], 0)
        self.assertEqual(snapdev["state"], elastio_snap.State.ACTIVE | elastio_snap.State.SNAPSHOT)
        self.assertEqual(snapdev["cow"], "/{}".format(self.cow_file))
        self.assertEqual(snapdev["bdev"], self.device)
        self.assertEqual(snapdev["version"], 1)
        self.assertNotEqual(snapdev["falloc_size"], 0)
        self.assertEqual(snapdev["ignore_snap_errors"], False)

    def test_reload_verified_inc(self):
        self.assertEqual(elastio_snap.setup(self.minor, self.device, self.cow_full_path, ignore_snap_errors=True), 0)
        self.assertEqual(elastio_snap.transition_to_incremental(self.minor), 0)

        util.unmount(self.mount)
        self.addCleanup(util.mount, self.device, self.mount)

        self.kmod.unload()
        self.kmod.load()
        self.assertFalse(os.path.exists(self.snap_device))

        self.assertEqual(elastio_snap.reload_incremental(self.minor, self.device, self.cow_reload_path), 0)
        self.addCleanup(elastio_snap.destroy, self.minor)
        self.assertFalse(os.path.exists(self.snap_device))

        snapdev = elastio_snap.info(self.minor)
        self.assertIsNotNone(snapdev)

        self.assertEqual(snapdev["error"], 0)
        self.assertEqual(snapdev["state"], elastio_snap.State.UNVERIFIED)
        self.assertEqual(snapdev["cow"], "/{}".format(self.cow_file))
        self.assertEqual(snapdev["bdev"], self.device)
        self.assertEqual(snapdev["version"], 0)
        self.assertEqual(snapdev["falloc_size"], 0)
        self.assertEqual(snapdev["ignore_snap_errors"], False)

        # Mount and test that snapshot is active
        util.mount(self.device, self.mount)
        self.addCleanup(util.unmount, self.device, self.mount)

        self.assertTrue(os.path.exists(self.cow_full_path))
        self.assertFalse(os.path.exists(self.snap_device))

        snapdev = elastio_snap.info(self.minor)
        self.assertIsNotNone(snapdev)

        self.assertEqual(snapdev["error"], 0)
        self.assertEqual(snapdev["state"], elastio_snap.State.ACTIVE)
        self.assertEqual(snapdev["cow"], "/{}".format(self.cow_file))
        self.assertEqual(snapdev["bdev"], self.device)
        self.assertEqual(snapdev["version"], 1)
        self.assertNotEqual(snapdev["falloc_size"], 0)
        self.assertEqual(snapdev["ignore_snap_errors"], False)


if __name__ == "__main__":
    unittest.main()
