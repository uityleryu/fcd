#!/bin/sh
################################################################################
#Description    : To create tool.tar which contains the prodcut specific tool 
#                 stuffs from fcd-script-tools repo
#Revision       : 1.0.0
################################################################################
# For build environmental variables
BUILD_DIR=$(pwd)
OUTDIR="${BUILD_DIR}/output"
STAGEDIR="${OUTDIR}/stage"
NEWSQUASHFS="${STAGEDIR}/NewSquashfs"

if [ ! -d ${BUILD_DIR}/fcd-script-tools/tools ]; then \
	echo "${BUILD_DIR}/fcd-script-tools/tools doesn't exist, "; \
	echo "please do, make PRD=UDM -f fcdmaker32.mk gitrepo"; \
	exit 1; \
fi

if [ ! -d ${NEWSQUASHFS}/srv/tftp/tools ]; then \
	mkdir -p ${NEWSQUASHFS}/srv/tftp/tools; \
fi

cd ${BUILD_DIR}/fcd-script-tools/tools
tar -cvzf tools.tar $@; chmod 777 tools.tar
mv ${BUILD_DIR}/fcd-script-tools/tools/tools.tar ${NEWSQUASHFS}/srv/tftp/tools/tools.tar
