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


def udev_start_exec_queue():
    cmd = ["udevadm", "control", "--start-exec-queue"]
    subprocess.check_call(cmd)


def udev_stop_exec_queue():
    cmd = ["udevadm", "control", "--stop-exec-queue"]
    subprocess.check_call(cmd)


def loop_create(path):
    cmd = ["losetup", "--find", "--show", "--partscan", path]
    return subprocess.check_output(cmd, timeout=10).rstrip().decode("utf-8")


def loop_destroy(loop):
    cmd = ["losetup", "-d", loop]
    subprocess.check_call(cmd, timeout=10)


def mkfs(device, fs="ext4"):
    if (fs == "xfs"):
        cmd = ["mkfs.xfs", device, "-f"]
    else:
        cmd = ["mkfs." + fs, "-F", device]

    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)


def dev_size_mb(device):
    return int(subprocess.check_output("blockdev --getsize64 %s" % device, shell=True))//1024**2


# This method finds name of the last partition of the disk
def get_last_partition(disk):
    # The output of this command 'lsblk /dev/loop0 -l -o NAME -n' is something like
    # loop0
    # loop0p1
    # but sometimes the order is random
    cmd = ["lsblk", disk, "-l", "-o", "NAME", "-n"]
    disk_and_parts = subprocess.check_output(cmd, timeout=10).rstrip().decode("utf-8").splitlines()
    disk_and_parts.sort()
    # We need to take last item from the sorted list, which is partition for sure
    return "/dev/" + disk_and_parts[-1]


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
        cmd = ["partprobe", device]
        subprocess.check_call(cmd, timeout=10)
        settle()
        partitions.append(get_last_partition(device))

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


def assemble_mirror_raid(devices, seed):
    # 1. Create RAID partitions
    partitions=[]
    for device in devices:
        cmd = ["parted", "--script", device, "mklabel gpt"]
        subprocess.check_call(cmd, timeout=10)
        cmd = ["parted", "--script", device, "mkpart 'RAID' 0% 100%"]
        subprocess.check_call(cmd, timeout=10)
        cmd = ["parted", "--script", device, "set 1 raid on"]
        subprocess.check_call(cmd, timeout=10)
        cmd = ["partprobe", device]
        subprocess.check_call(cmd, timeout=10)
        settle()
        partitions.append(get_last_partition(device))

    # 2. Create RAID 1 array.
    udev_stop_exec_queue()
    raid_dev = "/dev/md" + str(seed)
    cmd = ["mdadm", "--create", "--quiet", "--auto=yes", "--force", "--metadata=0.90", raid_dev, "--level=1", "--raid-devices=" + str(len(partitions))]
    cmd += partitions
    subprocess.check_call(cmd, timeout=10)
    udev_start_exec_queue()

    return raid_dev


def disassemble_mirror_raid(raid_device):
    udev_stop_exec_queue()
    cmd = ["mdadm", "--stop", raid_device]
    subprocess.check_call(cmd, timeout=10)
    udev_start_exec_queue()
