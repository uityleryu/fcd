
# Images
#
IMAGE-UISP-S-Plus= \
    images/ee7c* \
    unms-fw/uisp-s-plus/uisp-s-plus*

IMAGE-UISP-P-LITE= \
    images/eefa* \
    unms-fw/UISP-P-Lite.bin \
    unms-fw/u-boot-ar933x-ep.bin \
    unms-fw/uisp_p_lite_epx_cfg.bin \
    unms-fw/UISPP* \

IMAGE-UISP-CONSOLE= \
    images/ee6a* \
    unms-fw/uisp-console/* \

IMAGE-UISP-LTE= \
    images/dca2* \
    images/dca3* \
    unms-fw/LL.qca956x.* \
    unms-fw/uisp-lte-initramfs-64MB.img \

IMAGE-UISP-O-LITE= \
    images/ee6c* \
    unms-fw/UISPO.mt7621.* \

IMAGE-UISP-O-PRO= \
    images/eed3* \
    unms-fw/DIAG_UISP_O_Pro_1.3.4.7.8-Dev03.vmlinux.bix \
    unms-fw/UISP_O_PRO_Pre_u-boot-60495.bin

IMAGE-UISP-R= \
    images/ee6e* \
    unms-fw/uisp-r/UISPR.mt7621* \

IMAGE-UISP-R-PRO= \
    images/ee6d* \
    unms-fw/uisp-r-pro/* \

IMAGE-UISP-P= \
    # images/ee5a* \

IMAGE-UISP-P-PRO= \
    # images/ee5b* \

IMAGE-UISP-P-UPS= \
		unms-fw/uisp-p-ups/UISP-P-UPS* \
		images/eed6*

IMAGE-UNMS+=$(IMAGE-UISP-S-Plus)
IMAGE-UNMS+=$(IMAGE-UISP-CONSOLE)
IMAGE-UNMS+=$(IMAGE-UISP-LTE)
IMAGE-UNMS+=$(IMAGE-UISP-O-LITE)
IMAGE-UNMS+=$(IMAGE-UISP-O-PRO)
IMAGE-UNMS+=$(IMAGE-UISP-S-MICRO)
IMAGE-UNMS+=$(IMAGE-UISP-R)
IMAGE-UNMS+=$(IMAGE-UISP-R-PRO)
IMAGE-UNMS+=$(IMAGE-UISP-P-LITE)
IMAGE-UNMS+=$(IMAGE-UISP-P)
IMAGE-UNMS+=$(IMAGE-UISP-P-PRO)
IMAGE-UNMS+=$(IMAGE-UISP-P-UPS)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UbiquitiNMS
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee*

# Project specific tools

TOOLS-UNMS+=$(TOOLS-CONFIG)

TOOLS-UISP-CONSOLE=$(TOOLS-UNMS)
TOOLS-UISP-CONSOLE+= uisp-console/helper_AL324_release

TOOLS-UNMS-S-LITE=$(TOOLS-UNMS)
TOOLS-UNMS-S-LITE+= unms-slite/*

TOOLS-UISP-S-LITE=$(TOOLS-UNMS)
TOOLS-UISP-S-LITE+= unms-slite/*

TOOLS-UISP-LTE=$(TOOLS-UNMS)
TOOLS-UISP-LTE+= unms-lte/*

TOOLS-UISP-O-LITE=$(TOOLS-UNMS)
TOOLS-UISP-O-LITE+= uisp-o-lite/*

TOOLS-UISP-O-PRO=$(TOOLS-UNMS)
TOOLS-UISP-O-PRO+= unms-spro/*

TOOLS-UISP-R=$(TOOLS-UNMS)
TOOLS-UISP-R+= uisp-r/helper_MT7621_release

TOOLS-UISP-R-PRO=$(TOOLS-UNMS)
TOOLS-UISP-R-PRO+= uisp-r-pro/helper_AL324_release

TOOLS-UISP-P-LITE=$(TOOLS-UNMS)
TOOLS-UISP-P-LITE+= uisp-p-lite/*

TOOLS-UISP-P=$(TOOLS-UNMS)
TOOLS-UISP-P+= uisp_p/*

TOOLS-UISP-P-PRO=$(TOOLS-UNMS)
TOOLS-UISP-P-PRO+= uisp_p_pro/*

TOOLS-UISP-P-UPS=$(TOOLS-UNMS)
TOOLS-UISP-P-UPS+= eed6/*

TOOLS-UISP-S-Plus=$(TOOLS-UNMS)
TOOLS-UISP-S-Plus+= uisp_s_plus/helper_MRVL_ACT5_release

# Project target
$(eval $(call ProductImage,UNMS,FCD_$(PRD)_UNMS-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-CONSOLE,FCD_$(PRD)_UISP-CONSOLE_$(VER)_$(FWVER)))
# UNMS-S-LITE is a special case that it will keep this BOM revision, system ID and model name
$(eval $(call ProductImage,UNMS-S-LITE,FCD_$(PRD)_UNMS-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-S-LITE,FCD_$(PRD)_UISP-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-LTE,FCD_$(PRD)_UNMS-LTE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-O-LITE,FCD_$(PRD)_UISP-O-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-O-PRO,FCD_$(PRD)_UISP-O-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-R,FCD_$(PRD)_UISP-R_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-R-PRO,FCD_$(PRD)_UISP-R-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-P-LITE,FCD_$(PRD)_UISP-P-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-P,FCD_$(PRD)_UISP-P_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-P-PRO,FCD_$(PRD)_UISP-P-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-P-UPS,FCD_$(PRD)_UISP-P-UPS_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UISP-S-Plus,FCD_$(PRD)_UISP-S-Plus_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,UNMS,FCD_$(PRD)_UNMS-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-CONSOLE,FCD_$(PRD)_UISP-CONSOLE_$(VER)_$(FWVER)))
# UNMS-S-LITE is a special case that it will keep this BOM revision, system ID and model name
$(eval $(call ProductCompress,UNMS-S-LITE,FCD_$(PRD)_UNMS-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-S-LITE,FCD_$(PRD)_UISP-S-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-LTE,FCD_$(PRD)_UNMS-LTE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-O-LITE,FCD_$(PRD)_UISP-O-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-O-PRO,FCD_$(PRD)_UISP-O-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-R,FCD_$(PRD)_UISP-R_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-R-PRO,FCD_$(PRD)_UISP-R-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-P-LITE,FCD_$(PRD)_UISP-P-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-P,FCD_$(PRD)_UISP-P_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-P-PRO,FCD_$(PRD)_UISP-P-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-P-UPS,FCD_$(PRD)_UISP-P-UPS_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UISP-S-Plus,FCD_$(PRD)_UISP-S-Plus_$(VER)_$(FWVER)))

# ==================================================================================================
# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,00817_eed0))
$(eval $(call ProductCompress2,01019_eed1))
$(eval $(call ProductCompress2,00900_ee50))
$(eval $(call ProductCompress2,00988_ee6f))
$(eval $(call ProductCompress2,00782_dca2))
$(eval $(call ProductCompress2,00832_dca3))
$(eval $(call ProductCompress2,00973_ee6a))
$(eval $(call ProductCompress2,01129_ee6a))
$(eval $(call ProductCompress2,01168_ee6a))
$(eval $(call ProductCompress2,01201_ee6a))
$(eval $(call ProductCompress2,00819_ee6c))
$(eval $(call ProductCompress2,00820_eed3))
$(eval $(call ProductCompress2,00821_eefa))
$(eval $(call ProductCompress2,01061_ee6d))
$(eval $(call ProductCompress2,00989_ee6e))
$(eval $(call ProductCompress2,00990_ee5a))
$(eval $(call ProductCompress2,00822_ee5b))
$(eval $(call ProductCompress2,02932_eed4))
$(eval $(call ProductCompress2,03162_eed5))
$(eval $(call ProductCompress2,00732_1200))
$(eval $(call ProductCompress2,UISP_UDC-SERIES))
$(eval $(call ProductCompress2,UISP_Console-SERIES))
$(eval $(call ProductCompress2,01123_eed6))
$(eval $(call ProductCompress2,01223_ee7c))
