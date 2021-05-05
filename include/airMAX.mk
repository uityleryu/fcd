
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
    am-fw/2WA.v8.7.2.44330.210106.1336.bin \
    am-fw/WA.v8.7.2.44330.210106.1337.bin \
    am-fw/2XC.v8.7.2.44330.210106.1337.bin \
    am-fw/XC.v8.7.2.44330.210106.1337.bin \
    am-fw/WA.v8.7.4.45112.210415.1103.bin \
    am-fw/XC.v8.7.4.45112.210415.1103.bin \
    am-fw/2WA.v8.7.4.45112.210415.1103.bin \
    am-fw/2XC.v8.7.4.45112.210415.1103.bin \
    am-fw/WA.v8.7.5-alpha.45137.210419.1121.bin \
    am-fw/UBNT_WA.bin \
    am-fw/UBNT_2WA.bin \
    am-fw/UBNT_XC.bin \
    am-fw/UBNT_2XC.bin \
    am-fw/AR934X_ART_UB.bin \
    am-fw/AR934X_UB.bin \
    am-fw/QCA955X_ART_UB.bin \
    am-fw/QCA955X_UB.bin \

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

TOOLS-ACB-SERIES= \
    am/helper_ARxxxx_aircube \
    am/aic_cred_gen.sh

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

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,AIRMAX,FCD_$(PRD)_AIRMAX-ALL_$(VER)))
$(eval $(call ProductCompress,GBE,FCD_$(PRD)_GBE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,PRISMAP,FCD_$(PRD)_PRISMAP_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,60G-LAS,FCD_$(PRD)_60G-LAS_$(VER)_$(FWVER),$(ALL)))
$(eval $(call ProductCompress,AC-SERIES,FCD_$(PRD)_AC-SERIES_$(VER)_$(FWVER),$(ALL)))


# ==================================================================================================
# Single product definition
# ==================================================================================================

IMAGE-AR9342-AC-SERIES= \
    am-fw/u-boot-ar934x.bin \
    am-fw/u-boot-art-ar934x.bin \
    am-fw/AR934X_ART_UB.bin \
    am-fw/AR934X_UB.bin \

IMAGE-QCA955x-AC-SERIES= \
    am-fw/u-boot-qca955x.bin \
    am-fw/u-boot-art-qca955x.bin \
    am-fw/QCA955X_ART_UB.bin \
    am-fw/QCA955X_UB.bin \

IMAGE-00348-e1f5=$(IMAGE-QCA955x-AC-SERIES)
IMAGE-00348-e1f5+= \
    images/e1f5* \
    am-fw/XC.v8.7.4.45112.210415.1103.bin \
    am-fw/QCA955X_QCA9882_AR8033_V08.img \
    am-fw/UBNT_XC.bin

IMAGE-00549-e2c5=$(IMAGE-AR9342-AC-SERIES)
IMAGE-00549-e2c5+= \
    images/e2c5* \
    am-fw/WA.v8.7.4.45112.210415.1103.bin \
    am-fw/WA.ar934x--LSDK-10.1.389__ubnt-wasp-peregrine-5G-std-16M_V4.img \
    am-fw/UBNT_WA.bin

IMAGE-00592-e2c7=$(IMAGE-AR9342-AC-SERIES)
IMAGE-00592-e2c7+= \
    images/e2c7* \
    am-fw/WA.v8.7.4.45112.210415.1103.bin \
    am-fw/WA.ar934x--LSDK-10.1.389__ubnt-wasp-peregrine-5G-std-16M_V4.img \
    am-fw/UBNT_WA.bin

IMAGE-00570-e2f3=$(IMAGE-QCA955x-AC-SERIES)
IMAGE-00570-e2f3+= \
    images/e2f3* \
    am-fw/2XC.v8.7.4.45112.210415.1102.bin \
    am-fw/XC.qca955x-LSDK-ART-Rocket-2AC-HSR-G2-16M-V4.img \
    am-fw/UBNT_2XC.bin

