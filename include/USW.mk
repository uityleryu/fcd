
# Images

IMAGE-USW-PRO= \
    images/eb36* \
    images/eb37* \
    images/eb67* \
    images/eb68* \
    usw-fw/unifiswitch-us24pro* \
    usw-fw/unifiswitch-us48pro* \
    usw-fw/US.bcm5616x.*

IMAGE-USW-6XG= \
    images/eb23* \
    usw-fw/unifiswitch-6xg150-* \
    usw-fw/US.bcm5616x.*

IMAGE-USW-FLEX= \
    images/ed10* \
    usw-fw/unifiswitch-usflex-* \
    usw-fw/unifiswitch-mt7621-* \
    usw-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    usw-fw/MFG.us-flex.BL_gd9df1cea.UAP_4be38fd.image \
    usw-fw/US.mt7621.*

IMAGE-ULS-RPS= \
    images/ed11* \
    usw-fw/unifiswitch-ulsrps-* \
    usw-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    usw-fw/unifi-v1.1.2.71-gd9df1cea_usw-mt7621-16MB_u-boot.bin \
    usw-fw/US.mt7621.*

IMAGE-USW-16-24-48= \
    images/ed20* \
    images/ed21* \
    images/ed22* \
    images/ed23* \
    images/ed24* \
    images/ed25* \
    usw-fw/unifiswitch-16-* \
    usw-fw/unifiswitch-24-* \
    usw-fw/unifiswitch-48-* \
    usw-fw/unifiswitch-16poe-* \
    usw-fw/unifiswitch-24poe-* \
    usw-fw/unifiswitch-48poe-* \
    usw-fw/US.rtl838x.*

IMAGE-USW-LITE= \
    images/ed26* \
    images/ed2a* \
    usw-fw/unifiswitch-lite-16poe-* \
    usw-fw/unifiswitch-lite-8poe-* \
    usw-fw/unifiswitch-16poe-* \
    usw-fw/US.rtl838x.*

IMAGE-USW-LEAF= \
    images/f060* \
    usw-fw/fw.LEAF* \
    usw-fw/fw.UDC*

IMAGE-USW-SPINE= \
    images/f062* \
    usw-fw/fw.SPINE* \
    usw-fw/fw.UDC* \
    usw-fw/bsp.*

IMAGE-USW-FLEX-MINI= \
    images/ed30* \
    usw-fw/unifiswitch-mini-* \
    usw-fw/US.m487.*

IMAGE-USW-XG= \
    images/eb25* \
    images/eb26* \
    images/eb27* \
    usw-fw/unifiswitch-xg24poe* \
    usw-fw/unifiswitch-xg48poe* \
    usw-fw/unifiswitch-xgagg* \
    usw-fw/US.bcm5617x*

IMAGE-USW+=$(IMAGE-USW-PRO)
IMAGE-USW+=$(IMAGE-USW-6XG)
IMAGE-USW+=$(IMAGE-USW-FLEX)
IMAGE-USW+=$(IMAGE-ULS-RPS)
IMAGE-USW+=$(IMAGE-USW-16-24-48)
IMAGE-USW+=$(IMAGE-USW-LITE)
IMAGE-USW+=$(IMAGE-USW-LEAF)
IMAGE-USW+=$(IMAGE-USW-SPINE)
IMAGE-USW+=$(IMAGE-USW-FLEX-MINI)
IMAGE-USW+=$(IMAGE-USW-XG)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiSwitch
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# FCD images repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-image.git

USW-PRO_FCDIMG_HASH=
USW-6XG_FCDIMG_HASH=
USW-FLEX_FCDIMG_HASH=
ULS-RPS_FCDIMG_HASH=
USW-16-24-48_FCDIMG_HASH=
USW-LITE_FCDIMG_HASH=
USW-LEAF_FCDIMG_HASH=84778307319c8093f456fb1f1d427d273bba4809
USW-SPINE_FCDIMG_HASH=
USW-FLEX-MINI_FCDIMG_HASH=
USW-XG_FCDIMG_HASH=

FCDIMG_VER=

