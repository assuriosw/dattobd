#!/bin/bash

set -ex

fs=xfs
#fs=ext4

dev=/dev/vdb1
mnt=/mnt
bkp_dir=/backups
bkp=$bkp_dir/bkb.img
snap=/dev/elastio-snap0
cow=$mnt/cow
ret=0

force="-F"
[ "$fs" = "xfs" ] && force="-f"

mkdir -p $bkp_dir

umount $dev || true

dd if=/dev/zero of=$dev count=255 bs=1M
mkfs.$fs $dev $force

mount $dev $mnt

#xfs_freeze -f /mnt
#xfs_freeze -u /mnt
#sleep 16
elioctl setup-snapshot $dev ${cow}0 0
echo "Snap 0 created" > $mnt/snap0.txt

#sleep 16
#xfs_freeze -f /mnt
#xfs_freeze -u /mnt
dd if=$snap of=$bkp bs=1M

max=25
for i in $(seq 0 $max); do
#xfs_freeze -f /mnt
#xfs_freeze -u /mnt
#sleep 16
    sync
    for k in {0..5}; do
err=0
	err_msg=$(elioctl transition-to-incremental 0 2>&1) || err=$?
        if [ $err -ne 0 ] && echo $err_msg | grep "Device or resource busy" ; then
             sleep 1
	else
	     break
        fi
    done

[ $err -ne 0 ] && exit $err

#xfs_freeze -f /mnt
#xfs_freeze -u /mnt
    echo "Snap $i is in the incremental mode" >> $mnt/snap$i.txt
#sleep 16
    j=$((i+1))
#xfs_freeze -f /mnt
#xfs_freeze -u /mnt
    sync
    elioctl transition-to-snapshot ${cow}$j 0

#xfs_freeze -f /mnt
#xfs_freeze -u /mnt
    echo "Snap $j is in the snapshot mode" >> $mnt/snap$j.txt
#sleep 16

    update-img $snap ${cow}$i $bkp
    rm ${cow}$i

    #cat /proc/elastio-info
done

    for k in {0..5}; do
err=0
	err_msg=$(elioctl destroy 0 2>&1) || err=$?
        if [ $err -ne 0 ] && echo $err_msg | grep "Device or resource busy" ; then
             sleep 1
	else
	     break
        fi
    done

umount $dev

loopdev=$(losetup --find --show $bkp)

if [ "$fs" = "xfs" ]; then
	fsck_cmd="xfs_repair -n -v $loopdev"
else
	fsck_cmd="fsck.$fs -n -f -v $loopdev"
fi

$fsck_cmd || ret=$?

mount -o nouuid $loopdev $mnt
set +x
ls $mnt
for f in $(ls $mnt/snap*.txt | sort); do
    cat $f
done
set -x
umount $loopdev

# $fsck_cmd && echo "CLEAN!!!" || echo "FAILED!!!"

losetup -d $loopdev
rm $bkp

exit $ret
