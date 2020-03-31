# Images

IMAGE-UAP-FLEXHD= \
    images/ec26* \
    uap-fw/unifiap-mt7621* \
    uap-fw/unifi-v1.0.9.57-gd7bab423_uap-mt7621-32MB_u-boot.bin \
    uap-fw/V9-uImage_5030-TXBF_enabled-20171101.dms \
    uap-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    uap-fw/BZ.mt7621.*

IMAGE-UAP-IWHD= \
    images/ec22* \
    uap-fw/unifiap-mt7621* \
    uap-fw/unifi-v1.0.9.57-gd7bab423_uap-mt7621-32MB_u-boot.bin \
    uap-fw/V9-uImage_5030-TXBF_enabled-20171101.dms \
    uap-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    uap-fw/BZ.mt7621.*

IMAGE-UAP-NANO-IW-FLEXHD= \
    images/ec20* \
    images/ec22* \
    images/ec26* \
    uap-fw/uap-nanohd-fw.bin \
    uap-fw/uap-iwhd-fw.bin \
    uap-fw/uap-flexhd-fw.bin \
    uap-fw/unifiap-mt7621* \
    uap-fw/unifi-v1.0.9.57-gd7bab423_uap-mt7621-32MB_u-boot.bin \
    uap-fw/V9-uImage_5030-TXBF_enabled-20171101.dms \
    uap-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    uap-fw/BZ.mt7621.*

IMAGE-UBB= \
    images/dc98* \
    images/dc9c* \
    uap-fw/UBB* \
    uap-fw/ubntubb-u-boot.rom \
    uap-fw/Unifi_bridge-spf6.1.1_nor-v4.bin

IMAGE-UAP-INDUSTRIAL= \
    images/ec2a* \
    uap-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    uap-fw/BZ.mt7621.*

IMAGE-UAP6= \
    images/a610* \
    images/a611* \
    images/a612* \
    images/a613* \
    images/a614* \
    uap-fw/uap6* \
    uap-fw/lede-mtk-mt7621-UAP6-initramfs-kernel.bin \
    uap-fw/u-boot-mt7621-mfg-v2.bin \
    uap-fw/kernel-uap6-afi6-7603_7915a-v3.bin \
    uap-fw/unifi-PR-82.56-g3967dfe8_uap6-mt7621-31MB_u-boot.bin \
    uap-fw/BZ.mt7621.uap6*


IMAGE-UAP+=$(IMAGE-UAP-FLEXHD)
IMAGE-UAP+=$(IMAGE-UAP-IWHD)
IMAGE-UAP+=$(IMAGE-UAP-NANO-IW-FLEXHD)
IMAGE-UAP+=$(IMAGE-UBB)
IMAGE-UAP+=$(IMAGE-UAP-INDUSTRIAL)
IMAGE-UAP+=$(IMAGE-UAP6)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiAP
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/helper_UNIFI_MT7621_release \
    common/helper_UAP6_MT7621_release

# Project specific tools

TOOLS-UBB+= \
    uap/cfg_part.bin \
    uap/helper_IPQ40xx \
    uap/id_rsa \
    uap/id_rsa.pub 

TOOLS-UAP-INDUSTRIAL+= \
    uap/helper_UNIFI_MT7621_release

TOOLS-UAP-FLEXHD+=$(TOOLS-CONFIG)
TOOLS-UAP-IWHD+=$(TOOLS-CONFIG)
TOOLS-UAP-NANO-IW-FLEXHD+=$(TOOLS-CONFIG)
TOOLS-UAP6+=$(TOOLS-CONFIG)

# Assign common tool for every model
TOOLS-UAP-INDUSTRIAL+=$(TOOLS-CONFIG)
TOOLS-UBB+=$(TOOLS-CONFIG)

# Assign UAP series tools
TOOLS-UAP+=$(TOOLS-UBB)
TOOLS-UAP+=$(TOOLS-UAP-INDUSTRIAL)

# Project target

$(eval $(call ProductImage,UAP,FCD_$(PRD)_UAP-ALL_$(VER)))
$(eval $(call ProductImage,UAP-FLEXHD,FCD_$(PRD)_UAP-FLEXHD_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UAP-IWHD,FCD_$(PRD)_UAP-IWHD_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UAP-NANO-IW-FLEXHD,FCD_$(PRD)_UAP-NANO-IW-FLEXHD_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UBB,FCD_$(PRD)_UAP-UBB_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UAP-INDUSTRIAL,FCD_$(PRD)_UAP-INDUSTRIAL_$(VER)))
$(eval $(call ProductImage,UAP6,FCD_$(PRD)_UAP6_$(VER)_$(FWVER)))