# UBNTLIB repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-ubntlib.git

USW-PRO_UBNTLIB_HASH=
USW-6XG_UBNTLIB_HASH=
USW-FLEX_UBNTLIB_HASH=
ULS-RPS_UBNTLIB_HASH=
USW-16-24-48_UBNTLIB_HASH=
USW-LITE_UBNTLIB_HASH=
USW-LEAF_UBNTLIB_HASH=11b2602e7d213ec31bd0eeda477d60547f7f16a7
USW-SPINE_UBNTLIB_HASH=
USW-FLEX-MINI_UBNTLIB_HASH=
USW-XG_UBNTLIB_HASH=

UBNTLIB_VER=

# TOOL repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-tools.git

USW-PRO_TOOL_HASH=
USW-6XG_TOOL_HASH=
USW-FLEX_TOOL_HASH=
ULS-RPS_TOOL_HASH=
USW-16-24-48_TOOL_HASH=
USW-LITE_TOOL_HASH=
USW-LEAF_TOOL_HASH=8750be65f9e051345fc81b402605a8d41e318fda
USW-SPINE_TOOL_HASH=
USW-FLEX-MINI_TOOL_HASH=
USW-XG_TOOL_HASH=

TOOL_VER=

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/helper_UNIFI_MT7621_release

# Project specific tools

TOOLS-USW+=$(TOOLS-CONFIG)

TOOLS-USW-16-24-48+=$(TOOLS-USW)
TOOLS-USW-16-24-48+= \
    usw_rtl838x/helper_rtl838x \
    usw_rtl838x/rtl838x-ee

TOOLS-USW-LITE+=$(TOOLS-USW)
TOOLS-USW-LITE+= \
    usw_rtl838x/helper_rtl838x \
    usw_rtl838x/rtl838x-ee

TOOLS-USW-LEAF=$(TOOLS-USW)
TOOLS-USW-LEAF+= \
    usw_leaf/create_preload.sh \
    usw_leaf/decrypt.pyc \
    usw_leaf/fake-leaf.bin \
    usw_leaf/fake-spine.bin \
    usw_leaf/fwdiag-ssd.sh \
    usw_leaf/helper_AL324_release_udc \
    usw_leaf/__init__.py \
    usw_leaf/uswleaf-decrypt \

TOOLS-USW-SPINE=$(TOOLS-USW)
# the tools for the USW-SPINE are almost identical to the USW-LEAF
TOOLS-USW-SPINE+=$(TOOLS-USW-LEAF)

TOOLS-USW-6XG=$(TOOLS-USW)
TOOLS-USW-PRO=$(TOOLS-USW)
TOOLS-USW-FLEX=$(TOOLS-USW)
TOOLS-ULS-RPS=$(TOOLS-USW)
TOOLS-ULS-RPS+= \
    uls_rps/burnin.sh \
    uls_rps/burnin.cfg \
    uls_rps/system.cfg.burnin \
    uls_rps/ubidiag \
    uls_rps/uls_get_power_status_fcd.sh \
    uls_rps/uls_power.sh

TOOLS-USW-FLEX-MINI=$(TOOLS-USW)
TOOLS-USW-FLEX-MINI+= \
    usw_mini/x86-4k-ee

TOOLS-USW-XG=$(TOOLS-USW)
# Project target

$(eval $(call ProductImage,USW,FCD-USW-$(VER)))
$(eval $(call ProductImage,USW-6XG,FCD-USW-6XG-$(VER)))
$(eval $(call ProductImage,USW-PRO,FCD-USW-PRO-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USW-FLEX,FCD-USW-FLEX-$(VER)-$(FWVER)))
$(eval $(call ProductImage,ULS-RPS,FCD-ULS-RPS-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USW-16-24-48,FCD-USW-16-24-48-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USW-LITE,FCD-USW-LITE-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USW-LEAF,FCD-USW-LEAF-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USW-SPINE,FCD-USW-SPINE-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USW-FLEX-MINI,FCD-USW-FLEX-MINI-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USW-XG,FCD-USW-XG-$(VER)-$(FWVER)))
