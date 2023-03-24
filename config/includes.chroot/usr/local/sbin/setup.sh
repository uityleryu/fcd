#!/bin/sh

BASEDIR="/home/ubnt"
OSTRDIR="${BASEDIR}/ostrich"

if [ -d ${OSTRDIR} ]; then
    rm -rf ${OSTRDIR}
fi

if [ -f ${BASEDIR}/$1 ]; then
    tar -xvzf ${BASEDIR}/$1 -C ${BASEDIR}
else
    echo "There is no any tgz file"
    exit 1
fi  

sudo rm -rfv /tftpboot/*
sudo rm -rfv /usr/local/sbin/*
if [ -f ${BASEDIR}/version.txt ]; then
    sudo rm -rfv ${BASEDIR}/version.txt
fi

# sudo cp -rfv ${BASEDIR}/ostrich/tftp/* /tftpboot/
sudo cp -rfv ${BASEDIR}/ostrich/sbin/* /usr/local/sbin
sudo cp -rfv ${BASEDIR}/ostrich/version.txt ${BASEDIR}/version.txt
cd /tftpboot/tools; sudo tar -xvzf /tftpboot/tools/tools.tar

sudo rm -rfv ${BASEDIR}/$1
sudo rm -rfv ${BASEDIR}/ostrich
