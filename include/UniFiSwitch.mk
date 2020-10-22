
# Images

IMAGE-USW-PRO= \
    images/eb36* \
    images/eb37* \
    images/eb67* \
    images/eb68* \
    usw-fw/unifiswitch-us24pro* \
    usw-fw/unifiswitch-us48pro* \
    usw-fw/US.bcm5616x*

IMAGE-USW-6XG= \
    images/eb23* \
    usw-fw/unifiswitch-6xg150-* \
    usw-fw/unifiswitch-us24pro* \
    usw-fw/US.bcm5616x*

IMAGE-USW-FLEX= \
    images/ed10* \
    usw-fw/unifiswitch-usflex-* \
    usw-fw/unifiswitch-mt7621-* \
    usw-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    usw-fw/MFG.us-flex.BL_gd9df1cea.UAP_4be38fd.image \
    usw-fw/US.mt7621.*

IMAGE-ULS-RPS= \
    images/ed11* \
    usw-fw/unifiswitch-ulsrps-* \
    usw-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    usw-fw/unifi-v1.1.2.71-gd9df1cea_usw-mt7621-16MB_u-boot.bin \
    usw-fw/US.mt7621.*

IMAGE-USW-16-24-48= \
    images/ed20* \
    images/ed21* \
    images/ed22* \
    images/ed23* \
    images/ed24* \
    images/ed25* \
    usw-fw/unifiswitch-16-* \
    usw-fw/unifiswitch-24-* \
    usw-fw/unifiswitch-48-* \
    usw-fw/unifiswitch-16poe-* \
    usw-fw/unifiswitch-24poe-* \
    usw-fw/unifiswitch-48poe-* \
    usw-fw/US.rtl838x*

IMAGE-USW-LITE= \
    images/ed26* \
    images/ed2a* \
    usw-fw/unifiswitch-lite-16poe-* \
    usw-fw/unifiswitch-lite-8poe-* \
    usw-fw/unifiswitch-16poe-* \
    usw-fw/US.rtl838x*

IMAGE-USW-LEAF= \
    images/f060* \
    usw-fw/usw-leaf* \
    usw-fw/UDC*

IMAGE-USW-SPINE= \
    images/f062* \
    usw-fw/usw-leaf* \
    usw-fw/UDC*

IMAGE-USW-LEAF-PRO= \
    images/f063* \
    usw-fw/usw-leaf* \
    usw-fw/UDC*

IMAGE-USW-FLEX-MINI= \
    images/ed30* \
    usw-fw/unifiswitch-mini-* \
    usw-fw/US.m487.*

IMAGE-USW-EnterpriseXG-24= \
    images/eb29* \
    usw-fw/unifiswitch-enterprise-xg24* \
    usw-fw/US.bcm5617x*

IMAGE-USW-MISSION-CRITICAL= \
    images/ed2c* \
    usw-fw/unifiswitch-mc-* \
    usw-fw/US.rtl838x*

IMAGE-USW-Enterprise-24-PoE= \
    images/eb38* \
    usw-fw/unifiswitch-enterprise-24-poe* \
    usw-fw/unifiswitch-us24pro* \
    usw-fw/US.bcm5616x*

IMAGE-USW-Enterprise-48-PoE= \
    images/eb28* \
    usw-fw/unifiswitch-enterprise-48-poe* \
    usw-fw/US.bcm5617x*

IMAGE-USW-Aggregation= \
    images/ed2d* \
    usw-fw/usw-aggregation-* \
    usw-fw/US.rtl930x*

IMAGE-USW-Aggregation-Pro= \
    images/eb27* \
    usw-fw/unifiswitch-aggpro* \
    usw-fw/US.bcm5617x*

IMAGE-US-GEN1= \
    images/eb10* \
    images/eb18* \
    images/eb21* \
    images/eb30* \
    images/eb31* \
    images/eb60* \
    images/eb62* \
    usw-fw/us-gen1-fw.bin \
    usw-fw/us-gen1-mfg.bin \
    usw-fw/US.bcm5334x.v5.11.0.11599.200422.1002-uboot.bin \
    usw-fw/US.bcm5334x.v5.11.0.11599.200422.1002-uboot-mfg.bin

