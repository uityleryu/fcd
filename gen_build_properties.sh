#!/bin/bash

#set -x

HERE=`dirname $0`
HERE=`cd ${HERE};pwd`
BASEDIR=${HERE}
#OUTFILE=${BASEDIR}/build.properties

OUTFILE=$1
BRANCH=$2

outtofile ()
{
	FILENAME=$1

	cat > ${FILENAME} << EOF
scm_reftype=${SCM_REFTYPE}
scm_refname=${SCM_REFNAME}
scm_distance=${SCM_DISTANCE}
scm_hash=${SCM_HASH}
scm_dirty=${SCM_DIRTY}
build_date=${BUILD_DATE}
build_time=${BUILD_TIME}
build_user=${BUILD_USER}
build_host=${BUILD_HOST}
build_num=${BUILD_NUM}
EOF
}

if [ -e "$OUTFILE" ]; then
	source "$OUTFILE"
fi

pushd ${BASEDIR} > /dev/null
	BASE=BEGIN_BUILD
	BUILD_USER=$(whoami)
	BUILD_HOST=$(hostname)
	BUILD_DATE=$(date +%F)
	BUILD_TIME=$(date +%T)
	BUILD_NUM=${build_num:-0}
	BUILD_NUM=$((BUILD_NUM+1))
	GITDESCRIBE=$(git describe 2>/dev/null)
	DISTANCE=$(expr "${GITDESCRIBE}" : '.*-\([0-9]*\)-g.*')
	SHORTHASH=$(expr "${GITDESCRIBE}" : '.*-[0-9]*-g\([0-9a-f]*\).*')
	DIRTY=$(git diff --exit-code --ignore-submodules=all >/dev/null 2>&1 || echo dirty)
	LONGHASH=$(git rev-parse HEAD)
	
	SCM_HASH=${LONGHASH}

	# curent revision is an ATAG
	if [ "${BRANCH}" == "" -a "${GITDESCRIBE}" != "" -a "${DISTANCE}" == "" -a "${SHORTHASH}" == "" -a "${DIRTY}" == "" ]; then
		SCM_REFTYPE=atag
		TMP_REFNAME=$(echo ${GITDESCRIBE} | awk -F'-' '{print $1}')
		case ${TMP_REFNAME} in
		[0-9]*)
			SCM_REFNAME=$(echo v${TMP_REFNAME})
			;;
		*)
			SCM_REFNAME=${TMP_REFNAME}
			;;
		esac
		SCM_DISTANCE=$(expr "$(git describe --tags --match ${BASE})" : '.*-\([0-9]*\)-g.*')
		SCM_DIRTY=false
		outtofile ${OUTFILE}
		exit 0
	fi

	if [ "${BRANCH}" == "" ]; then 
		BRANCH=$(git branch | awk '/^\* /{print}' | sed 's,^\* ,,g')
	fi

	if [ "${BRANCH}" == "(no branch)" ]; then
		SCM_REFTYPE=unknown
		SCM_REFNAME=unknown
		SCM_DISTANCE=0
		if [ "${DIRTY}" == "" ]; then
			SCM_DIRTY=false
		else
			SCM_DIRTY=true
		fi
		outtofile ${OUTFILE}
		exit 0
	fi

	GITDESCRIBE=$(git describe --tags --match "${BASE}")
	DISTANCE=$(expr "${GITDESCRIBE}" : '.*-\([0-9]*\)-g.*')
	SHORTHASH=$(expr "${GITDESCRIBE}" : '.*-[0-9]*-g\([0-9a-f]*\).*')

	SCM_REFTYPE=branch
	SCM_REFNAME=${BRANCH}

	if [ "${GITDESCRIBE}" != "" ]; then
		# current revision is on a branch we are tracking
		if [ "${DISTANCE}" == "" -a "${SHORTHASH}" == "" ]; then
			SCM_DISTANCE=0
		else
			SCM_DISTANCE=${DISTANCE}
		fi
	else
		# current revision is on a branch we are not tracking
		SCM_DISTANCE=-1
	fi

	if [ "${DIRTY}" == "" ]; then
		SCM_DIRTY=false
	else
		SCM_DIRTY=true
	fi
	if [ "$SCM_DISTANCE" = -1 ]; then
		SCM_DISTANCE=-1.$BUILD_NUM
	fi
	outtofile ${OUTFILE}
		
popd > /dev/null
