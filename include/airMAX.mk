
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

IMAGE-LBE-5AC-XR= \
    images/e7ff* \
    am-fw/u-boot-ar934x.bin \
    am-fw/u-boot-art-ar934x.bin \
    am-fw/WA.v8.7.4-beta.44660.210219.1654.bin \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V1.img \
    am-fw/AR934X_ART_UB.bin \
    am-fw/AR934X_UB.bin \

IMAGE-AC-SERIES= \
    images/e1f5* images/e3d5* images/e3f5* images/e4f5* \
    images/e5f5* images/e6f5* images/e7f5* images/e8f5* \
    images/e9f5* images/e7e5* images/e8e5* images/e2f2* \
    images/e4f2* images/e3f3* images/e3d6* images/e3d7* \
    images/e3d8* images/e7e6* images/e7f7* images/e7f9* \
    images/e7e7* images/e7e9* images/e7e8* images/e7fa* \
    images/e7fc* images/e7fb* images/e2c5* images/e4f3* \
    images/e2f3* images/e3d9* images/e2c7* images/e7fd* \
    images/e7fe* images/e7ff*\
    am-fw/u-boot-ar934x.bin \
    am-fw/u-boot-art-ar934x.bin \
    am-fw/u-boot-qca955x.bin \
    am-fw/u-boot-art-qca955x.bin \
    am-fw/LSDK-10.1.389-AR9342-QCA988X-AR8035-16M_V3.bin \
    am-fw/LSDK-10.1.389-AR9342-QCA988X-AR8035-16M_V3.img \
    am-fw/QCA955X_QCA9882_AR8033_HSR_V07.bin \
    am-fw/QCA955X_QCA9882_AR8033_V08.bin \
    am-fw/WA.ar934x--LSDK-10.1.389__ubnt-wasp-peregrine-5G-std-16M_V4.img \
    am-fw/WA.ar934x-LSDK-ART2_815-NBE-5AC-G2-Wasp-16M-V4.img \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V1.bin \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V1.img \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V3.img \
    am-fw/WA.ar934x-LSDK-ART-LBE-AC-90-BR-16M-V1.img \
    am-fw/WA.ar934x-LSDK-ART-NBE-2AC-13-16M-V1.img \
    am-fw/XC.qca955x-LSDK-ART-BASESTATION-G2-16M-V2.img \
    am-fw/XC.qca955x.LSDK-ART.NBE-5AC-G2-v2.img \
    am-fw/XC.qca955x-LSDK-ART-ROCKET-2AC-HSR-16M-V3.img \
    am-fw/XC.qca955x-LSDK-ART-Rocket-2AC-HSR-G2-16M-V4.img \
    am-fw/XC.qca955x-LSDK-ART-Rocket-2AC-HSR-G2-16M-V4.NO_EEPROM.bin \
    am-fw/XC.qca955x--V1---LSDK-10.1.389__ubnt-scorpion-peregrine-5G-std-16M.img \
    am-fw/XC.qca955x--V2---LSDK-10.1.389__ubnt-scorpion-peregrine-5G-std-16M.bin \
    am-fw/2WA.v8.7.2.44330.210106.1336.bin \
    am-fw/WA.v8.7.2.44330.210106.1337.bin \
    am-fw/2XC.v8.7.2.44330.210106.1337.bin \
    am-fw/XC.v8.7.2.44330.210106.1337.bin \
    am-fw/UBNT_WA.bin \
    am-fw/UBNT_2WA.bin \
    am-fw/UBNT_XC.bin \
    am-fw/UBNT_2XC.bin \
    am-fw/AR934X_ART_UB.bin \
    am-fw/AR934X_UB.bin \
    am-fw/QCA955X_ART_UB.bin \
    am-fw/QCA955X_UB.bin \
    am-fw/WA.v8.7.4-beta.44660.210219.1654.bin

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

TOOLS-AC-SERIES= \
    am/helper_ARxxxx_11ac \
    am/cfg_part_ar9342.bin \
    am/id_rsa \
    am/id_rsa.pub \
    am/fl_lock_11ac_re

TOOLS-LBE-5AC-XR=$(TOOLS-AC-SERIES)


# Assign common tool for every model
TOOLS-GBE+=$(TOOLS-CONFIG)
TOOLS-PRISMAP+=$(TOOLS-CONFIG)
TOOLS-60G-LAS+=$(TOOLS-CONFIG)
TOOLS-AC-SERIES+=$(TOOLS-CONFIG)
TOOLS-LBE-5AC-XR+=$(TOOLS-CONFIG)

# Assign UAP series tools
TOOLS-AIRMAX+=$(TOOLS-GBE)
TOOLS-AIRMAX+=$(TOOLS-PRISMAP)
TOOLS-AIRMAX+=$(TOOLS-60G-LAS)
TOOLS-AIRMAX+=$(TOOLS-LBE-5AC)

# Project target

$(eval $(call ProductImage,AIRMAX,FCD_$(PRD)_AIRMAX-ALL_$(VER)))
$(eval $(call ProductImage,GBE,FCD_$(PRD)_GBE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,PRISMAP,FCD_$(PRD)_PRISMAP_$(VER)_$(FWVER)))
$(eval $(call ProductImage,60G-LAS,FCD_$(PRD)_60G-LAS_$(VER)_$(FWVER)))
$(eval $(call ProductImage,AC-SERIES,FCD_$(PRD)_AC-SERIES_$(VER)_$(FWVER)))
$(eval $(call ProductImage,LBE-5AC-XR,FCD_$(PRD)_LBE-5AC-XR_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,AIRMAX,FCD_$(PRD)_AIRMAX-ALL_$(VER)))
$(eval $(call ProductCompress,GBE,FCD_$(PRD)_GBE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,PRISMAP,FCD_$(PRD)_PRISMAP_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,60G-LAS,FCD_$(PRD)_60G-LAS_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,LBE-5AC-XR,FCD_$(PRD)_LBE-5AC-XR_$(VER)_$(FWVER),$(ALL)))
$(eval $(call ProductCompress,AC-SERIES,FCD_$(PRD)_AC-SERIES_$(VER)_$(FWVER),$(ALL)))


# ==================================================================================================

IMAGE-e7ff= \
    images/e7ff* \
    am-fw/u-boot-ar934x.bin \
    am-fw/u-boot-art-ar934x.bin \
    am-fw/WA.v8.7.4-beta.44660.210219.1654.bin \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V1.img \
    am-fw/AR934X_ART_UB.bin \
    am-fw/AR934X_UB.bin \

TOOLS-e7ff= \
    am/helper_ARxxxx_11ac \
    am/cfg_part_ar9342.bin \
    am/id_rsa \
    am/id_rsa.pub \
    am/fl_lock_11ac_re

TOOLS-e7ff+=$(TOOLS-CONFIG)

# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,e7ff,FCD_$(PRD)_e7ff_$(VER)_$(FWVER),$(ALL)))