IMAGE-USW-FLEX-XG= \
    images/ed40* \
    usw-fw/unifiswitch-flex-xg.bin \
    usw-fw/US.mvpj4b*

IMAGE-USW-Enterprise-8-PoE= \
    images/ed41* \
    usw-fw/unifiswitch-flex-xg.bin \
    usw-fw/unifiswitch-enterprise-8-poe.bin \
    usw-fw/US.mvpj4b*

IMAGE-USW+=$(IMAGE-USW-PRO)
IMAGE-USW+=$(IMAGE-USW-6XG)
IMAGE-USW+=$(IMAGE-USW-FLEX)
IMAGE-USW+=$(IMAGE-ULS-RPS)
IMAGE-USW+=$(IMAGE-USW-16-24-48)
IMAGE-USW+=$(IMAGE-USW-LITE)
IMAGE-USW+=$(IMAGE-USW-LEAF)
IMAGE-USW+=$(IMAGE-USW-SPINE)
IMAGE-USW+=$(IMAGE-USW-FLEX-MINI)
IMAGE-USW+=$(IMAGE-USW-EnterpriseXG-24)
IMAGE-USW+=$(IMAGE-USW-MISSION-CRITICAL)
IMAGE-USW+=$(IMAGE-USW-Enterprise-24-PoE)
IMAGE-USW+=$(IMAGE-USW-Enterprise-48-PoE)
IMAGE-USW+=$(IMAGE-USW-Aggregation)
IMAGE-USW+=$(IMAGE-USW-Aggregation-Pro)
IMAGE-USW+=$(IMAGE-US-GEN1)
IMAGE-USW+=$(IMAGE-USW-FLEX-XG)
IMAGE-USW+=$(IMAGE-USW-Enterprise-8-PoE)


# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiSwitch
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

TOOLS-USW-16-24-48+=$(TOOLS-USW)
TOOLS-USW-16-24-48+= \
    usw_rtl838x/helper_RTL838x

TOOLS-USW-LITE+=$(TOOLS-USW)
TOOLS-USW-LITE+= \
    usw_rtl838x/helper_RTL838x

TOOLS-USW-LEAF=$(TOOLS-USW)
TOOLS-USW-LEAF+= \
    usw_leaf/create_preload.sh \
    usw_leaf/decrypt.pyc \
    usw_leaf/fake-leaf.bin \
    usw_leaf/fake-spine.bin \
    usw_leaf/fwdiag-ssd.sh \
    usw_leaf/helper_AL324_release_udc \
    usw_leaf/__init__.py \
    usw_leaf/uswleaf-decrypt \

TOOLS-USW-SPINE=$(TOOLS-USW)
# the tools for the USW-SPINE are almost identical to the USW-LEAF
TOOLS-USW-SPINE+=$(TOOLS-USW-LEAF)

TOOLS-USW-LEAF-PRO=$(TOOLS-USW)
# the tools for the USW-SPINE are almost identical to the USW-LEAF
TOOLS-USW-LEAF-PRO+=$(TOOLS-USW-LEAF)

TOOLS-USW-6XG=$(TOOLS-USW)
TOOLS-USW-PRO=$(TOOLS-USW)
TOOLS-USW-FLEX=$(TOOLS-USW)

TOOLS-ULS-RPS=$(TOOLS-USW)
TOOLS-ULS-RPS+= \
    uls_rps/burnin.sh \
    uls_rps/burnin.cfg \
    uls_rps/system.cfg.burnin \
    uls_rps/ubidiag \
    uls_rps/uls_get_power_status_fcd.sh \
    uls_rps/uls_power.sh

TOOLS-USW-FLEX-MINI=$(TOOLS-USW)
TOOLS-USW-FLEX-MINI+= \
    usw_mini/x86-4k-ee

TOOLS-USW-EnterpriseXG-24=$(TOOLS-USW)

TOOLS-USW-MISSION-CRITICAL=$(TOOLS-USW)
TOOLS-USW-MISSION-CRITICAL+= \
    usw_rtl838x/helper_RTL838x

