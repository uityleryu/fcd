#!/bin/bash

SRC_DIR=target/edit/usr/local/sbin/products
DST_FILE=target/edit/usr/local/sbin/products.txt.km

rm -f ${DST_FILE}

CURRENT=1
for MODEL in `ls ${SRC_DIR} | sort`; do
	while IFS= read line
	do
		echo "product.${CURRENT}.${line}" >> ${DST_FILE}
	done <${SRC_DIR}/${MODEL}
	CURRENT=`expr ${CURRENT} + 1`
done

