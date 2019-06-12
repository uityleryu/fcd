IMAGE-UAP-FLEX= \
    images/ec26* \
    uap-fw/unifiap-mt7621* \
    uap-fw/V8-unifi-v1.0.1.43-g12f846ff_uap-mt7621-32MB_u-boot.bin \
    uap-fw/V9-uImage_5030-TXBF_enabled-20171101.dms \
    uap-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    uap-fw/BZ.mt7621.*

IMAGE-UBB= \
    images/dc98* \
    uap-fw/UBB.* \
    uap-fw/ubntubb-u-boot.rom

IMAGE-UAP-INDUSTRIAL= \
    images/ec2a* \
    uap-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    uap-fw/BZ.mt7621.*

IMAGE-UAP+=$(IMAGE-UAP-FLEX)
IMAGE-UAP+=$(IMAGE-UBB)
IMAGE-UAP+=$(IMAGE-UAP-INDUSTRIAL)

DIAG_MODEL=UniFiAP
DIAG_UI_MODEL=UniFiAP
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

UPYFCD_VER=
FCDIMG_VER=
UBNTLIB_VER=
TOOL_VER=

# Assign tools for every product
TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee

TOOLS-UBB+= \
    uap/cfg_part.bin \
    uap/helper_IPQ40xx \
    uap/id_rsa \
    uap/id_rsa.pub 

TOOLS-UAP-INDUSTRIAL+= \
    uap/helper_UNIFI_MT7621_release

# Assign common tool for every model
TOOLS-UAP-INDUSTRIAL+=$(TOOLS-CONFIG)
TOOLS-UBB+=$(TOOLS-CONFIG)

# Assign UAP series tools
TOOLS-UAP+=$(TOOLS-UBB)
TOOLS-UAP+=$(TOOLS-UAP-INDUSTRIAL)


$(eval $(call ProductImage,UAP,FCD-UAP-ALL-$(VER)))
$(eval $(call ProductImage,UAP-FLEXHD,FCD-UAP-FLEXHD-$(VER)))
$(eval $(call ProductImage,UBB,FCD-UAP-UBB-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UAP-INDUSTRIAL,FCD-UAP-INDUSTRIAL-$(VER)))
