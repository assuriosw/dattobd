#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only

#
# Copyright (C) 2019 Datto, Inc.
# Additional contributions by Elastio Software, Inc are Copyright (C) 2020 Elastio Software Inc.
#

import hashlib
import subprocess


def mount(device, path, opts=None):
    cmd = ["mount", device, path]
    if opts:
        cmd += ["-o", opts]

    subprocess.check_call(cmd, timeout=10)


def unmount(path):
    cmd = ["umount", path]
    subprocess.check_call(cmd, timeout=10)


def dd(ifile, ofile, count, **kwargs):
    cmd = ["dd", "status=none", "if={}".format(ifile), "of={}".format(ofile), "count={}".format(count)]
    for k, v in kwargs.items():
        cmd.append("{}={}".format(k, v))

    subprocess.check_call(cmd, timeout=30)


def md5sum(path):
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)

    return md5.hexdigest()


def settle(timeout=20):
    cmd = ["udevadm", "settle", "-t", "{}".format(timeout)]
    subprocess.check_call(cmd, timeout=(timeout + 10))


def loop_create(path):
    cmd = ["losetup", "--find", "--show", path]
    return subprocess.check_output(cmd, timeout=10).rstrip().decode("utf-8")


def loop_destroy(loop):
    cmd = ["losetup", "-d", loop]
    subprocess.check_call(cmd, timeout=10)


def mkfs(device, fs="ext4"):
    if (fs == "xfs"):
        cmd = ["mkfs.xfs", device, "-f"]
    else:
        cmd = ["mkfs." + fs, "-F", device]

    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=40)

def dev_size_mb(device):
    return int(subprocess.check_output("blockdev --getsize64 %s" % device, shell=True))//1024**2

def assemble_mirror_lvm(devices, seed):
    # 1. Create LVM partitions
    partitions=[]
    for device in devices:
        cmd = ["parted", "--script", device, "mklabel gpt"]
        subprocess.check_call(cmd, timeout=10)
        cmd = ["parted", "--script", device, "mkpart 'LVM2' 0% 100%"]
        subprocess.check_call(cmd, timeout=10)
        cmd = ["parted", "--script", device, "set 1 lvm on"]
        subprocess.check_call(cmd, timeout=10)

        cmd = ["lsblk", device, "-l", "-o", "NAME", "-n"]
        partitions.append("/dev/" + subprocess.check_output(cmd, timeout=10).rstrip().decode("utf-8").split("\n")[-1])

    # 2. Create physical volume.  The command looks like 'pvcreate /dev/sdb1 /dev/sdc1'
    cmd = ["pvcreate"]
    cmd += partitions
    subprocess.check_call(cmd, timeout=10)

    # 3. Create volume group.  The command looks like 'vgcreate volgroup_mirror /dev/sdb1 /dev/sdc1'
    vol_group = "vg_mirror" + str(seed)
    logical_vol = "lv_mirror" + str(seed)
    cmd = ["vgcreate", vol_group]
    cmd += partitions
    subprocess.check_call(cmd, timeout=10)

    # 4. Create logical volume with mirroring.  The command looks like 'lvcreate -L 230MB -m1 -n vg_mirror lv_mirror'
    dev_size = dev_size_mb(devices[1])
    log_vol_size = str(dev_size - int(dev_size/10)) + "MB"
    cmd = ["lvcreate", "-L", log_vol_size, "-m1", "-n", logical_vol, vol_group]
    subprocess.check_call(cmd, timeout=10)
    lvm_dev = "/dev/" + vol_group + "/" + logical_vol

    # 5. Convert LVM logical volume name to the kernel bdev name like /dev/vg_mirror22/lv_mirror22 to the /dev/dm-4 or so
    cmd = ["readlink", "-f", lvm_dev]
    return subprocess.check_output(cmd, timeout=10).rstrip().decode("utf-8")


def disassemble_mirror_lvm(lvm_device):
    # 0. Preperation. Convert /dev/dm-X kernel bdev name or any kind of the LVM device name to the /dev/mapper/vg_name-lv_name
    cmd = ["find", "-L", "/dev/mapper", "-samefile", lvm_device]
    lvm_device = subprocess.check_output(cmd, timeout=10).rstrip().decode("utf-8")

    # 1. Disable LVM.  The command looks like 'lvchange -an /dev/mapper/vg_mirror22-lv_mirror22'
    cmd = ["lvchange", "-an", lvm_device]
    subprocess.check_call(cmd, timeout=10)

    # 2. Delete LVM volume.  The command looks like 'lvremove /dev/mapper/vg_mirror22-lv_mirror22'
    cmd = ["lvremove", "-f", lvm_device]
    subprocess.check_call(cmd, timeout=10)

    # 3. Disable volume group.  The command looks like 'vgremove vg_mirror22'
    vol_group = lvm_device.replace("/dev/mapper/", "").split("-")[0]
    cmd = ["vgremove", vol_group]
    subprocess.check_call(cmd, timeout=10)


def assemble_mirror_raid(devices):
    return "not implemented"


def disassemble_mirror_raid(raid_device):
    return "not implemented"
