# SPDX-License-Identifier: GPL-2.0-only

#
# Copyright (C) 2020 Elastio Software Inc.
#

import os
import subprocess
import unittest

import kmod
import util

from random import randint

@unittest.skipUnless(os.geteuid() == 0, "Must be run as root")
@unittest.skipIf(os.getenv('TEST_DEVICES'), "Multipart testcase works now just with the internal loopback devices")
class DeviceTestCaseMultipart(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # For now let's hardcode 2 partitions
        cls.part_count = 2
        cls.minors = []
        for i in range(cls.part_count):
            # Unexpectedly randint can generate 2 same numbers in a row.
            # So, let's verify the difference of the random numbers.
            while True:
                r = randint(0, 23)
                if not r in cls.minors: break
            cls.minors.append(r)

        cls.kmod = kmod.Module("../src/elastio-snap.ko")
        cls.kmod.load(debug=1)

        cls.backing_store = ("/tmp/disk_{0:03d}.img".format(cls.minors[0]))
        util.dd("/dev/zero", cls.backing_store, 256, bs="1M")

        cls.device = util.loop_create(cls.backing_store, cls.part_count)
        cls.devices = []
        cls.devices += util.get_partitions(cls.device)

        cls.mounts = []
        cls.fs = os.getenv('TEST_FS', 'ext4')
        for i in range(cls.part_count):
            util.mkfs(cls.devices[i], cls.fs)
            cls.mounts.append("/tmp/elastio-snap_{0:03d}".format(cls.minors[i]))
            os.makedirs(cls.mounts[i], exist_ok=True)
            util.mount(cls.devices[i], cls.mounts[i])

    @classmethod
    def tearDownClass(cls):
        for mount in cls.mounts:
            util.unmount(mount)
            os.rmdir(mount)

        util.loop_destroy(cls.device)
        os.unlink(cls.backing_store)

        cls.kmod.unload()
