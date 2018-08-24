#!/bin/bash

CURDIR=$(pwd)
SRC_DIR=${CURDIR}/config/includes.chroot/usr/local/sbin/products
DST_FILE=${CURDIR}/config/includes.chroot/usr/local/sbin/products.txt.km

rm -f ${DST_FILE}

CURRENT=1
for MODEL in `ls ${SRC_DIR} | sort`; do
	while IFS= read line
	do
		echo "product.${CURRENT}.${line}" >> ${DST_FILE}
	done <${SRC_DIR}/${MODEL}
	CURRENT=`expr ${CURRENT} + 1`
done

