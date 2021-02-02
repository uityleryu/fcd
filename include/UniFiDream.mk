# Images

IMAGE-UDM-BASIC= \
    udm-fw/ubnt-upgrade-compat.tgz

IMAGE-UDM+=$(IMAGE-UDM-BASIC)
IMAGE-UDM+= \
    images/ea11* \
    udm-fw/ubnt_udm_all_rev1_boot.img \
    udm-fw/uImage-udm-udmp.r \
    udm-fw/UDM.alpinev2.v1.8.6.6a09c7c.210125.1544.bin

IMAGE-UDMSE+=$(IMAGE-UDM-BASIC)
IMAGE-UDMSE+= \
    images/ea13* \
    udm-fw/ubnt_udm_all_rev1_boot.img \
    udm-fw/uImage-udmse.r \
    udm-fw/UDM.alpinev2.v1.0.30+builder.1762.cfb07db.190916.1318.bin

IMAGE-UDMPRO+=$(IMAGE-UDM-BASIC)
IMAGE-UDMPRO+= \
    images/ea15* \
    udm-fw/ubnt_udm_all_rev1_boot.img \
    udm-fw/uImage-udm-udmp.r \
    udm-fw/UDMPRO.alpinev2.v1.8.6.6a09c7c.210125.1544.bin

IMAGE-UXGPRO+=$(IMAGE-UDM-BASIC)
IMAGE-UXGPRO+= \
    images/ea19* \
    udm-fw/boot-uxg.img \
    udm-fw/uImage-uxg.r \
    udm-fw/UXG*

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
    images/ec28* \
    udm-fw/uImage-LoCo \
	udm-fw/UDM.lite.uImage.recovery \
	udm-fw/UDM.mt7622.v1.8.0-pre+ubnt.2718.a4c17ceM.200430.0902.bin

IMAGE-UDR= \
    images/eccc* \
    udm-fw/*udr*.bin \
    udm-fw/UDR.mt7622*

IMAGE-UDMPRO-SE+=$(IMAGE-UDM-BASIC)
IMAGE-UDMPRO-SE+= \
    images/ea2c* \
    udm-fw/uImage-udmpro-se* \
    udm-fw/boot-udmpro-se* \
    udm-fw/UDMPROSE.arm64*

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

TOOLS-UDM+=$(TOOLS-CONFIG)
TOOLS-UDM+= udm/*

TOOLS-UDMSE=$(TOOLS-UDM)
TOOLS-UDMPRO=$(TOOLS-UDM)
TOOLS-UXGPRO=$(TOOLS-UDM)
TOOLS-UDR=$(TOOLS-UDM)

TOOLS-UDMXG+=$(TOOLS-CONFIG)
TOOLS-UDMXG+= udm_xg/*

TOOLS-UDMB+=$(TOOLS-CONFIG)
TOOLS-UDMB+= udm_b/*

TOOLS-UDMLITE+=$(TOOLS-CONFIG)
TOOLS-UDMLITE+= udm/*

TOOLS-UDMPRO-SE=$(TOOLS-UDM)

# Project target
$(eval $(call ProductImage,UDM,FCD_$(PRD)_UDM_$(VER)))
$(eval $(call ProductImage,UDMSE,FCD_$(PRD)_UDMSE_$(VER)))
$(eval $(call ProductImage,UDMPRO,FCD_$(PRD)_UDMPRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UXGPRO,FCD_$(PRD)_UXGPRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDMXG,FCD_$(PRD)_UDMXG_$(VER)))
$(eval $(call ProductImage,UDMB,FCD_$(PRD)_UDMB_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDMLITE,FCD_$(PRD)_UDMLITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDR,FCD_$(PRD)_UDR_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UDMPRO-SE,FCD_$(PRD)_UDMPRO-SE_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,UDM,FCD_$(PRD)_UDM_$(VER)))
$(eval $(call ProductCompress,UDMSE,FCD_$(PRD)_UDMSE_$(VER)))
$(eval $(call ProductCompress,UDMPRO,FCD_$(PRD)_UDMPRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UXGPRO,FCD_$(PRD)_UXGPRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDMXG,FCD_$(PRD)_UDMXG_$(VER)))
$(eval $(call ProductCompress,UDMB,FCD_$(PRD)_UDMB_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDMLITE,FCD_$(PRD)_UDMLITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDR,FCD_$(PRD)_UDR_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UDMPRO-SE,FCD_$(PRD)_UDMPRO-SE_$(VER)_$(FWVER)))