IMAGE-00569-e4f3=$(IMAGE-AR9342-AC-SERIES)
IMAGE-00569-e4f3+= \
    images/e4f3* \
    am-fw/2WA.v8.7.4.45112.210415.1103.bin \
    am-fw/WA.ar934x-LSDK-ART-NBE-2AC-13-16M-V1.img \
    am-fw/UBNT_2WA.bin

IMAGE-00346-e4f5=$(IMAGE-QCA955x-AC-SERIES)
IMAGE-00346-e4f5+= \
    images/e4f5* \
    am-fw/XC.v8.7.4.45112.210415.1103.bin \
    am-fw/QCA955X_QCA9882_AR8033_V08.img \
    am-fw/UBNT_XC.bin

# System ID: e5f5 +++++++++++++++++++++++++++++++
IMAGE-00363-e5f5=$(IMAGE-QCA955x-AC-SERIES)
IMAGE-00363-e5f5+= \
    images/e5f5* \
    am-fw/XC.v8.7.4.45112.210415.1103.bin \
    am-fw/XC.qca955x--V2---LSDK-10.1.389__ubnt-scorpion-peregrine-5G-std-16M.img \
    am-fw/UBNT_XC.bin

IMAGE-00421-e5f5=$(IMAGE-QCA955x-AC-SERIES)
IMAGE-00421-e5f5+= \
    images/e5f5* \
    am-fw/XC.v8.7.4.45112.210415.1103.bin \
    am-fw/XC.qca955x--V2---LSDK-10.1.389__ubnt-scorpion-peregrine-5G-std-16M.img \
    am-fw/UBNT_XC.bin

IMAGE-00429-e5f5=$(IMAGE-QCA955x-AC-SERIES)
IMAGE-00429-e5f5+= \
    images/e5f5* \
    am-fw/XC.v8.7.4.45112.210415.1103.bin \
    am-fw/XC.qca955x--V2---LSDK-10.1.389__ubnt-scorpion-peregrine-5G-std-16M.img \
    am-fw/UBNT_XC.bin
# System ID: e5f5 +++++++++++++++++++++++++++++++

# System ID: e3d5 +++++++++++++++++++++++++++++++
IMAGE-00427-e3d5=$(IMAGE-QCA955x-AC-SERIES)
IMAGE-00427-e3d5+= \
    images/e3d5* \
    am-fw/XC.v8.7.4.45112.210415.1103.bin \
    am-fw/XC.qca955x--V2---LSDK-10.1.389__ubnt-scorpion-peregrine-5G-std-16M.img \
    am-fw/UBNT_XC.bin

IMAGE-00477-e3d5=$(IMAGE-QCA955x-AC-SERIES)
IMAGE-00477-e3d5+= \
    images/e3d5* \
    am-fw/XC.v8.7.4.45112.210415.1103.bin \
    am-fw/XC.qca955x--V2---LSDK-10.1.389__ubnt-scorpion-peregrine-5G-std-16M.img \
    am-fw/UBNT_XC.bin
# System ID: e3d5 +++++++++++++++++++++++++++++++

# System ID: e3d6 +++++++++++++++++++++++++++++++
IMAGE-00492-e3d6=$(IMAGE-AR9342-AC-SERIES)
IMAGE-00492-e3d6+= \
    images/e3d6* \
    am-fw/WA.v8.7.4.45112.210415.1103.bin \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V1.img \
    am-fw/UBNT_WA.bin

IMAGE-00559-e3d6=$(IMAGE-AR9342-AC-SERIES)
IMAGE-00559-e3d6+= \
    images/e3d6* \
    am-fw/WA.v8.7.4.45112.210415.1103.bin \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V1.img \
    am-fw/UBNT_WA.bin
# System ID: e3d6 +++++++++++++++++++++++++++++++

IMAGE-00513-e7e6=$(IMAGE-QCA955x-AC-SERIES)
IMAGE-00513-e7e6+= \
    images/e7e6* \
    am-fw/XC.v8.7.4.45112.210415.1103.bin \
    am-fw/XC.qca955x-LSDK-ART-BASESTATION-G2-16M-V2.img \
    am-fw/UBNT_XC.bin

