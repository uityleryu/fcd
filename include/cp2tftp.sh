#!/bins/sh

# For build environmental variables
OUTDIR=$(pwd)/output
APP_DIR="usr/local/sbin"
EXLIVECD="${OUTDIR}/ExtractLivedCD"
EXSQUASHFS="${OUTDIR}/ExtractLivedSquashfs"
STAGEDIR="${OUTDIR}/stage"
NEWLIVEDCD="${STAGEDIR}/NewLiveCD"
NEWSQUASHFS="${STAGEDIR}/NewSquashfs"

BUILD_DIR=$(pwd)
FCDAPP_DIR="${BUILD_DIR}/config/includes.chroot"

for arg in "$@"; do
	echo "prepareimg.sh: input: ${arg}"
	echo "prepareimg.sh: dirname: $(dirname ${arg})"
	if [ ! -d ${NEWSQUASHFS}/srv/tftp/$(dirname ${arg}) ]; then \
		mkdir -p ${NEWSQUASHFS}/srv/tftp/$(dirname ${arg}); \
	fi
	cp -rf ${STAGEDIR}/fcd-image/${arg} ${NEWSQUASHFS}/srv/tftp/$(dirname ${arg}); \
done