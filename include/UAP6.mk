# Images
#

IMAGE-U6= \
    images/a610* \
    images/a611* \
    images/a612* \
    images/a613* \
    images/a614* \
	images/a620* \
    uap-fw/uap6* \
	uap-fw/u6* \
    uap-fw/lede-mtk-mt7621-UAP6-initramfs*.bin \
    uap-fw/u-boot-mt7621-mfg*.bin \
    uap-fw/kernel-uap6-afi6-7603_7915a*.bin \
    uap-fw/unifi-v1.1.21.53-gcb13e97f_uap6-mt7621-31MB_u-boot.bin \
    uap-fw/BZ.mt7621.*

IMAGE-UAP+=$(IMAGE-U6)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiAP6
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/helper_UNIFI_MT7621_release \
    common/aarch64-rpi4-64k-ee \
	common/helper_UAP6_MT7622_release \
	common/helper_UAP6_MT7621_release 

# Project specific tools
TOOLS-U6+=$(TOOLS-CONFIG)

# Project target
$(eval $(call ProductImage,U6,FCD_$(PRD)_U6_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,U6,FCD_$(PRD)_U6_$(VER)_$(FWVER)))
