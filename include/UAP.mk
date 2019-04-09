IMAGE-UAP-FLEX= \
    images/ec26* \
    uap-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    uap-fw/BZ.mt7621.*

IMAGE-UAP+=$(IMAGE-UAP-FLEX)

DIAG_MODEL=UniFiAP
DIAG_UI_MODEL=UniFiAP
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

UPYFCD_VER=
FCDIMG_VER=
UBNTLIB_VER=
TOOL_VER=

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf

TOOLS-UAP+=$(TOOLS-CONFIG)

TOOLS-UAP-FLEXHD=$(TOOLS-USW)

$(eval $(call ProductImage,UAP,FCD-UAP-$(VER)))
$(eval $(call ProductImage,UAP-FLEXHD,FCD-UAP-FLEXHD-$(VER)))