IMAGE-00526-e7e7=$(IMAGE-QCA955x-AC-SERIES)
IMAGE-00526-e7e7+= \
    images/e7e7* \
    am-fw/XC.v8.7.4.45112.210415.1103.bin \
    am-fw/XC.qca955x-LSDK-ART-BASESTATION-G2-16M-V2.img \
    am-fw/UBNT_XC.bin

IMAGE-00545-e7e9=$(IMAGE-QCA955x-AC-SERIES)
IMAGE-00545-e7e9+= \
    images/e7e7* \
    am-fw/XC.v8.7.4.45112.210415.1103.bin \
    am-fw/XC.qca955x-LSDK-ART-BASESTATION-G2-16M-V2.img \
    am-fw/UBNT_XC.bin

IMAGE-00546-e7e8=$(IMAGE-QCA955x-AC-SERIES)
IMAGE-00546-e7e8+= \
    images/e7e8* \
    am-fw/XC.v8.7.4.45112.210415.1103.bin \
    am-fw/XC.qca955x-LSDK-ART-BASESTATION-G2-16M-V2.img \
    am-fw/UBNT_XC.bin

IMAGE-00497-e7f9=$(IMAGE-AR9342-AC-SERIES)
IMAGE-00497-e7f9+= \
    images/e7f9* \
    am-fw/WA.v8.7.4.45112.210415.1103.bin \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V1.img \
    am-fw/UBNT_WA.bin

IMAGE-00552-e7fa=$(IMAGE-AR9342-AC-SERIES)
IMAGE-00552-e7fa+= \
    images/e7fa* \
    am-fw/WA.v8.7.4.45112.210415.1103.bin \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V3.img \
    am-fw/UBNT_WA.bin

IMAGE-00554-e7fb=$(IMAGE-AR9342-AC-SERIES)
IMAGE-00553-e7fb+= \
    images/e7fb* \
    am-fw/WA.v8.7.4.45112.210415.1103.bin \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V3.img \
    am-fw/UBNT_WA.bin

IMAGE-00556-e7fc=$(IMAGE-AR9342-AC-SERIES)
IMAGE-00556-e7fc+= \
    images/e7fc* \
    am-fw/WA.v8.7.4.45112.210415.1103.bin \
    am-fw/WA.ar934x-LSDK-ART2_815-NBE-5AC-G2-Wasp-16M-V4.img \
    am-fw/UBNT_WA.bin

IMAGE-00643-e7fe=$(IMAGE-AR9342-AC-SERIES)
IMAGE-00643-e7fe+= \
    images/e7fe* \
    am-fw/WA.v8.7.4.45112.210415.1103.bin \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V1.img \
    am-fw/UBNT_WA.bin

IMAGE-00962-e7ff=$(IMAGE-AR9342-AC-SERIES)
IMAGE-00962-e7ff+= \
    images/e7ff* \
    am-fw/WA.v8.7.5-alpha.45137.210419.1121.bin \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V1.img \
    am-fw/UBNT_WA.bin

IMAGE-00402-e8e5=$(IMAGE-AR9342-AC-SERIES)
IMAGE-00402-e8e5+= \
    images/e8e5* \
    am-fw/WA.v8.7.4.45112.210415.1103.bin \
    am-fw/LSDK-10.1.389-AR9342-QCA988X-AR8035-16M_V3.img \
    am-fw/UBNT_WA.bin

IMAGE-00485-e7f7=$(IMAGE-AR9342-AC-SERIES)
IMAGE-00485-e7f7+= \
    images/e7f7* \
    am-fw/WA.v8.7.4.45112.210415.1103.bin \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V3.img \
    am-fw/UBNT_WA.bin

