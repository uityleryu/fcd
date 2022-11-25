
# Images

IMAGE-GBE= \
    images/dc9* \
    images/dca* \
    am-fw/GBE.* \
    am-fw/GP.* \
    am-fw/ubnthd-u-boot.rom \
    am-fw/gigabeam*

IMAGE-PRISMAP= \
    images/dc9* \
    am-fw/XC.*

IMAGE-ACB-SERIES= \
    images/e8f8* \
    am-fw/u-boot-ar934x-aic.bin \
    am-fw/u-boot-art-ar934x-aic.bin \
    am-fw/u-boot-art-qca953x-aic.bin \
    am-fw/u-boot-qca953x-aic.bin

IMAGE-AC-SERIES= \
    images/e1f5* images/e3d5* images/e3f5* images/e4f5* \
    images/e5f5* images/e6f5* images/e7f5* images/e8f5* \
    images/e9f5* images/e7e5* images/e8e5* images/e2f2* \
    images/e4f2* images/e3f3* images/e3d6* images/e3d7* \
    images/e3d8* images/e7e6* images/e7f7* images/e7f9* \
    images/e7e7* images/e7e9* images/e7e8* images/e7fa* \
    images/e7fc* images/e7fb* images/e2c5* images/e4f3* \
    images/e2f3* images/e3d9* images/e2c7* images/e7fd* \
    images/e7fe* images/e7ff* \
    am-fw/u-boot-ar934x.bin \
    am-fw/u-boot-art-ar934x.bin \
    am-fw/u-boot-qca955x.bin \
    am-fw/u-boot-art-qca955x.bin \
    am-fw/QCA955X_QCA9882_AR8033_V08.img \
    am-fw/WA.ar934x--LSDK-10.1.389__ubnt-wasp-peregrine-5G-std-16M_V4.img \
    am-fw/WA.ar934x-LSDK-ART2_815-NBE-5AC-G2-Wasp-16M-V4.img \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V1.img \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V3.img \
    am-fw/WA.ar934x-LSDK-ART-NBE-2AC-13-16M-V1.img \
    am-fw/XC.qca955x-LSDK-ART-BASESTATION-G2-16M-V2.img \
    am-fw/XC.qca955x-LSDK-ART-Rocket-2AC-HSR-G2-16M-V4.img \
    am-fw/XC.qca955x--V2---LSDK-10.1.389__ubnt-scorpion-peregrine-5G-std-16M.img \
    am-fw/2WA.v8.7.11.46972.220614.0419.bin \
    am-fw/2XC.v8.7.11.46972.220614.0427.bin \
    am-fw/WA.v8.7.11.46972.220614.0420.bin \
    am-fw/XC.v8.7.11.46972.220614.0419.bin \
    am-fw/WA.v8.7.5-alpha.45137.210419.1121.bin \
    am-fw/UBNT_WA.bin \
    am-fw/UBNT_2WA.bin \
    am-fw/UBNT_XC.bin \
    am-fw/UBNT_2XC.bin \
    am-fw/AR934X_ART_UB.bin \
    am-fw/AR934X_UB.bin \
    am-fw/QCA955X_ART_UB.bin \
    am-fw/QCA955X_UB.bin \
    am-fw/WA.ar934x-LSDK-ART-LBE-AC-90-BR-16M-V1.img \
    am-fw/WA.v8.7.5-alpha2.45300.210507.1454.bin \
    am-fw/LSDK-10.1.389-AR9342-QCA988X-AR8035-16M_V3.img \
    am-fw/XC.qca955x-LSDK-ART-ROCKET-2AC-HSR-16M-V3.img \
    am-fw/XC.qca955x.LSDK-ART.NBE-5AC-G2-v2.img \
    am-fw/LSDK-10.1.389-AR9342-QCA988X-AR8035-16M_V3.img \
    am-fw/QCA955X_QCA9882_AR8033_HSR_V07.bin \
    am-fw/XC.qca955x--V1---LSDK-10.1.389__ubnt-scorpion-peregrine-5G-std-16M.img \
    am-fw/LSDK-10.1.389-AR9342-QCA988X-AR8035-16M_V3.bin \
    am-fw/openwrt-ath79-lbe-5ac-xr-initramfs-kernel-v2.bin

