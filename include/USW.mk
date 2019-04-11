
IMAGE-USW-24= \
    images/eb36* \
    images/eb67* \
    usw-fw/unifiswitch-us* \
    usw-fw/US.bcm5616x.feature-usw-pro-dev.*

IMAGE-USW-6XG= \
    images/eb23* \
    usw-fw/unifiswitch-6xg150-* \
    usw-fw/US.bcm5616x.*

IMAGE-USW-FLEX= \
    images/ed10* \
    usw-fw/unifiswitch-usflex-* \
    usw-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    usw-fw/unifi-v1.0.9.57-gd7bab423_uap-mt7621-32MB_u-boot.bin \
    usw-fw/US.mt7621.*

IMAGE-ULS-RPS= \
    images/ed11* \
    usw-fw/unifiswitch-ulsrps-* \
    usw-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    usw-fw/US.mt7621.sh-add-uls-rps-rebase-develop.10098.190320.2303-uboot.bin

IMAGE-USW-LITE= \
    images/ed20* \
    images/ed21* \
    usw-fw/US.rtl838x.*

IMAGE-USW-LEAF= \
    images/f060* \
    usw-fw/usw-leaf* \
    usw-fw/udc* \
    usw-fw/UDC*

IMAGE-USW+=$(IMAGE-USW-24)
IMAGE-USW+=$(IMAGE-USW-6XG)
IMAGE-USW+=$(IMAGE-USW-FLEX)
IMAGE-USW+=$(IMAGE-ULS-RPS)
IMAGE-USW+=$(IMAGE-USW-LITE)
IMAGE-USW+=$(IMAGE-USW-LEAF)

DIAG_UI_MODEL=UniFiSwitch
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

UPYFCD_VER =5b6a7681ba673d002e35dc6b70ab4925bd21b475
FCDIMG_VER =3c2312c03b2d7644d4755b0602062481372ebd35
UBNTLIB_VER=671910c29d7dfacfca754ea5aa594ddfabe4310f
TOOL_VER   =70ef4fa14efee327877c387b04e7b67514b978ff

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf

TOOLS-USW+=$(TOOLS-CONFIG)

TOOLS-USW-LITE+=$(TOOLS-USW)
TOOLS-USW-LITE+= \
    usw_lite/helper_rtl838x \
    usw_lite/rtl838x-ee

TOOLS-USW-LEAF+=$(TOOLS-USW)
TOOLS-USW-LEAF+= usw-leaf/*

TOOLS-USW-6XG=$(TOOLS-USW)
TOOLS-USW-24=$(TOOLS-USW)
TOOLS-USW-FLEX=$(TOOLS-USW)
TOOLS-ULS-RPS=$(TOOLS-USW)
TOOLS-ULS-RPS+= \
    uls_rps/burnin.sh \
    uls_rps/burnin.cfg \
    uls_rps/system.cfg.burnin \
    uls_rps/ubidiag \
    uls_rps/uls_get_power_status_fcd.sh \
    uls_rps/uls_power.sh 

$(eval $(call ProductImage,USW,FCD-USW-$(VER)))
$(eval $(call ProductImage,USW-6XG,FCD-USW-6XG-$(VER)))
$(eval $(call ProductImage,USW-24,FCD-USW-24-$(VER)))
$(eval $(call ProductImage,USW-FLEX,FCD-USW-FLEX-$(VER)))
$(eval $(call ProductImage,ULS-RPS,FCD-ULS-RPS-$(VER)))
$(eval $(call ProductImage,USW-LITE,FCD-USW-LITE-$(VER)))
$(eval $(call ProductImage,USW-LEAF,FCD-USW-LEAF-$(VER)))