IMAGE-00488-e8f8= \
    images/e8f8* \
    am-fw/u-boot-ar934x-aic.bin \
    am-fw/u-boot-art-ar934x-aic.bin \
    am-fw/u-boot-art-qca953x-aic.bin \
    am-fw/u-boot-qca953x-aic.bin

# -----------------------------------------------------------------------------------------

TOOLS-COMMON-AC= \
    am/helper_ARxxxx_11ac_20210329 \
    am/cfg_part_ac_series.bin \
    am/id_rsa \
    am/id_rsa.pub \
    am/fl_lock_11ac_re

TOOLS-00348-e1f5=$(TOOLS-COMMON-AC)
TOOLS-00348-e1f5+=$(TOOLS-CONFIG)

TOOLS-00549-e2c5=$(TOOLS-COMMON-AC)
TOOLS-00549-e2c5+=$(TOOLS-CONFIG)

TOOLS-00592-e2c7=$(TOOLS-COMMON-AC)
TOOLS-00592-e2c7+=$(TOOLS-CONFIG)

TOOLS-00570-e2f3=$(TOOLS-COMMON-AC)
TOOLS-00570-e2f3+=$(TOOLS-CONFIG)

TOOLS-00569-e4f3=$(TOOLS-COMMON-AC)
TOOLS-00569-e4f3+=$(TOOLS-CONFIG)

TOOLS-00346-e4f5=$(TOOLS-COMMON-AC)
TOOLS-00346-e4f5+=$(TOOLS-CONFIG)

# System ID: e5f5 +++++++++++++++++++++++++++++++
TOOLS-00363-e5f5=$(TOOLS-COMMON-AC)
TOOLS-00363-e5f5+=$(TOOLS-CONFIG)

TOOLS-00421-e5f5=$(TOOLS-COMMON-AC)
TOOLS-00421-e5f5+=$(TOOLS-CONFIG)

TOOLS-00429-e5f5=$(TOOLS-COMMON-AC)
TOOLS-00429-e5f5+=$(TOOLS-CONFIG)
# System ID: e5f5 +++++++++++++++++++++++++++++++

# System ID: e3d5 +++++++++++++++++++++++++++++++
TOOLS-00427-e3d5=$(TOOLS-COMMON-AC)
TOOLS-00427-e3d5+=$(TOOLS-CONFIG)

TOOLS-00477-e3d5=$(TOOLS-COMMON-AC)
TOOLS-00477-e3d5+=$(TOOLS-CONFIG)
# System ID: e3d5 +++++++++++++++++++++++++++++++

# System ID: e3d6 +++++++++++++++++++++++++++++++
TOOLS-00492-e3d6=$(TOOLS-COMMON-AC)
TOOLS-00492-e3d6+=$(TOOLS-CONFIG)

TOOLS-00559-e3d6=$(TOOLS-COMMON-AC)
TOOLS-00559-e3d6+=$(TOOLS-CONFIG)
# System ID: e3d6 +++++++++++++++++++++++++++++++

TOOLS-00485-e7f7=$(TOOLS-COMMON-AC)
TOOLS-00485-e7f7+=$(TOOLS-CONFIG)

TOOLS-00513-e7f6=$(TOOLS-COMMON-AC)
TOOLS-00513-e7f6+=$(TOOLS-CONFIG)

TOOLS-00526-e7e7=$(TOOLS-COMMON-AC)
TOOLS-00526-e7e7+=$(TOOLS-CONFIG)

TOOLS-00545-e7e9=$(TOOLS-COMMON-AC)
TOOLS-00545-e7e9+=$(TOOLS-CONFIG)

TOOLS-00546-e7f8=$(TOOLS-COMMON-AC)
TOOLS-00546-e7f8+=$(TOOLS-CONFIG)

TOOLS-00497-e7f9=$(TOOLS-COMMON-AC)
TOOLS-00497-e7f9+=$(TOOLS-CONFIG)

TOOLS-00552-e7fa=$(TOOLS-COMMON-AC)
TOOLS-00552-e7fa+=$(TOOLS-CONFIG)

