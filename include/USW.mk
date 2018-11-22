# AFi-AX
IMAGE-USW-24=images/eb36* \
             images/eb67* \
             usw-fw/unifiswitch-us* \
             usw-fw/US.bcm5616x.feature-usw-pro-dev.*

IMAGE-USW-6XG=images/eb23* \
              usw-fw/unifiswitch-6xg150-* \
              usw-fw/US.bcm5616x.*

IMAGE-USW+=$(IMAGE-USW-24)
IMAGE-USW+=$(IMAGE-USW-6XG)

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

$(eval $(call ProductImage,USW,FCD-USW-$(VER)))
$(eval $(call ProductImage,USW-6XG,FCD-USW-6XG-$(VER)))
$(eval $(call ProductImage,USW-24,FCD-USW-24-$(VER)))
