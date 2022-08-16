#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only

#
# Copyright (C) 2020 Elastio Software Inc.
#

import errno
import os
import subprocess
import time
import unittest
from random import randint

import elastio_snap
import util
from devicetestcase_multipart import DeviceTestCaseMultipart

class TestMultipart(DeviceTestCaseMultipart):
    def setUp(self):
        self.cow_file = "cow.snap"
        self.cow_full_paths = []
        self.snap_devices = []
        self.snap_mounts = []
        for i in range(self.part_count):
            self.cow_full_paths.append("{}/{}".format(self.mounts[i], self.cow_file))
            self.snap_devices.append("/dev/elastio-snap{}".format(self.minors[i]))
            self.snap_mounts.append("/tmp/elastio-snap{}".format(self.minors[i]))
            os.makedirs(self.snap_mounts[i], exist_ok=True)


    def test_setup_2_volumes_same_disk(self):
        for i in range(self.part_count):
            self.assertEqual(elastio_snap.setup(self.minors[i], self.devices[i], self.cow_full_paths[i]), 0)
            #self.addCleanup(elastio_snap.destroy, self.minors[i])

            self.assertTrue(os.path.exists(self.snap_devices[i]))

            snapdev = elastio_snap.info(self.minors[i])
            self.assertIsNotNone(snapdev)

            self.assertEqual(snapdev["error"], 0)
            self.assertEqual(snapdev["state"], 3)
            self.assertEqual(snapdev["cow"], "/{}".format(self.cow_file))
            self.assertEqual(snapdev["bdev"], self.devices[i])
            self.assertEqual(snapdev["version"], 1)

        # Destroy 2nd snapshot device first
        self.assertEqual(elastio_snap.destroy(self.minors[-1]), 0)

        # Write to the 2nd device
        testfile = "{}/testfile".format(self.mounts[-1])
        with open(testfile, "w") as f:
            f.write("The quick brown fox")

        self.addCleanup(os.remove, testfile)
        os.sync()
        time.sleep(5)

        # Destroy 1st snapshot device finally
        self.assertEqual(elastio_snap.destroy(self.minors[0]), 0)

    def test_modify_origins(self):
        for i in range(self.part_count):
            testfile = "{}/testfile".format(self.mounts[i])
            snapfile = "{}/testfile".format(self.snap_mounts[i])

            with open(testfile, "w") as f:
                f.write("The quick brown fox")

            self.addCleanup(os.remove, testfile)
            os.sync()
            md5_orig = util.md5sum(testfile)

            self.assertEqual(elastio_snap.setup(self.minors[i], self.devices[i], self.cow_full_paths[i]), 0)
            self.addCleanup(elastio_snap.destroy, self.minors[i])

            with open(testfile, "w") as f:
                f.write("jumps over the lazy dog")

            os.sync()
            # TODO: norecovery option, probably, should not be here after the fix of the elastio/elastio-snap#63
            opts = "nouuid,norecovery,ro" if (self.fs == "xfs") else "ro"
            util.mount(self.snap_devices[i], self.snap_mounts[i], opts)
            self.addCleanup(util.unmount, self.snap_mounts[i])
            self.addCleanup(os.rmdir, self.snap_mounts[i])

            md5_snap = util.md5sum(snapfile)
            self.assertEqual(md5_orig, md5_snap)

if __name__ == "__main__":
    unittest.main()