TOOLS-00554-e7fb=$(TOOLS-COMMON-AC)
TOOLS-00554-e7fb+=$(TOOLS-CONFIG)

TOOLS-00643-e7fe=$(TOOLS-COMMON-AC)
TOOLS-00643-e7fe+=$(TOOLS-CONFIG)

TOOLS-00556-e7fc=$(TOOLS-COMMON-AC)
TOOLS-00556-e7fc+=$(TOOLS-CONFIG)

TOOLS-00962-e7ff=$(TOOLS-COMMON-AC)
TOOLS-00962-e7ff+=$(TOOLS-CONFIG)

TOOLS-00488-e8f8= \
    am/helper_ARxxxx_aircube \
    am/aic_cred_gen.sh


# ==================================================================================================
# Product series definition
# ==================================================================================================

IMAGE-AC-SERIES+=$(IMAGE-00348-e1f5)
IMAGE-AC-SERIES+=$(IMAGE-00402-e8e5)
IMAGE-AC-SERIES+=$(IMAGE-00549-e2c5)
IMAGE-AC-SERIES+=$(IMAGE-00592-e2c7)
IMAGE-AC-SERIES+=$(IMAGE-00570-e2f3)
IMAGE-AC-SERIES+=$(IMAGE-00569-e4f3)
IMAGE-AC-SERIES+=$(IMAGE-00346-e4f5)
IMAGE-AC-SERIES+=$(IMAGE-00363-e5f5)
IMAGE-AC-SERIES+=$(IMAGE-00421-e5f5)
IMAGE-AC-SERIES+=$(IMAGE-00429-e5f5)
IMAGE-AC-SERIES+=$(IMAGE-00427-e3d5)
IMAGE-AC-SERIES+=$(IMAGE-00477-e3d5)
IMAGE-AC-SERIES+=$(IMAGE-00492-e3d6)
IMAGE-AC-SERIES+=$(IMAGE-00559-e3d6)
IMAGE-AC-SERIES+=$(IMAGE-00513-e7f6)
IMAGE-AC-SERIES+=$(IMAGE-00485-e7f7)
IMAGE-AC-SERIES+=$(IMAGE-00526-e7e7)
IMAGE-AC-SERIES+=$(IMAGE-00545-e7e9)
IMAGE-AC-SERIES+=$(IMAGE-00546-e7f8)
IMAGE-AC-SERIES+=$(IMAGE-00497-e7f9)
IMAGE-AC-SERIES+=$(IMAGE-00552-e7fa)
IMAGE-AC-SERIES+=$(IMAGE-00554-e7fb)
IMAGE-AC-SERIES+=$(IMAGE-00556-e7fc)
IMAGE-AC-SERIES+=$(IMAGE-00643-e7fe)
IMAGE-AC-SERIES+=$(IMAGE-00962-e7ff)

TOOLS-AC-SERIES+=$(TOOLS-00348-e1f5)
TOOLS-AC-SERIES+=$(TOOLS-00402-e8e5)
TOOLS-AC-SERIES+=$(TOOLS-00549-e2c5)
TOOLS-AC-SERIES+=$(TOOLS-00592-e2c7)
TOOLS-AC-SERIES+=$(TOOLS-00570-e2f3)
TOOLS-AC-SERIES+=$(TOOLS-00569-e4f3)
TOOLS-AC-SERIES+=$(TOOLS-00346-e4f5)
TOOLS-AC-SERIES+=$(TOOLS-00363-e5f5)
TOOLS-AC-SERIES+=$(TOOLS-00421-e5f5)
TOOLS-AC-SERIES+=$(TOOLS-00429-e5f5)
TOOLS-AC-SERIES+=$(TOOLS-00427-e3d5)
TOOLS-AC-SERIES+=$(TOOLS-00477-e3d5)
TOOLS-AC-SERIES+=$(TOOLS-00492-e3d6)
TOOLS-AC-SERIES+=$(TOOLS-00559-e3d6)
TOOLS-AC-SERIES+=$(TOOLS-00513-e7f6)
TOOLS-AC-SERIES+=$(TOOLS-00485-e7f7)
TOOLS-AC-SERIES+=$(TOOLS-00526-e7e7)
TOOLS-AC-SERIES+=$(TOOLS-00545-e7e9)
TOOLS-AC-SERIES+=$(TOOLS-00546-e7e8)
TOOLS-AC-SERIES+=$(TOOLS-00497-e7f9)
TOOLS-AC-SERIES+=$(TOOLS-00552-e7fa)
TOOLS-AC-SERIES+=$(TOOLS-00554-e7fb)
TOOLS-AC-SERIES+=$(TOOLS-00556-e7fc)
TOOLS-AC-SERIES+=$(TOOLS-00643-e7fe)
TOOLS-AC-SERIES+=$(TOOLS-00962-e7ff)

