# Images
#

IMAGE-UAP-FLEXHD= \
    images/ec26* \
    uap-fw/uap-nanohd-fcd.bin \
    uap-fw/unifiap-mt7621* \
    uap-fw/unifi-v1.0.9.57-gd7bab423_uap-mt7621-32MB_u-boot.bin \
    uap-fw/unifi-v1.1.19.50-g761f9863_uap-mt7621-32MB_u-boot.bin \
    uap-fw/V9-uImage_5030-TXBF_enabled-20171101.dms \
    uap-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
	uap-fw/lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel* \
    uap-fw/BZ.mt7621.*

IMAGE-UAP-IWHD= \
    images/ec22* \
    uap-fw/uap-nanohd-fcd.bin \
    uap-fw/unifiap-mt7621* \
    uap-fw/unifi-v1.0.9.57-gd7bab423_uap-mt7621-32MB_u-boot.bin \
    uap-fw/unifi-v1.1.19.50-g761f9863_uap-mt7621-32MB_u-boot.bin \
    uap-fw/V9-uImage_5030-TXBF_enabled-20171101.dms \
    uap-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
	uap-fw/lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel* \
    uap-fw/BZ.mt7621.*

IMAGE-UAP-NANO-IW-FLEXHD= \
    images/ec20* \
    images/ec22* \
    images/ec26* \
    uap-fw/uap-nanohd-fcd.bin \
	uap-fw/uap-nanohd-fw.bin \
    uap-fw/uap-iwhd-fw.bin \
    uap-fw/uap-flexhd-fw.bin \
    uap-fw/unifiap-mt7621* \
    uap-fw/unifi-v1.0.9.57-gd7bab423_uap-mt7621-32MB_u-boot.bin \
    uap-fw/unifi-v1.1.19.50-g761f9863_uap-mt7621-32MB_u-boot.bin \
    uap-fw/V9-uImage_5030-TXBF_enabled-20171101.dms \
    uap-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
	uap-fw/lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel* \
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

IMAGE-UBB-XG= \
    images/dd12* \
    uap-fw/UBB_XG* \
    uap-fw/UBBXG* \
    uap-fw/af60* \
    uap-fw/NAND_factory_ubi.img

