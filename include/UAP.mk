IMAGE-UAP-FLEX= \
    images/ec26* \
    uap-fw/unifiap-mt7621* \
    uap-fw/V8-unifi-v1.0.1.43-g12f846ff_uap-mt7621-32MB_u-boot.bin \
    uap-fw/V9-uImage_5030-TXBF_enabled-20171101.dms \
    uap-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    uap-fw/BZ.mt7621.*

IMAGE-UBB= \
    images/dc98* \
    uap-fw/UBB.v0.9.10.40735.190503.1747.bin \
    uap-fw/ubntubb-u-boot.rom


IMAGE-UAP+=$(IMAGE-UAP-FLEX)
IMAGE-UAP+=$(IMAGE-UBB)

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

TOOLS-UBB+= \
    uap/cfg_part.bin \
    uap/helper_IPQ40xx \
    uap/id_rsa \
    uap/id_rsa.pub \
    uap/x86-4k-ee

TOOLS-UBB+=$(TOOLS-CONFIG)
TOOLS-UAP+=$(TOOLS-UBB)


$(eval $(call ProductImage,UAP,FCD-UAP-$(VER)))
$(eval $(call ProductImage,UAP-FLEXHD,FCD-UAP-FLEXHD-$(VER)))
$(eval $(call ProductImage,UBB,FCD-UBB-$(VER)))