# 00492 and 00559 use the identical PCBA but the ID is different
# So, they share the same system ID
PRODUCT-AC-SERIES+=00348-e1f5
PRODUCT-AC-SERIES+=00402-e8e5
PRODUCT-AC-SERIES+=00549-e2c5
PRODUCT-AC-SERIES+=00592-e2c7
PRODUCT-AC-SERIES+=00570-e2f3
PRODUCT-AC-SERIES+=00569-e4f3
PRODUCT-AC-SERIES+=00346-e4f5
PRODUCT-AC-SERIES+=00363-e5f5
PRODUCT-AC-SERIES+=00421-e5f5
PRODUCT-AC-SERIES+=00429-e5f5
PRODUCT-AC-SERIES+=00427-e3d5
PRODUCT-AC-SERIES+=00477-e3d5
PRODUCT-AC-SERIES+=00492-e3d6
PRODUCT-AC-SERIES+=00559-e3d6
PRODUCT-AC-SERIES+=00513-e7f6
PRODUCT-AC-SERIES+=00485-e7f7
PRODUCT-AC-SERIES+=00526-e7e7
PRODUCT-AC-SERIES+=00545-e7e9
PRODUCT-AC-SERIES+=00546-e7f8
PRODUCT-AC-SERIES+=00497-e7f9
PRODUCT-AC-SERIES+=00552-e7fa
PRODUCT-AC-SERIES+=00554-e7fb
PRODUCT-AC-SERIES+=00556-e7fc
PRODUCT-AC-SERIES+=00643-e7fe
PRODUCT-AC-SERIES+=00962-e7ff

# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,00348-e1f5))
$(eval $(call ProductCompress2,00402-e8e5))
$(eval $(call ProductCompress2,00549-e2c5))
$(eval $(call ProductCompress2,00592-e2c7))
$(eval $(call ProductCompress2,00570-e2f3))
$(eval $(call ProductCompress2,00569-e4f3))
$(eval $(call ProductCompress2,00346-e4f5))
$(eval $(call ProductCompress2,00363-e5f5))
$(eval $(call ProductCompress2,00421-e5f5))
$(eval $(call ProductCompress2,00429-e5f5))
$(eval $(call ProductCompress2,00427-e3d5))
$(eval $(call ProductCompress2,00477-e3d5))
$(eval $(call ProductCompress2,00492-e3d6))
$(eval $(call ProductCompress2,00559-e3d6))
$(eval $(call ProductCompress2,00513-e7f6))
$(eval $(call ProductCompress2,00485-e7f7))
$(eval $(call ProductCompress2,00526-e7e7))
$(eval $(call ProductCompress2,00545-e7e9))
$(eval $(call ProductCompress2,00546-e7f8))
$(eval $(call ProductCompress2,00497-e7f9))
$(eval $(call ProductCompress2,00552-e7fa))
$(eval $(call ProductCompress2,00554-e7fb))
$(eval $(call ProductCompress2,00556-e7fc))
$(eval $(call ProductCompress2,00643-e7fe))
$(eval $(call ProductCompress2,00962-e7ff))
$(eval $(call ProductCompress2,00488-e8f8))
$(eval $(call ProductCompress2,AC-SERIES))
