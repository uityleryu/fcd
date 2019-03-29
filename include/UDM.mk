# UDM
IMAGE-UDM-BASIC= \
    udm-fw/ubnt_udm_all_v1_sigined_20181017_boot.img \
    udm-fw/ubnt-upgrade-compat.tgz \
    udm-fw/uImage-0.9.4-a9df305.r \
    udm-fw/uImage-0.9.5.r

IMAGE-UDM+=$(IMAGE-UDM-BASIC)
IMAGE-UDM+= \
    images/ea11* \
    udm-fw/UDM.alpinev2.v0.9.5.f18c4d1.190128.1425.bin \

IMAGE-UDMSE+=$(IMAGE-UDM-BASIC)
IMAGE-UDMSE+= \
    images/ea13* \
    udm-fw/UDM.alpinev2.v0.10.1.879a225.190311.0833.bin

IMAGE-UDMPRO+=$(IMAGE-UDM-BASIC)
IMAGE-UDMPRO+= \
    images/ea15* \
    udm-fw/UDM.alpinev2.v0.10.1.879a225.190311.0833.bin

IMAGE-UDMXG=
#IMAGE-UDMXG=images/ea17* \
#            udm-fw/*

IMAGE-UDMB= \
    images/ec25* \
    udm-fw/udm-b-* \
    udm-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    udm-fw/unifi-v1.0.9.57-gd7bab423_uap-mt7621-32MB_u-boot.bin \
    udm-fw/BZ.mt7621.*

IMAGE-UDMLOCO= \

IMAGE-UDMALL+=$(IMAGE-UDM)
IMAGE-UDMALL+=$(IMAGE-UDMSE)
IMAGE-UDMALL+=$(IMAGE-UDMPRO)
#IMAGE-UDMALL+=$(IMAGE-UDMXG)

DIAG_MODEL=udm
DIAG_UI_MODEL=UniFiDream
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

UPYFCD_VER=
FCDIMG_VER=
UBNTLIB_VER=
TOOL_VER=

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
