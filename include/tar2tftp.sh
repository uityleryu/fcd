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
FTU_DIR="${BUILD_DIR}/DIAG"

BUILD_DIR=$(pwd)
FCDAPP_DIR="${BUILD_DIR}/config/includes.chroot"
PACK_FILES=""

if [ ! -d ${BUILD_DIR}/fcd-image ]; then \
	echo "${BUILD_DIR}/fcd-image doesn't exist, "; \
	echo "please do, make PRD=UDM -f fcdmaker32.mk gitrepo"; \
	exit 1; \
fi

if [ ! -d ${NEWSQUASHFS}/srv/tftp/tools ]; then \
	mkdir -p ${NEWSQUASHFS}/srv/tftp/tools; \
fi

if [ ! -d ${BUILD_DIR}/fcd-image/tools/tmp ]; then \
	mkdir -p ${BUILD_DIR}/fcd-image/tools/tmp; \
else \
	rm -rf ${BUILD_DIR}/fcd-image/tools/tmp/*; \
fi

for arg in "$@"; do
	cd ${BUILD_DIR}/fcd-image/tools; \
	cp -rf $arg ${BUILD_DIR}/fcd-image/tools/tmp; \
done

cd ${BUILD_DIR}/fcd-image/tools/tmp; tar -cvzf tools.tar * .; chmod 777 tools.tar
cp -rf ${BUILD_DIR}/fcd-image/tools/tmp/tools.tar ${NEWSQUASHFS}/srv/tftp/tools
