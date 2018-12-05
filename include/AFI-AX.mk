# AFi-AX
IMAGE-AFI-AX-R=images/da11* \
               afi-fw/*

IMAGE-AFI-AX-P=images/da12* \
               afi-fw/*

IMAGE-AFI-AX+=$(IMAGE-AFI-AX-R)
IMAGE-AFI-AX+=$(IMAGE-AFI-AX-P)

DIAG_MODEL=afi_ax_r

UPYFCD_VER=4956696e8902c84db6d2b0b69eda60a0ef9da942
FCDIMG_VER=c12758b1fdfbb0c07c33a0c21efd0a01bd19f445

TOOLS=tools/al324-ee \
      tools/ax_gen_eeprom.py \
      tools/evtest \
      tools/helper_AL324_release \
      tools/helper_IPQ807x_release \
      tools/ipq807x-aarch64-ee \
      tools/dropbear_arm64 \
      tools/dropbearkey_arm64 \
      tools/ubios-udapi-server.default \
      tools/sshd_config \
      tools/stop_daemons.sh \
      tools/DUT_wireless \

$(eval $(call ProductImage,AFI-AX,FCD-AFI-AX-$(VER)))
$(eval $(call ProductImage,AFI-AX-R,FCD-AFI-AX-R-$(VER)))
$(eval $(call ProductImage,AFI-AX-P,FCD-AFI-AX-P-$(VER)))
