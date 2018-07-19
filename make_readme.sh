#!/bin/bash

OUTDIR=$1

if [ $# -lt 1 ]; then
	OUTDIR='.'
fi

eval $(cat ${OUTDIR}/build.properties)
BUILD_TIME=$(date -d "${build_date} ${build_time}" +%y%m%d_%H%M)
if [ "${scm_dirty}" != "true" ]; then
	SCMVER=${scm_refname}_${scm_distance}
else
	SCMVER=${scm_refname}_${scm_distance}_${build_user}_${build_host}_`date -d "${build_date} ${build_time}" +%y%m%d_%H%M`
fi

FW_PATH="target/edit/tftpboot.src/images"

#get firmware versions
ver_eap=(`strings -n12 $FW_PATH/uap-fw.bin`)
ver_uap16=(`strings -n12 $FW_PATH/uap16-fw.bin`)
ver_pro=(`strings -n12 $FW_PATH/pro-fw.bin`)
ver_ac=(`strings -n12 $FW_PATH/uapac-fw.bin`)
ver_qca933x=(`strings -n12 $FW_PATH/uapinwall-fw.bin`)
ver_usw=(`strings -n12 $FW_PATH/unifiswitch-fw.bin`)
ver_qca956x=(`strings -n12 $FW_PATH/uapgen211ac-fw.bin`)
ver_qca9342=(`strings -n12 $FW_PATH/uap_qca9342-fw.bin`)
ver_uswxg=(`strings -n12 $FW_PATH/unifiswitch-xg-fw.bin`)
ver_ipq806x=(`strings -n12 $FW_PATH/uap_ipq806x-fw.bin`)
ver_usw64m=(`strings -n12 $FW_PATH/unifiswitch-us48p-64m-fw.bin`)
ver_usw6xg150_64m=(`strings -n12 $FW_PATH/unifiswitch-6xg150-fw.bin`)
ver_usc8=(`strings -n12 $FW_PATH/unifiswitch-usc8-fw.bin`)

#strip "UBNT" from begining
ver_eap=${ver_eap#UBNT}
ver_uap16=${ver_uap16#UBNT}
ver_pro=${ver_pro#UBNT}
ver_ac=${ver_ac#UBNT}
ver_qca933x=${ver_qca933x#UBNT}
ver_usw=${ver_usw#UBNT}
ver_qca956x=${ver_qca956x#UBNT}
ver_qca9342=${ver_qca9342#UBNT}
ver_uswxg=${ver_uswxg#UBNT}
ver_ipq806x=${ver_ipq806x#UBNT}
ver_usw64m=${ver_usw64m#UBNT}
ver_usw6xg150_64m=${ver_usw6xg150_64m#UBNT}
ver_usc8=${ver_usc8#UBNT}

declare -a ARTS
art_count=0

for i in $FW_PATH/*ART*.bin; do
	ver=(`strings -n12 $i`)
    typeset v x
    v=${i##*/}
	x=${i#.} # get rid of the '.'
	v=${v%.$x}
	ARTS[$art_count]="\t"$v"\t- "${ver#UBNT}"\n"
		((art_count++))
done

declare -a CH_LOG
#Open file for reading to array
exec 10<changes.txt
count=0

while read LINE <&10; do
    CH_LOG[$count]="    -"$LINE
	    ((count++))
done

text1="================================================================================
UAP Factory CD ${SCMVER} (${build_date} ${build_time})
================================================================================

Changelog:"

text2="
UniFi-AP/UniFi-Switch firmwares:
    -$ver_eap for 8MB
	Supported hardware:
		UAP-Outdoor5G
    -$ver_pro for 16MB
	Supported hardware:
		UAP-Pro
    -$ver_qca933x for 8MB
	Supported hardware:
		UAP-InWall
    -$ver_qca956x for 16MB
	Support hardware:
		UAP-AC-LR
		UAP-AC-Lite
		UAP-AC-Pro
		UAP-AC-EDU
		UAP-AC-Mesh
		UAP-AC-Mesh-Pro
 		UAP-AC-InWall
		UAP-AC-InWall-Pro
    -$ver_qca9342 for 8MB
	Supported hardware:
		UAPv2
		UAP-LRv2
    -$ver_ipq806x for 32MB
	Supported hardware:
		UAP-AC-HD
		UAP-AC-SHD
		UAP-AC-XG
		UAP-XG-MESH
		UAP-XG-STADIUM
    -$ver_usw for 32MB
	Support hardware:
		USW-8
		USW-8-60w
		USW-8-150w
		USW-16-150w
		USW-24
		USW-24-250w
		USW-24-500w
		USW-48
		USW-48-500w
		USW-48-750w
    -$ver_usw64m for 64MB
	Support hardware:
		USW-24P-L2
		USW-48P-L2
    -$ver_uswxg for 64MB
	Support hardware:
		USW-XG
    -$ver_usw6xg150_64m for 64MB
	Support hardware:
		USW-6XG-150
    -$ver_usc8
	Support hardware:
		US-USC8

Back to ART utility:
${ARTS[@]}"

#output log to file
echo -e "$text1" > ${OUTDIR}/README.README
for (( i = 0 ; i < ${#CH_LOG[@]} ; i++ ))
do
echo -e "${CH_LOG[$i]}" >> ${OUTDIR}/README.README
done
echo -e "$text2" >> ${OUTDIR}/README.README


