
# Images

IMAGE-UDM-BASIC= \
    udm-fw/ubnt-upgrade-compat.tgz

IMAGE-UDM+=$(IMAGE-UDM-BASIC)
IMAGE-UDM+= \
    images/ea11* \
    udm-fw/ubnt_udm_all_rev1_boot.img \
    udm-fw/uImage.r \
    udm-fw/UDM.alpinev2.v1.0.26.c4175d3.190902.1403.bin

IMAGE-UDMSE+=$(IMAGE-UDM-BASIC)
IMAGE-UDMSE+= \
    images/ea13* \
    udm-fw/ubnt_udm_all_rev1_boot.img \
    udm-fw/uImage.r \
    udm-fw/UDM.alpinev2.v1.0.30+builder.1762.cfb07db.190916.1318.bin

IMAGE-UDMPRO+=$(IMAGE-UDM-BASIC)
IMAGE-UDMPRO+= \
    images/ea15* \
    udm-fw/ubnt_udm_all_rev1_boot.img \
    udm-fw/uImage.r \
    udm-fw/UDM.alpinev2.v1.0.31+builder.1754.7418b9d.190918.0858.bin

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
    images/ec28* \
    udm-fw/uImage-LoCo

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiDream
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# FCD images repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-image.git

UDM_FCDIMG_HASH=
UDMSE_FCDIMG_HASH=995cc72c28a126be68aeddc3510a16d64cd25096
UDMPRO_FCDIMG_HASH=f1897acab4249814e5e08065708655df8d3e1aaa
UDMXG_FCDIMG_HASH=
UDMB_FCDIMG_HASH=
UDMLOCO_FCDIMG_HASH=

FCDIMG_VER=

# UBNTLIB repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-ubntlib.git

UDM_UBNTLIB_HASH=
UDMSE_UBNTLIB_HASH=751b6c6a3e79c914f4b32edeb5c4b2193cd262ca
UDMPRO_UBNTLIB_HASH=751b6c6a3e79c914f4b32edeb5c4b2193cd262ca
UDMXG_UBNTLIB_HASH=
UDMB_UBNTLIB_HASH=
UDMLOCO_UBNTLIB_HASH=

UBNTLIB_VER=

# TOOL repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-tools.git

UDM_TOOL_HASH=
UDMSE_TOOL_HASH=1a1436298c288312e2152d1baf0f6af02c9424b3
UDMPRO_TOOL_HASH=4cfbf58ab33b03ad71f630fa7d3c08bc1a8e9f6a
UDMXG_TOOL_HASH=
UDMB_TOOL_HASH=
UDMLOCO_TOOL_HASH=

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/helper_UNIFI_MT7621_release

# Project specific tools

TOOLS-UDM+=$(TOOLS-CONFIG)
TOOLS-UDM+= udm/*

TOOLS-UDMSE=$(TOOLS-UDM)
TOOLS-UDMPRO=$(TOOLS-UDM)

TOOLS-UDMXG+=$(TOOLS-CONFIG)
TOOLS-UDMXG+= udm_xg/*

TOOLS-UDMB+=$(TOOLS-CONFIG)
TOOLS-UDMB+= udm_b/*

TOOLS-UDMLOCO+=$(TOOLS-CONFIG)
TOOLS-UDMLOCO+= udm/*

# Project target

$(eval $(call ProductImage,UDM,FCD-UDM-$(VER)))
$(eval $(call ProductImage,UDMSE,FCD-UDMSE-$(VER)))
$(eval $(call ProductImage,UDMPRO,FCD-UDMPRO-$(VER)))
$(eval $(call ProductImage,UDMXG,FCD-UDMXG-$(VER)))
$(eval $(call ProductImage,UDMB,FCD-UDMB-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UDMLOCO,FCD-UDMLOCO-$(VER)-$(FWVER)))
