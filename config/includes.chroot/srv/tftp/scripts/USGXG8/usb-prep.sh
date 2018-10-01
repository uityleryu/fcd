#!/bin/sh

DEV_NAME=$1
IMG_FILE=$2
DEV="/dev/$DEV_NAME"

fatal () {
    echo "[FAILED] $@"
    exit 1
}

[ -b "$DEV" ] || fatal 'Invalid device'
[ -f "$IMG_FILE" ] || fatal 'Invalid image file'

parted -s $DEV mklabel msdos

(parted -s $DEV mkpart primary fat32 1049k 150M \
 && parted -s $DEV mkpart primary ext2 150M 1900M) \
    || fatal 'Failed to create partitions'

(mkdosfs ${DEV}1 && mkfs.ext3 ${DEV}2) || fatal 'Make filesystems'

D1=/media/usb1
D2=/media/usb2
mkdir -p $D1 $D2 || fatal 'Create directories'

(mount ${DEV}1 $D1 && mount ${DEV}2 $D2) || fatal 'Mount filesystems'

echo 'I: Installing kernel image'
TKERN=vmlinux.tmp
KERN=vmlinux.64
(
    cd $D1
    tar -xf $IMG_FILE $TKERN $TKERN.md5 || fatal 'Extract kernel'
    osum=$(cat $TKERN.md5)
    nsum=$(md5sum $TKERN | sed 's/ .*$//')
    [ "$osum" == "$nsum" ] || fatal 'Kernel checksum'
    (mv $TKERN $KERN && mv $TKERN.md5 $KERN.md5) || fatal 'Move kernel'
) || exit 1

echo 'I: Installing root image'
TRIMG=squashfs.tmp
RIMG=squashfs.img
TVFILE=version.tmp
VFILE=version
(
    cd $D2
    tar -xf $IMG_FILE $TRIMG $TRIMG.md5 $TVFILE || fatal 'Extract root'
    osum=$(cat $TRIMG.md5)
    nsum=$(md5sum $TRIMG | sed 's/ .*$//')
    [ "$osum" == "$nsum" ] || fatal 'Root checksum'
    (mv $TRIMG $RIMG && mv $TRIMG.md5 $RIMG.md5 && mv $TVFILE $VFILE) \
        || fatal 'Move root'
) || exit 1

echo 'I: Finishing'
sync ; umount $D1 $D2

echo '[DONE]'
