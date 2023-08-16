# Images

IMAGE-UDM-BASIC= \
    udm-fw/ubnt-upgrade-compat.tgz

IMAGE-UDM-00623+=$(IMAGE-UDM-BASIC)
IMAGE-UDM-00623+= \
    images/ea11* \
    udm-fw/ubnt_udm_all_rev1_boot.img \
    udm-fw/udm/*

IMAGE-UDM-01134+=$(IMAGE-UDM-BASIC)
IMAGE-UDM-01134+= \
    images/ea11* \
    udm-fw/ubnt_udm_all_rev1_boot.img \
    udm-fw/udm/*

IMAGE-UDMSE+=$(IMAGE-UDM-BASIC)
IMAGE-UDMSE+= \
    images/ea13* \
    udm-fw/ubnt_udm_all_rev1_boot.img \
    udm-fw/uImage-udmse.r \
    udm-fw/UDM.alpinev2.v1.0.30+builder.1762.cfb07db.190916.1318.bin

IMAGE-UDMPRO-00723+=$(IMAGE-UDM-BASIC)
IMAGE-UDMPRO-00723+= \
    images/ea15* \
    udm-fw/ubnt_udm_all_rev1_boot.img \
    udm-fw/udmp/* 

IMAGE-UDMPRO-01133+=$(IMAGE-UDM-BASIC)
IMAGE-UDMPRO-01133+= \
    images/ea15* \
    udm-fw/udmp/* 

IMAGE-UXGPRO+=$(IMAGE-UDM-BASIC)
IMAGE-UXGPRO+= \
    images/ea19* \
    uxg-fw/alpine/*

IMAGE-UDMXG=
#IMAGE-UDMXG=images/ea17* \
#            udm-fw/*

IMAGE-UDMB= \
    images/ec25* \
    udm-fw/udm-b-* \
    udm-fw/Unifi-ONE-* \
    udm-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    udm-fw/unifi-v1.0.9.57-gd7bab423_uap-mt7621-32MB_u-boot.bin \
    udm-fw/unifi-v1.1.19.50-g761f9863_uap-mt7621-32MB_u-boot.bin \
	udm-fw/lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel* \
    udm-fw/BZ.mt7621.*

IMAGE-UDMLITE= \
    images/ec2d* \
    udm-fw/udm-lite/* 

IMAGE-UDR= \
    images/eccc* \
    udm-fw/udr/* 

IMAGE-UDM-SE+=$(IMAGE-UDM-BASIC)
IMAGE-UDM-SE+= \
    images/ea2c* \
    udm-fw/udm-se/*

IMAGE-UDW= \
    images/ea2a* \
    udm-fw/udw/*

IMAGE-UDW-PRO= \
    images/ea2b* \
    udm-fw/udw-pro/*

IMAGE-UDW-PRO-PU+= \
    images/ea2e* \
    udm-fw/udw-pro-pu/*

IMAGE-UDR-PRO+= \
    images/a678* \
    udm-fw/udr-pro/*

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiDream
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/helper_UNIFI_MT7621_release \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-UDM-00623+=$(TOOLS-CONFIG)
TOOLS-UDM-00623+= udm/*
TOOLS-UDM-01134+=$(TOOLS-CONFIG)
TOOLS-UDM-01134+= udm/*

TOOLS-UDMSE=$(TOOLS-UDM)
TOOLS-UDMPRO-00723=$(TOOLS-UDM)
TOOLS-UDMPRO-01133=$(TOOLS-UDM)

TOOLS-UXGPRO=$(TOOLS-UDM)
TOOLS-UDR=$(TOOLS-UDM)

TOOLS-UDMXG+=$(TOOLS-CONFIG)
TOOLS-UDMXG+= udm_xg/*

TOOLS-UDMB+=$(TOOLS-CONFIG)
TOOLS-UDMB+= udm_b/*

TOOLS-UDMLITE+=$(TOOLS-CONFIG)
TOOLS-UDMLITE+= udm_lite/*

TOOLS-UDM-SE+=$(TOOLS-CONFIG)
TOOLS-UDM-SE+= \
    udm/helper_AL324* \
    udm_se/nvr-lcm-tools* \
    udm_se/unas.pub

TOOLS-UDW+=$(TOOLS-CONFIG)
TOOLS-UDW+= \
    udm/helper_AL324* \
    udw/nvr-lcm-tools*


TOOLS-UDW-PRO+=$(TOOLS-CONFIG)
TOOLS-UDW-PRO+= \
    udm/helper_AL324*

TOOLS-UDW-PRO-PU=$(TOOLS-UDM)
TOOLS-UDW-PRO-PU+= \
    pdu_pro/helper_MT7628_release

TOOLS-UDR-PRO+=$(TOOLS-CONFIG)
TOOLS-UDR-PRO+= \
    udm/helper_AL324*

# Project target
$(eval $(call ProductImage,UDM-00623,FCD_$(PRD)_UDM_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDM-01134,FCD_$(PRD)_UDM_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDMSE,FCD_$(PRD)_UDMSE_$(VER)))
$(eval $(call ProductImage,UDMPRO-00723,FCD_$(PRD)_UDMPRO-00723_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDMPRO-01133,FCD_$(PRD)_UDMPRO-01133_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UXGPRO,FCD_$(PRD)_UXGPRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDMXG,FCD_$(PRD)_UDMXG_$(VER)))
$(eval $(call ProductImage,UDMB,FCD_$(PRD)_UDMB_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDMLITE,FCD_$(PRD)_UDMLITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDR,FCD_$(PRD)_UDR_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDM-SE,FCD_$(PRD)_UDM-SE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDW,FCD_$(PRD)_UDW_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDW-PRO,FCD_$(PRD)_UDW_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDW-PRO-PU,FCD_$(PRD)_UDW-PRO-PU_$(VER)_$(FWVER)))
# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,UDM-00623,FCD_$(PRD)_UDM_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDM-01134,FCD_$(PRD)_UDM_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDMSE,FCD_$(PRD)_UDMSE_$(VER)))
$(eval $(call ProductCompress,UDMPRO,FCD_$(PRD)_UDMPRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UXGPRO,FCD_$(PRD)_UXGPRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDMXG,FCD_$(PRD)_UDMXG_$(VER)))
$(eval $(call ProductCompress,UDMB,FCD_$(PRD)_UDMB_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDMLITE,FCD_$(PRD)_UDMLITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDR,FCD_$(PRD)_UDR_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDM-SE,FCD_$(PRD)_UDM-SE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDW,FCD_$(PRD)_UDW_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDW-PRO,FCD_$(PRD)_UDW_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDW-PRO-PU,FCD_$(PRD)_UDW-PRO-PU_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDR-PRO,FCD_$(PRD)_UDR-ULTRA_$(VER)_$(FWVER)))

# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,00917_ea2c))
$(eval $(call ProductCompress2,01097_ea2c))
$(eval $(call ProductCompress2,01029_ea2e))
$(eval $(call ProductCompress2,00623_ea11))
$(eval $(call ProductCompress2,02719_ea17))
$(eval $(call ProductCompress2,00618_ea13))
$(eval $(call ProductCompress2,00723_ea15))
$(eval $(call ProductCompress2,01133_ea15))
$(eval $(call ProductCompress2,00622_ec25))
$(eval $(call ProductCompress2,00786_eccc))
$(eval $(call ProductCompress2,00633_ec28))
$(eval $(call ProductCompress2,01075_ec2d))
$(eval $(call ProductCompress2,00843_ea2a))
$(eval $(call ProductCompress2,00845_ea2b))
$(eval $(call ProductCompress2,07651_a678))
$(eval $(call ProductCompress2,08806_a679))
$(eval $(call ProductCompress2,UniFiDream_UDMSE-SERIES))
