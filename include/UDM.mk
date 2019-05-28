# UDM
IMAGE-UDM-BASIC= \
    udm-fw/ubnt-upgrade-compat.tgz 

IMAGE-UDM+=$(IMAGE-UDM-BASIC)
IMAGE-UDM+= \
    images/ea11* \
    udm-fw/ubnt_udm_all_v1_sigined_20181017_boot.img \
    udm-fw/uImage-0.9.5.r \
    udm-fw/UDM.alpinev2.v0.11.5.80d6569.190520.0920.bin

IMAGE-UDMSE+=$(IMAGE-UDM-BASIC)
IMAGE-UDMSE+= \
    images/ea13* \
	udm-fw/ubnt_udm_all_v1_sigined_20181017_boot.img \
	udm-fw/uImage-0.9.4-a9df305.r \
    udm-fw/UDM.alpinev2.v0.12.0-dummy+builder.1263.f01062a.190524.2138.bin

IMAGE-UDMPRO+=$(IMAGE-UDM-BASIC)
IMAGE-UDMPRO+= \
    images/ea15* \
    udm-fw/udm_pro_hw7_boot_02d0578.img \
    udm-fw/uImage.r \
    udm-fw/UDM.alpinev2.v0.11.0.3e8dcdc.190503.0829.bin

IMAGE-UDMXG=
#IMAGE-UDMXG=images/ea17* \
#            udm-fw/*

IMAGE-UDMB= \
    images/ec25* \
    udm-fw/udm-b-* \
    udm-fw/Unifi-ONE-* \
    udm-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    udm-fw/unifi-v1.0.9.57-gd7bab423_uap-mt7621-32MB_u-boot.bin \
    udm-fw/BZ.mt7621.*

IMAGE-UDMLOCO= \

IMAGE-UDMALL+=$(IMAGE-UDM)
IMAGE-UDMALL+=$(IMAGE-UDMSE)
IMAGE-UDMALL+=$(IMAGE-UDMPRO)
#IMAGE-UDMALL+=$(IMAGE-UDMXG)

DIAG_UI_MODEL=UniFiDream
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

UPYFCD_VER = 
FCDIMG_VER = 0c6e6da81274de2885e47ffebfe4aa023daa935f
UBNTLIB_VER= e485b83efa89f36b25a67aba6f4216c75862042c
TOOL_VER   = caafecb9b0bdd72219b3750417b7a76ae2e3848e

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf

TOOLS-UDM+=$(TOOLS-CONFIG)
TOOLS-UDM+= udm/*

TOOLS-UDMSE=$(TOOLS-UDM)
TOOLS-UDMPRO=$(TOOLS-UDM)

TOOLS-UDMXG+=$(TOOLS-CONFIG)
TOOLS-UDMXG+= udm_xg/*

TOOLS-UDMB+=$(TOOLS-CONFIG)
TOOLS-UDMB+= udm_b/*

TOOLS-UDMLOCO+=$(TOOLS-CONFIG)
TOOLS-UDMLOCO+= udm_loco/*

TOOLS-UDMALL+=$(TOOLS-UDM)
#TOOLS-UDMALL+=$(TOOLS-UDMXG)

$(eval $(call ProductImage,UDM,FCD-UDM-$(VER)))
$(eval $(call ProductImage,UDMSE,FCD-UDMSE-$(VER)))
$(eval $(call ProductImage,UDMPRO,FCD-UDMPRO-$(VER)))
$(eval $(call ProductImage,UDMXG,FCD-UDMXG-$(VER)))
$(eval $(call ProductImage,UDMB,FCD-UDMB-$(VER)))
$(eval $(call ProductImage,UDMLOCO,FCD-UDMLOCO-$(VER)))
$(eval $(call ProductImage,UDMALL,FCD-UDMALL-$(VER)))
