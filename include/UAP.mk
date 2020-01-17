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

IMAGE-UAP+=$(IMAGE-UAP-FLEXHD)
IMAGE-UAP+=$(IMAGE-UAP-IWHD)
IMAGE-UAP+=$(IMAGE-UAP-NANO-IW-FLEXHD)
IMAGE-UAP+=$(IMAGE-UBB)
IMAGE-UAP+=$(IMAGE-UAP-INDUSTRIAL)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiAP
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# FCD images repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-image.git

UAP-FLEXHD_FCDIMG_HASH=
UAP-IWHD_FCDIMG_HASH=
UAP-NANO-IW-FLEXHD_FCDIMG_HASH=
UBB_FCDIMG_HASH=
UAP-INDUSTRIAL_FCDIMG_HASH=

FCDIMG_VER=

# UBNTLIB repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-ubntlib.git

UAP-FLEXHD_UBNTLIB_HASH=
UAP-IWHD_UBNTLIB_HASH=
UAP-NANO-IW-FLEXHD_UBNTLIB_HASH=
UBB_UBNTLIB_HASH=
UAP-INDUSTRIAL_UBNTLIB_HASH=

UBNTLIB_VER=

# TOOL repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-tools.git

UAP-FLEXHD_TOOL_HASH=
UAP-IWHD_TOOL_HASH=
UAP-NANO-IW-FLEXHD_TOOL_HASH=
UBB_TOOL_HASH=
UAP-INDUSTRIAL_TOOL_HASH=

TOOL_VER=

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/helper_UNIFI_MT7621_release

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

# Assign common tool for every model
TOOLS-UAP-INDUSTRIAL+=$(TOOLS-CONFIG)
TOOLS-UBB+=$(TOOLS-CONFIG)

# Assign UAP series tools
TOOLS-UAP+=$(TOOLS-UBB)
TOOLS-UAP+=$(TOOLS-UAP-INDUSTRIAL)

# Project target

$(eval $(call ProductImage,UAP,FCD-UAP-ALL-$(VER)))
$(eval $(call ProductImage,UAP-FLEXHD,FCD-UAP-FLEXHD-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UAP-IWHD,FCD-UAP-IWHD-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UAP-NANO-IW-FLEXHD,FCD-UAP-NANO-IW-FLEXHD-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UBB,FCD-UAP-UBB-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UAP-INDUSTRIAL,FCD-UAP-INDUSTRIAL-$(VER)))
