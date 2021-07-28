#!/bin/bash
################################################################################
#Description    : To copy the product specific images from fcd-image repo
#
#Revision       : 1.0.0
################################################################################
# For build environmental variables
BUILD_DIR=$(pwd)
OUTDIR="${BUILD_DIR}/output"
OSTRICH_DIR="${OUTDIR}/ostrich"
STAGEDIR="${OUTDIR}/stage"
NEWSQUASHFS="${STAGEDIR}/NewSquashfs"

if [ ! -d ${BUILD_DIR}/fcd-image ]; then \
	echo "${BUILD_DIR}/fcd-image doesn't exist, "; \
	echo "please do, make PRD=UDM -f fcdmaker32.mk gitrepo"; \
	exit 1; \
fi

arr_opts=($@ "${arr_opts[@]}")
case ${arr_opts[0]} in
	iso)
		echo "Starting packing images for live CD"
		for arg in "${arr_opts[@]:1}"; do
			echo "prepareimg.sh: input: ${arg}"
			echo "prepareimg.sh: dirname: $(dirname ${arg})"
			if [ ! -d ${NEWSQUASHFS}/srv/tftp/$(dirname ${arg}) ]; then \
				mkdir -p ${NEWSQUASHFS}/srv/tftp/$(dirname ${arg}); \
			fi
			cp -rf ${BUILD_DIR}/fcd-image/${arg} ${NEWSQUASHFS}/srv/tftp/$(dirname ${arg}); \
		done
		;;
	ostrich)
		echo "Starting packing images for raspbian"
		for arg in "${arr_opts[@]:1}"; do
			echo "prepareimg.sh: input: ${arg}"
			echo "prepareimg.sh: dirname: $(dirname ${arg})"
			if [ ! -d ${OSTRICH_DIR}/tftp/$(dirname ${arg}) ]; then \
				mkdir -p ${OSTRICH_DIR}/tftp/$(dirname ${arg}); \
			fi
			cp -rf ${BUILD_DIR}/fcd-image/${arg} ${OSTRICH_DIR}/tftp/$(dirname ${arg}); \
		done
		;;
	*)
		echo "Not support!!!"
		exit 1
		;;
esac