IMAGE-M-SERIES= \
    images/e865* \
    amm-fw/*

IMAGE-AIRMAX+=$(IMAGE-GBE)
IMAGE-AIRMAX+=$(IMAGE-PRISMAP)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=airMAX
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-GBE= \
    am/cfg_part.bin \
    am/helper_IPQ40xx \
    am/am_dummy_cal.bin \
    am/id_rsa \
    am/id_rsa.pub

TOOLS-PRISMAP= \
    am/cfg_part_qca9557.bin \
    am/fl_lock \
    am/helper_ARxxxx_11ac \
    am/id_rsa \
    am/id_rsa.pub

TOOLS-60G-LAS= \
    common/helper_UNIFI_MT7621_release \

TOOLS-AC-SERIES+=$(TOOLS-CONFIG)
TOOLS-AC-SERIES+= \
    am/helper_ARxxxx_11ac_20210329 \
    am/cfg_part_ac_series.bin \
    am/id_rsa \
    am/id_rsa.pub \
    am/fl_lock_11ac_re

TOOLS-ACB-SERIES= \
    am/helper_ARxxxx_aircube \
    am/aic_cred_gen.sh

TOOLS-M-SERIES+=$(TOOLS-CONFIG)
TOOLS-M-SERIES+= \
    am_m/*

# Assign common tool for every model
TOOLS-GBE+=$(TOOLS-CONFIG)
TOOLS-PRISMAP+=$(TOOLS-CONFIG)
TOOLS-60G-LAS+=$(TOOLS-CONFIG)

# Assign UAP series tools
TOOLS-AIRMAX+=$(TOOLS-GBE)
TOOLS-AIRMAX+=$(TOOLS-PRISMAP)
TOOLS-AIRMAX+=$(TOOLS-60G-LAS)

# Project target

$(eval $(call ProductImage,AIRMAX,FCD_$(PRD)_AIRMAX-ALL_$(VER)))
$(eval $(call ProductImage,GBE,FCD_$(PRD)_GBE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,PRISMAP,FCD_$(PRD)_PRISMAP_$(VER)_$(FWVER)))
$(eval $(call ProductImage,60G-LAS,FCD_$(PRD)_60G-LAS_$(VER)_$(FWVER)))
$(eval $(call ProductImage,AC-SERIES,FCD_$(PRD)_AC-SERIES_$(VER)_$(FWVER)))
$(eval $(call ProductImage,ACB-SERIES,FCD_$(PRD)_ACB-SERIES_$(VER)_$(FWVER)))
$(eval $(call ProductImage,M-SERIES,FCD_$(PRD)_M-SERIES_$(VER)_$(FWVER)))

# ==================================================================================================
# Single product definition
# ==================================================================================================

$(eval $(call ProductCompress2,00348_e1f5))
$(eval $(call ProductCompress2,00402_e8e5))
$(eval $(call ProductCompress2,00549_e2c5))
$(eval $(call ProductCompress2,00592_e2c7))
$(eval $(call ProductCompress2,00570_e2f3))
$(eval $(call ProductCompress2,00569_e4f3))
$(eval $(call ProductCompress2,00346_e4f5))
$(eval $(call ProductCompress2,00363_e5f5))
$(eval $(call ProductCompress2,00421_e5f5))
$(eval $(call ProductCompress2,00429_e5f5))
$(eval $(call ProductCompress2,00427_e3d5))
$(eval $(call ProductCompress2,00477_e3d5))
$(eval $(call ProductCompress2,00492_e3d6))
$(eval $(call ProductCompress2,00559_e3d6))
$(eval $(call ProductCompress2,00513_e7f6))
$(eval $(call ProductCompress2,00485_e7f7))
$(eval $(call ProductCompress2,00526_e7e7))
$(eval $(call ProductCompress2,00545_e7e9))
$(eval $(call ProductCompress2,00546_e7f8))
$(eval $(call ProductCompress2,00497_e7f9))
$(eval $(call ProductCompress2,00552_e7fa))
$(eval $(call ProductCompress2,00554_e7fb))
$(eval $(call ProductCompress2,00556_e7fc))
$(eval $(call ProductCompress2,00643_e7fe))
$(eval $(call ProductCompress2,00962_e7ff))
$(eval $(call ProductCompress2,00488_e8f8))
$(eval $(call ProductCompress2,00717_a918))
$(eval $(call ProductCompress2,00714_dc9a))
$(eval $(call ProductCompress2,00494_e3d7))
$(eval $(call ProductCompress2,00825_dca0))
$(eval $(call ProductCompress2,00697_dc97))
$(eval $(call ProductCompress2,00709_dc99))
$(eval $(call ProductCompress2,00406_e7e5))
$(eval $(call ProductCompress2,01073_a659))
$(eval $(call ProductCompress2,00991_a660))
$(eval $(call ProductCompress2,01079_a661))
$(eval $(call ProductCompress2,01099_a662))
$(eval $(call ProductCompress2,01111_a663))
$(eval $(call ProductCompress2,01211_a670))
$(eval $(call ProductCompress2,01227_a673))
$(eval $(call ProductCompress2,AIRMAX_AC-SERIES))
$(eval $(call ProductCompress2,AIRMAX_AX-SERIES))
