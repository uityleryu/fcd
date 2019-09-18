#!/bin/sh

# For build environmental variables
OUTDIR=$(pwd)/output
APP_DIR="usr/local/sbin"
EXLIVECD="${OUTDIR}/ExtractLivedCD"
EXSQUASHFS="${OUTDIR}/ExtractLivedSquashfs"
STAGEDIR="${OUTDIR}/stage"
NEWLIVEDCD="${STAGEDIR}/NewLiveCD"
NEWSQUASHFS="${STAGEDIR}/NewSquashfs"
FWIMG_DIR="${BUILD_DIR}/fcd-image"

BUILD_DIR=$(pwd)
FCDAPP_DIR="${BUILD_DIR}/config/includes.chroot"

if [ ! -d ${BUILD_DIR}/fcd-image ]; then \
	echo "${BUILD_DIR}/fcd-image doesn't exist, "; \
	echo "please do, make PRD=UDM -f fcdmaker32.mk gitrepo"; \
	exit 1; \
fi

for arg in "$@"; do
	echo "prepareimg.sh: input: ${arg}"
	echo "prepareimg.sh: dirname: $(dirname ${arg})"
	if [ ! -d ${NEWSQUASHFS}/srv/tftp/$(dirname ${arg}) ]; then \
		mkdir -p ${NEWSQUASHFS}/srv/tftp/$(dirname ${arg}); \
	fi
	cp -rf ${BUILD_DIR}/fcd-image/${arg} ${NEWSQUASHFS}/srv/tftp/$(dirname ${arg}); \
done
