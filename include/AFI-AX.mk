# AFi-AX
IMAGE-AFI-AX-R=images/da11* \
               afi-fw/*

IMAGE-AFI-AX-P=images/da12* \
               afi-fw/*

IMAGE-AFI-AX+=$(IMAGE-AFI-AX-R)
IMAGE-AFI-AX+=$(IMAGE-AFI-AX-P)

DIAG_MODEL=afi_ax_r

UPYFCD_VER=4416bf52c96e2ba0977e4a9858ac3aab4f9a53eb
FCDIMG_VER=

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
      tools/golden_ax_dev.sh \
      tools/Golden_wireless \
      tools/as.txt \

$(eval $(call ProductImage,AFI-AX,FCD-AFI-AX-$(VER)))
$(eval $(call ProductImage,AFI-AX-R,FCD-AFI-AX-R-$(VER)))
$(eval $(call ProductImage,AFI-AX-P,FCD-AFI-AX-P-$(VER)))
