
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

IMAGE-USW-16-24= \
    images/ed20* \
    images/ed21* \
    images/ed23* \
    images/ed24* \
    usw-fw/unifiswitch-16-* \
    usw-fw/unifiswitch-24-* \
    usw-fw/unifiswitch-16poe-* \
    usw-fw/unifiswitch-24poe-* \
    usw-fw/US.rtl838x.*

IMAGE-USW-48= \
    images/ed22* \
    usw-fw/unifiswitch-48poe-* \
    usw-fw/US.rtl838x.pcb*

IMAGE-USW-LEAF= \
    images/f060* \
    usw-fw/fw.UDC*

IMAGE-USW-MINI= \
    images/ed30* \
    usw-fw/unifiswitch-mini-* \
    usw-fw/US.m487.*

IMAGE-USW+=$(IMAGE-USW-PRO)
IMAGE-USW+=$(IMAGE-USW-6XG)
IMAGE-USW+=$(IMAGE-USW-FLEX)
IMAGE-USW+=$(IMAGE-ULS-RPS)
IMAGE-USW+=$(IMAGE-USW-16-24)
IMAGE-USW+=$(IMAGE-USW-LEAF)
IMAGE-USW+=$(IMAGE-USW-MINI)

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
USW-16-24_FCDIMG_HASH=
USW-48_FCDIMG_HASH=
USW-LEAF_FCDIMG_HASH=
USW-MINI_FCDIMG_HASH=

FCDIMG_VER=

# UBNTLIB repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-ubntlib.git

USW-PRO_UBNTLIB_HASH=
USW-6XG_UBNTLIB_HASH=
USW-FLEX_UBNTLIB_HASH=
ULS-RPS_UBNTLIB_HASH=
USW-16-24_UBNTLIB_HASH=
USW-48_UBNTLIB_HASH=
USW-LEAF_UBNTLIB_HASH=
USW-MINI_UBNTLIB_HASH=

UBNTLIB_VER=

# TOOL repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-tools.git

USW-PRO_TOOL_HASH=
USW-6XG_TOOL_HASH=
USW-FLEX_TOOL_HASH=
ULS-RPS_TOOL_HASH=
USW-16-24_TOOL_HASH=
USW-48_TOOL_HASH=
USW-LEAF_TOOL_HASH=
USW-MINI_TOOL_HASH=

TOOL_VER=

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/helper_UNIFI_MT7621_release

# Project specific tools

TOOLS-USW+=$(TOOLS-CONFIG)

TOOLS-USW-16-24+=$(TOOLS-USW)
TOOLS-USW-16-24+= \
    usw_rtl838x/helper_rtl838x \
    usw_rtl838x/rtl838x-ee

TOOLS-USW-48+=$(TOOLS-USW)
TOOLS-USW-48+= \
    usw_rtl838x/helper_rtl838x \
    usw_rtl838x/rtl838x-ee

TOOLS-USW-LEAF=$(TOOLS-USW)
TOOLS-USW-LEAF+= \
    usw_leaf/*

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

TOOLS-USW-MINI=$(TOOLS-USW)
TOOLS-USW-MINI+= \
    usw_mini/x86-4k-ee

# Project target

$(eval $(call ProductImage,USW,FCD-USW-$(VER)))
$(eval $(call ProductImage,USW-6XG,FCD-USW-6XG-$(VER)))
$(eval $(call ProductImage,USW-PRO,FCD-USW-PRO-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USW-FLEX,FCD-USW-FLEX-$(VER)-$(FWVER)))
$(eval $(call ProductImage,ULS-RPS,FCD-ULS-RPS-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USW-16-24,FCD-USW-16-24-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USW-48,FCD-USW-48-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USW-LEAF,FCD-USW-LEAF-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USW-MINI,FCD-USW-MINI-$(VER)-$(FWVER)))
