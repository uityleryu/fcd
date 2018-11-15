# AFi-AX
IMAGE=images/da11/* \
          images/da12/*

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
      tools/ubios-udapi-server.default

# Amplifi product line
AFI-PRODUCT-LINE=""
$(eval $(call ProductImage,AFI,FCD-Amplifi-$(VER),afi_ax_r))