TOOLS-USW-Aggregation=$(TOOLS-USW)
TOOLS-USW-Aggregation+= \
    usw_rtl838x/helper_RTL838x

TOOLS-USW-Aggregation-Pro=$(TOOLS-USW)

TOOLS-USW-Enterprise-24-PoE=$(TOOLS-USW)
TOOLS-USW-Enterprise-48-PoE=$(TOOLS-USW)

TOOLS-USW-FLEX-XG=$(TOOLS-USW)
TOOLS-USW-FLEX-XG+= \
    usw_flex_xg/helper*

TOOLS-USW-Enterprise-8-PoE=$(TOOLS-USW)
TOOLS-USW-Enterprise-8-PoE+= \
    usw_enterprise_8_poe/helper*

# ALL
TOOLS-USW+=$(TOOLS-CONFIG)

TOOLS-US-GEN1+=$(TOOLS-USW)

# Project target

$(eval $(call ProductImage,USW,FCD_$(PRD)_USW-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductImage,US-GEN1,FCD_$(PRD)_US-GEN1-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-6XG,FCD_$(PRD)_USW-6XG_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-PRO,FCD_$(PRD)_USW-PRO-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-FLEX,FCD_$(PRD)_USW-FLEX_$(VER)_$(FWVER)))
$(eval $(call ProductImage,ULS-RPS,FCD_$(PRD)_ULS-RPS_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-16-24-48,FCD_$(PRD)_USW-16-24-48_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-LITE,FCD_$(PRD)_USW-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-LEAF,FCD_$(PRD)_USW-LEAF_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-LEAF-PRO,FCD_$(PRD)_USW-LEAF-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-SPINE,FCD_$(PRD)_USW-SPINE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-FLEX-MINI,FCD_$(PRD)_USW-FLEX-MINI_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-EnterpriseXG-24,FCD_$(PRD)_USW-EnterpriseXG-24_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-MISSION-CRITICAL,FCD_$(PRD)_USW-MISSION-CRITICAL_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-Enterprise-24-PoE,FCD_$(PRD)_USW-Enterprise-24-PoE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-Enterprise-48-PoE,FCD_$(PRD)_USW-Enterprise-48-PoE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-Aggregation,FCD_$(PRD)_USW-Aggregation_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-Aggregation-Pro,FCD_$(PRD)_USW-Aggregation-Pro_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-FLEX-XG,FCD_$(PRD)_USW-FLEX-XG_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USW-Enterprise-8-PoE,FCD_$(PRD)_USW-Enterprise-8-PoE_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,USW,FCD_$(PRD)_USW-ALL_$(VER)))
$(eval $(call ProductCompress,US-GEN1,FCD_$(PRD)_US-GEN1-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-6XG,FCD_$(PRD)_USW-6XG_$(VER)))
$(eval $(call ProductCompress,USW-PRO,FCD_$(PRD)_USW-PRO-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-FLEX,FCD_$(PRD)_USW-FLEX_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,ULS-RPS,FCD_$(PRD)_ULS-RPS_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-16-24-48,FCD_$(PRD)_USW-16-24-48_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-LITE,FCD_$(PRD)_USW-LITE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-LEAF,FCD_$(PRD)_USW-LEAF_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-SPINE,FCD_$(PRD)_USW-SPINE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-FLEX-MINI,FCD_$(PRD)_USW-FLEX-MINI_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-EnterpriseXG-24,FCD_$(PRD)_USW-EnterpriseXG-24_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-MISSION-CRITICAL,FCD_$(PRD)_USW-MISSION-CRITICAL_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-Enterprise-24-PoE,FCD_$(PRD)_USW-Enterprise-24-PoE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-Enterprise-48-PoE,FCD_$(PRD)_USW-Enterprise-48-PoE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-Aggregation,FCD_$(PRD)_USW-Aggregation_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-Aggregation-Pro,FCD_$(PRD)_USW-Aggregation-Pro_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-FLEX-XG,FCD_$(PRD)_USW-FLEX-XG_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USW-Enterprise-8-PoE,FCD_$(PRD)_USW-Enterprise-8-PoE_$(VER)_$(FWVER)))
