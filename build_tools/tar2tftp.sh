#!/bin/bash
################################################################################
#Description    : To create tool.tar which contains the prodcut specific tool
#                 stuffs from fcd-script-tools repo
#Revision       : 1.0.0
################################################################################
# For build environmental variables
BUILD_DIR=$(pwd)
OUTDIR="${BUILD_DIR}/output"
OSTRICH_DIR="${OUTDIR}/ostrich"
STAGEDIR="${OUTDIR}/stage"
NEWSQUASHFS="${STAGEDIR}/NewSquashfs"

if [ ! -d ${BUILD_DIR}/fcd-script-tools/tools ]; then \
	echo "${BUILD_DIR}/fcd-script-tools/tools doesn't exist, "; \
	echo "please do, make PRD=UDM -f fcdmaker32.mk gitrepo"; \
	exit 1; \
fi

arr_opts=($@ "${arr_opts[@]}")
case ${arr_opts[0]} in
	iso)
		if [ ! -d ${NEWSQUASHFS}/srv/tftp/tools ]; then \
			mkdir -p ${NEWSQUASHFS}/srv/tftp/tools; \
		fi

		cd ${BUILD_DIR}/fcd-script-tools/tools
		tar -cvzf tools.tar ${arr_opts[@]:1}; chmod 777 tools.tar
		mv ${BUILD_DIR}/fcd-script-tools/tools/tools.tar ${NEWSQUASHFS}/srv/tftp/tools/tools.tar
		;;
	ostrich)
		echo "Starting packing tools for raspbian"
		if [ ! -d ${OSTRICH_DIR}/tftp/tools ]; then \
			mkdir -p ${OSTRICH_DIR}/tftp/tools; \
		fi
		cd ${BUILD_DIR}/fcd-script-tools/tools
		tar -cvzf tools.tar ${arr_opts[@]:1}; chmod 777 tools.tar
		mv ${BUILD_DIR}/fcd-script-tools/tools/tools.tar ${OSTRICH_DIR}/tftp/tools/tools.tar
		;;
	*)
		echo "Not support!!!"
		exit 1
		;;
esac
