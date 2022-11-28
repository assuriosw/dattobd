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
        self.mount = self.mounts[self.target_part_num]
        self.cow_full_path = "{}/{}".format(self.mount, self.cow_file)

        self.snap_device = "/dev/elastio-snap{}".format(self.minor)
        self.snap_mount = "/tmp/elio-snap-mnt{0:03d}".format(self.minor)
        os.makedirs(self.snap_mount, exist_ok=True)
        self.addCleanup(os.rmdir, self.snap_mount)


    def test_setup_and_destroy_redirected(self):
        self.assertEqual(elastio_snap.setup(self.minor, self.device, self.cow_full_path), 0)
        self.assertTrue(os.path.exists(self.snap_device))

        snapdev = elastio_snap.info(self.minor)
        self.assertIsNotNone(snapdev)

        self.assertEqual(elastio_snap.destroy(self.minor), 0)
        self.assertFalse(os.path.exists(self.snap_device))
        self.assertIsNone(elastio_snap.info(self.minor))
        self.assertFalse(os.path.exists(self.cow_full_path))


    def test_destroy_dormant(self):
        self.assertEqual(elastio_snap.setup(self.minor, self.device, self.cow_full_path), 0)
        util.unmount(self.mount)

        #self.addCleanup(os.remove, self.cow_full_path)
        self.addCleanup(util.mount, self.device, self.mount)

        self.assertEqual(elastio_snap.destroy(self.minor), 0)
        self.assertFalse(os.path.exists(self.snap_device))
        self.assertIsNone(elastio_snap.info(self.minor))
        self.assertFalse(os.path.exists(self.cow_full_path))


if __name__ == "__main__":
    unittest.main()
