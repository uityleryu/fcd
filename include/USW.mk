# AFi-AX
IMAGE-USW-24=images/eb36* \
             images/eb67* \
             usw-fw/unifiswitch-us* \
             usw-fw/US.bcm5616x.feature-usw-pro-dev.*

IMAGE-USW-6XG=images/eb23* \
              usw-fw/unifiswitch-6xg150-* \
              usw-fw/US.bcm5616x.*

IMAGE-USW-FLEX=images/ed10* \
               usw-fw/unifiswitch-usflex-* \
               usw-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
               usw-fw/unifi-v1.0.9.57-gd7bab423_uap-mt7621-32MB_u-boot.bin \
               usw-fw/US.mt7621.*

IMAGE-USW+=$(IMAGE-USW-24)
IMAGE-USW+=$(IMAGE-USW-6XG)
IMAGE-USW+=$(IMAGE-USW-FLEX)

DIAG_MODEL=us_flex

UPYFCD_VER=41733951b067164a84d411796b00b278d8f90dd1

TOOLS=.tmux.conf \
      sshd_config

$(eval $(call ProductImage,USW,FCD-USW-$(VER)))
$(eval $(call ProductImage,USW-6XG,FCD-USW-6XG-$(VER)))
$(eval $(call ProductImage,USW-24,FCD-USW-24-$(VER)))
$(eval $(call ProductImage,USW-FLEX,FCD-USW-FLEX-$(VER)))
