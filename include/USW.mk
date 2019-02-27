
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

IMAGE-ULS-RPS=images/ed11* \
               usw-fw/unifiswitch-ulsrps-* \
               usw-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin 

IMAGE-USW+=$(IMAGE-USW-24)
IMAGE-USW+=$(IMAGE-USW-6XG)
IMAGE-USW+=$(IMAGE-USW-FLEX)
IMAGE-USW+=$(IMAGE-ULS-RPS)

DIAG_MODEL=us_flex
DIAG_UI_MODEL=Unifi-Switch
UPYFCD_VER=577583e552ddde895ce97cd73c8c16ef309d8e8b
FCDIMG_VER=662f044e77de6bde13b3b5064a1d93b9ad6e193c
UBNTLIB_VER=28999e4934c068d2c43470a34707072529485f45
TOOL_VER=bcacb75ec7305ef40068e739383c04c27074cb59
TOOLS-USW=.tmux.conf \
      sshd_config

TOOLS-USW-6XG=$(TOOLS-USW)
TOOLS-USW-24=$(TOOLS-USW)
TOOLS-USW-FLEX=$(TOOLS-USW)
TOOLS-ULS-RPS=$(TOOLS-USW)

$(eval $(call ProductImage,USW,FCD-USW-$(VER)))
$(eval $(call ProductImage,USW-6XG,FCD-USW-6XG-$(VER)))
$(eval $(call ProductImage,USW-24,FCD-USW-24-$(VER)))
$(eval $(call ProductImage,USW-FLEX,FCD-USW-FLEX-$(VER)))
$(eval $(call ProductImage,ULS-RPS,FCD-ULS-RPS-$(VER)))
