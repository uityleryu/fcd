#!/bin/sh

VER=$1

NAME_PREFIX=UAPFactory
if [ $# -lt 1 ]; then
	echo "Using <build.properties> for version number"
	eval $(cat build.properties)
	BUILD_TIME=$(date -d "${build_date} ${build_time}" +%y%m%d_%H%M)
	if [ "${scm_reftype}" = "atag" ]; then
		CDNAME=${NAME_PREFIX}-${scm_refname}_${scm_distance}
		IMAGE_NAME=${NAME_PREFIX}-${scm_refname}_${scm_distance}
	elif [ "${scm_dirty}" != "true" ]; then
		CDNAME=${NAME_PREFIX}-${scm_refname}_${scm_distance}
		IMAGE_NAME=${NAME_PREFIX}-${scm_refname}_${scm_distance}
	else
		CDNAME=${NAME_PREFIX}-${scm_refname}_${scm_distance}_${build_user}@${build_host}_${BUILD_TIME}
		IMAGE_NAME=${NAME_PREFIX}-${scm_refname}_${scm_distance}M
	fi
else
	CDNAME=${VER}
	IMAGE_NAME=${VER}
fi

echo "Will build $CDNAME with label $IMAGE_NAME"

touch edit/etc/skel/Desktop/version.txt
chmod 666 edit/etc/skel/Desktop/version.txt
echo $IMAGE_NAME > edit/etc/skel/Desktop/version.txt

convert edit/usr/share/xfce4/backdrops/xubuntu-karmic-backup.png \
-pointsize 60 \
-fill "Grey" \
-gravity "SouthEast" \
-draw "text 10,50 '$IMAGE_NAME'" \
edit/usr/share/xfce4/backdrops/xubuntu-karmic.png

# regenerate manifest
echo "Regenerating manifest..."

chmod +w extract-cd/casper/filesystem.manifest
chroot edit dpkg-query -W --showformat='${Package} ${Version}\n' > extract-cd/casper/filesystem.manifest
cp extract-cd/casper/filesystem.manifest extract-cd/casper/filesystem.manifest-desktop
sed -ie '/ubiquity/d' extract-cd/casper/filesystem.manifest-desktop
echo " ... done."

# compress filesystem
echo "Compressing filesystem..."
[ ! -f extract-cd/casper/filesystem.squashfs ] || rm extract-cd/casper/filesystem.squashfs
mksquashfs edit extract-cd/casper/filesystem.squashfs
echo " ... done."

# Set an image name in extract-cd/README.diskdefines
sed -i 's/^#define DISKNAME.*$/#define DISKNAME  UBIQUITY LiteStation Production CD/' extract-cd/README.diskdefines

# Remove old md5sum.txt and calculate new md5 sums
echo "Recalculating md5sums..."
rm extract-cd/md5sum.txt
(cd extract-cd && find . -type f -print0 | xargs -0 md5sum > md5sum.txt)
echo " ... done."

# Create Iso
echo "Creating ISO Image..."
cd extract-cd
mkisofs -r -V "$IMAGE_NAME" -cache-inodes -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o "../$CDNAME.iso" .
echo " ... done."

cd ..
md5sum -b $CDNAME.iso > $CDNAME.iso.md5sum

#echo "v$VER Factory CD with " > $CDNAME.README
#echo "" >> $CDNAME.README
#echo "Firmwares on CD:" >> $CDNAME.README
#./build-readme.pl edit/tftpboot/*-fw.bin >> $CDNAME.README
#./make_readme.sh $VER > $CDNAME.README
cp README.README $CDNAME.README

