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
    uap-fw/BZ.mt7621.* \
    uap-fw/BZ.mt7622.*

IMAGE-U6-PRO= \
	u6-fw/ipq5018/* \
    images/a650* 
IMAGE-U6-Mesh= \
	u6-fw/ipq5018/* \
    images/a651* 
IMAGE-U6-IW= \
	u6-fw/ipq5018/* \
    images/a652*
IMAGE-U6-Extender= \
	u6-fw/ipq5018/* \
    images/a653*
IMAGE-U6-Enterprise= \
	u6-fw/ipq5018/* \
    images/a654*
IMAGE-U6-Infinity= \
	u6-fw/ipq5018/* \
    images/a655*
IMAGE-U6-Enterprise-IW= \
	u6-fw/ipq5018/* \
    images/a656*
IMAGE-U6-QCA-Series= \
	u6-fw/ipq5018/* \
    images/a650* \
    images/a651* \
    images/a652* \
    images/a653* \
    images/a654* \
    images/a655* \
	images/a656* 
IMAGE-U6-LR= \
	u6-fw/mt7622/* \
	images/a620*

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
    common/aarch64-rpi4-64k-ee

TOOLS-CONFIG-U6-MT7622= \
    common/helper_UAP6_MT7622_release

# Project specific tools
TOOLS-U6+=$(TOOLS-CONFIG)
TOOLS-U6-PRO+=$(TOOLS-CONFIG)
TOOLS-U6-Mesh+=$(TOOLS-CONFIG)
TOOLS-U6-IW+=$(TOOLS-CONFIG)
TOOLS-U6-Extender+=$(TOOLS-CONFIG)
TOOLS-U6-Enterprise+=$(TOOLS-CONFIG)
TOOLS-U6-Infinity+=$(TOOLS-CONFIG)
TOOLS-U6-Enterprise-IW+=$(TOOLS-CONFIG)
TOOLS-U6-QCA-Series+=$(TOOLS-CONFIG)
TOOLS-U6-LR+=$(TOOLS-CONFIG) $(TOOLS-CONFIG-U6-MT7622)

# Project target
$(eval $(call ProductImage,U6,FCD_$(PRD)_U6_$(VER)_$(FWVER)))
$(eval $(call ProductImage,U6-PRO,FCD_$(PRD)_U6-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,U6-Mesh,FCD_$(PRD)_U6-Mesh_$(VER)_$(FWVER)))
$(eval $(call ProductImage,U6-IW,FCD_$(PRD)_U6-IW_$(VER)_$(FWVER)))
$(eval $(call ProductImage,U6-Extender,FCD_$(PRD)_U6-IW_$(VER)_$(FWVER)))
$(eval $(call ProductImage,U6-Enterprise,FCD_$(PRD)_U6-Enterprise_$(VER)_$(FWVER)))
$(eval $(call ProductImage,U6-Infinity,FCD_$(PRD)_U6-Infinity_$(VER)_$(FWVER)))
$(eval $(call ProductImage,U6-Enterprise-IW,FCD_$(PRD)_U6-Enterprise-IW_$(VER)_$(FWVER)))
$(eval $(call ProductImage,U6-QCA-Series,FCD_$(PRD)_Series_$(VER)_$(FWVER)))
$(eval $(call ProductImage,U6-LR,FCD_$(PRD)_U6-LR_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,U6,FCD_$(PRD)_U6_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,U6-PRO,FCD_$(PRD)_U6-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,U6-Mesh,FCD_$(PRD)_U6-Mesh_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,U6-IW,FCD_$(PRD)_U6-IW_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,U6-Extender,FCD_$(PRD)_U6-Extender_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,U6-Enterprise,FCD_$(PRD)_U6-Enterprise_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,U6-Infinity,FCD_$(PRD)_U6-Infinity_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,U6-Enterprise-IW,FCD_$(PRD)_U6-Enterprise-IW_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,U6-QCA-Series,FCD_$(PRD)_U6-QCA-Series_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,U6-LR,FCD_$(PRD)_U6-LR_$(VER)_$(FWVER)))


# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,00773_a612))
$(eval $(call ProductCompress2,00744_a620))
$(eval $(call ProductCompress2,00963_a650))
$(eval $(call ProductCompress2,10743_a651))
$(eval $(call ProductCompress2,10745_a652))
$(eval $(call ProductCompress2,10746_a653))
$(eval $(call ProductCompress2,10898_a654))
$(eval $(call ProductCompress2,10897_a655))
$(eval $(call ProductCompress2,00956_a656))
