#!/bin/bash
me=`basename "$0"`

if [ -z "$1" ]; then
	echo "FCD release preparation utility"
	echo ""
	echo "Usage:"
	echo "	$me -b <bootloader_file> -r <runtime_ file> -v <version> -c <changelog>"
	echo "Example:"
	echo "	$me -b=esx-u-boot.bin -r=esx-vmlinux.bix -v=1.0 -c='New FCD'"
	echo ""
		exit
fi

FW_IDX=0

for i in "$@"
do
case $i in
	-b=*)
	BOOTLOADER="${i#*=}"
	shift # past argument=value
	;;
	-r=*)
	RUNTIME="${i#*=}"
	shift # past argument=value
	;;
	-v=*)
	VERSION="${i#*=}"
	shift # past argument=value
	;;
	-c=*)
	CHANGELOG="${i#*=}"
	shift # past argument=value
	;;
		*)
esac
done
echo "VERSION    = ${VERSION}"
echo "BOOTLOADER = ${BOOTLOADER}"
echo "RUNTIME    = ${RUNTIME}"
echo ""


if [ -z "$VERSION" ]; then
	echo "VERSION is empty"
	exit
fi

if [ -z "$CHANGELOG" ]; then
	echo "CHANGELOG is empty"
	exit
fi


echo "Copying firmware files..."

cp ${BOOTLOADER} config/includes.chroot/srv/tftp/esx-u-boot.bin
cp ${RUNTIME}    config/includes.chroot/srv/tftp/esx-vmlinux.bix


echo "Setting version to [${VERSION}] ..."
echo ${VERSION} > config/includes.chroot/srv/tftp/version.txt
git add config/includes.chroot/srv/tftp/version.txt

echo "Updating changelog [${CHANGELOG}] ..."
printf "${CHANGELOG}\n" > config/includes.chroot/srv/tftp/changes.txt
git add config/includes.chroot/srv/tftp/changes.txt

#echo "Commiting changes (git push is not executed !)"
#git commit -m "FCD release v${VERSION}"

echo "Done!"
