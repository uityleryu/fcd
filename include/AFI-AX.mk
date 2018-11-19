# AFi-AX
IMAGE-AFI-AX-R=images/da11/* \
            images/da11_bootloader.bin \
            images/da11_fw.img

IMAGE-AFI-AX-P=images/da12/*

IMAGE-AFI-AX+=$(IMAGE-AFI-AX-R)
IMAGE-AFI-AX+=$(IMAGE-AFI-AX-P)

DIAG_MODEL=afi_ax_r

UPYFCD_VER=4e5fa351ba4db345567dbb335a35e078dacfd3ca

TOOLS=tools/al324-ee \
      tools/ax_gen_eeprom.py \
      tools/evtest \
      tools/helper_AL324_release \
      tools/helper_IPQ807x_release \
      tools/ipq807x-aarch64-ee \
      tools/dropbear_arm64 \
      tools/dropbearkey_arm64 \
      tools/ubios-udapi-server.default \
      tools/sshd_config

$(eval $(call ProductImage,AFI-AX,FCD-AFI-AX-$(VER)))
$(eval $(call ProductImage,AFI-AX-R,FCD-AFI-AX-R-$(VER)))
$(eval $(call ProductImage,AFI-AX-P,FCD-AFI-AX-P-$(VER)))
