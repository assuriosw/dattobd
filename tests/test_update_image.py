#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only

#
# Copyright (C) 2019 Datto, Inc.
# Additional contributions by Elastio Software, Inc are Copyright (C) 2020 Elastio Software Inc.
#

import math
import errno
import os
import platform
import unittest

import elastio_snap
import util
from devicetestcase import DeviceTestCase


class TestUpdateImage(DeviceTestCase):
    def setUp(self):
        self.snap_mount = "/mnt"
        self.snap_device = "/dev/elastio-snap{}".format(self.minor)
        self.snap_bkp = "./base-image.img"

        util.test_track(self._testMethodName, started=True)

    def tearDown(self):
        util.test_track(self._testMethodName, started=False)

    def test_update_sequence(self):
        iterations = 25
        file_name = "testfile"
        cow_paths = ["{}/{}".format(self.mount, "cow{}".format(i)) for i in range(0, iterations)]

        self.assertEqual(elastio_snap.setup(self.minor, self.device, cow_paths[0]), 0)
        self.addCleanup(elastio_snap.destroy, self.minor)

        # preparing base image
        util.dd(self.snap_device, self.snap_bkp, self.size_mb, bs="1M")
        self.addCleanup(os.remove, self.snap_bkp)
        write_testfile = "{}/{}".format(self.mount, file_name)

        for i in range(1, iterations):
            with open(write_testfile, "a") as f:
                f.write("Attempt to destroy humanity #{}\n".format(i))

            self.assertEqual(elastio_snap.transition_to_incremental(self.minor), 0)
            self.assertEqual(elastio_snap.transition_to_snapshot(self.minor, cow_paths[i]), 0)
            util.update_img(self.snap_device, cow_paths[i - 1], self.snap_bkp)
            os.remove(cow_paths[i - 1])

        temp_dir = util.mktemp_dir()
        self.addCleanup(os.rmdir, temp_dir)

        if self.fs == 'xfs':
            util.mount(self.snap_bkp, temp_dir, opts="nouuid")
            util.unmount(temp_dir)

        util.fsck(self.snap_bkp, self.fs)

        read_testfile = "{}/{}".format(temp_dir, file_name)

        if self.fs == 'xfs':
            util.mount(self.snap_bkp, temp_dir, opts="nouuid")
        else:
            util.mount(self.snap_bkp, temp_dir)

        self.addCleanup(util.unmount, temp_dir)
        self.assertEqual(util.file_lines(read_testfile), iterations - 1)

 
if __name__ == "__main__":
    unittest.main()