IMAGE-ULTE-FLEX= \
    images/e614* \
    images/e615* \
    uap-fw/ulte-flex/*

IMAGE-UAP-AC-Lite-LR-Pro= \
    images/e517* \
    images/e527* \
    images/e537* \
    uap-fw/BZ.qca956x*-uboot.bin\
    uap-fw/ART.qca956x*ART*.bin

IMAGE-ULTE-PRO= \
    images/e611* \
    images/e612* \
    images/e613* \
    uap-fw/ulte-pro/*

IMAGE-UAP+=$(IMAGE-UAP-FLEXHD)
IMAGE-UAP+=$(IMAGE-UAP-IWHD)
IMAGE-UAP+=$(IMAGE-UAP-NANO-IW-FLEXHD)
IMAGE-UAP+=$(IMAGE-UBB)
IMAGE-UAP+=$(IMAGE-UAP-INDUSTRIAL)
IMAGE-UAP+=$(IMAGE-UBB-XG)
IMAGE-UAP+=$(IMAGE-ULTE-FLEX)
IMAGE-UAP+=$(IMAGE-ULTE-PRO)

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
    common/aarch64-rpi4-64k-ee

# Assign common tool for every model
TOOLS-UBB+= \
    uap/cfg_part.bin \
    uap/helper_IPQ40xx \
    uap/id_rsa \
    uap/id_rsa.pub

TOOLS-UAP-INDUSTRIAL+= \
    uap/helper_UNIFI_MT7621_release

TOOLS-ULTE-FLEX+=$(TOOLS-CONFIG)
TOOLS-ULTE-FLEX+= \
    ulte_flex/helper*

TOOLS-UAP-AC-Lite-LR-Pro+=$(TOOLS-CONFIG)
TOOLS-UAP-AC-Lite-LR-Pro+= \
    uap/helper_ARxxxx_musl

TOOLS-UAP-FLEXHD+=$(TOOLS-CONFIG)
TOOLS-UAP-IWHD+=$(TOOLS-CONFIG)
TOOLS-UAP-NANO-IW-FLEXHD+=$(TOOLS-CONFIG)
TOOLS-UAP-INDUSTRIAL+=$(TOOLS-CONFIG)
TOOLS-UBB+=$(TOOLS-CONFIG)
TOOLS-UBB-XG+=$(TOOLS-CONFIG)

TOOLS-ULTE-PRO+=$(TOOLS-CONFIG)
TOOLS-ULTE-PRO+= \
    ulte_pro/helper* \
    ulte_pro/burnin.cfg


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
$(eval $(call ProductImage,UBB-XG,FCD_$(PRD)_UAP-UBB-XG_$(VER)_$(FWVER)))
$(eval $(call ProductImage,ULTE-FLEX,FCD_$(PRD)_ULTE-FLEX_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UAP-AC-Lite-LR-Pro,FCD_$(PRD)_UAP-AC-Lite-LR-Pro_$(VER)_$(FWVER)))
$(eval $(call ProductImage,ULTE-PRO,FCD_$(PRD)_ULTE-PRO_$(VER)_$(FWVER)))


# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,UAP,FCD_$(PRD)_UAP-ALL_$(VER)))
$(eval $(call ProductCompress,UAP-FLEXHD,FCD_$(PRD)_UAP-FLEXHD_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UAP-IWHD,FCD_$(PRD)_UAP-IWHD_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UAP-NANO-IW-FLEXHD,FCD_$(PRD)_UAP-NANO-IW-FLEXHD_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UBB,FCD_$(PRD)_UAP-UBB_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UAP-INDUSTRIAL,FCD_$(PRD)_UAP-INDUSTRIAL_$(VER)))
$(eval $(call ProductCompress,UBB-XG,FCD_$(PRD)_UAP-UBB-XG_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,ULTE-FLEX,FCD_$(PRD)_ULTE-FLEX_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UAP-AC-Lite-LR-Pro,FCD_$(PRD)_UAP-AC-Lite-LR-Pro_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,ULTE-PRO,FCD_$(PRD)_ULTE-PRO_$(VER)_$(FWVER)))



# Project compressed type2 file for RPi FCD host
$(eval $(call ProductCompress2,00390_e537))
$(eval $(call ProductCompress2,00800_dc9c))
$(eval $(call ProductCompress2,00958_dd12))
$(eval $(call ProductCompress2,00391_e517))
$(eval $(call ProductCompress2,00600_ec22))
$(eval $(call ProductCompress2,00641_ec26))
$(eval $(call ProductCompress2,00694_dc98))
$(eval $(call ProductCompress2,00573_ec20))
$(eval $(call ProductCompress2,00710_ec2a))
$(eval $(call ProductCompress2,02525_e611))
$(eval $(call ProductCompress2,00718_e612))
$(eval $(call ProductCompress2,00788_e613))
$(eval $(call ProductCompress2,01155_e613))
$(eval $(call ProductCompress2,00830_e614))
$(eval $(call ProductCompress2,00830_e618))
$(eval $(call ProductCompress2,00758_e615))
$(eval $(call ProductCompress2,00758_e619))
$(eval $(call ProductCompress2,00392_e527))
$(eval $(call ProductCompress2,01068_dcb4))
$(eval $(call ProductCompress2,01068_dcb5))
$(eval $(call ProductCompress2,03621_a922))
$(eval $(call ProductCompress2,01112_dca6))
$(eval $(call ProductCompress2,01248_dca7))
$(eval $(call ProductCompress2,01283_dca8))
$(eval $(call ProductCompress2,00438_e530))
$(eval $(call ProductCompress2,00533_e540))
$(eval $(call ProductCompress2,00542_e560))
$(eval $(call ProductCompress2,00562_e570))
$(eval $(call ProductCompress2,00557_e580))
$(eval $(call ProductCompress2,00557_e585))
$(eval $(call ProductCompress2,UniFiAP_UACCMPOE-SERIES,FCD_$(PRD)_UACCMPOE-SERIES_$(VER)_$(FWVER)))
$(eval $(call ProductCompress2,UMR_EU_AC-SERIES))
$(eval $(call ProductCompress2,UMR_US_AC-SERIES))
$(eval $(call ProductCompress2,UAP_ACGEN2-SERIES))
$(eval $(call ProductCompress2,01247_e618))
$(eval $(call ProductCompress2,00729_e619))
$(eval $(call ProductCompress2,08938_e620))
