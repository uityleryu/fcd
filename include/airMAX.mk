
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

IMAGE-LBE-5AC= \
    images/e7f9* \
    am-fw/u-boot-ar934x.bin \
    am-fw/u-boot-art-ar934x.bin \
    am-fw/WA.ar934x-LSDK-ART-ISO-STATION-5AC-16M-V1.bin \
    am-fw/WA.v8.7.2.43952.201126.1053.bin \

IMAGE-AIRMAX+=$(IMAGE-GBE)
IMAGE-AIRMAX+=$(IMAGE-PRISMAP)
IMAGE-AIRMAX+=$(IMAGE-LBE-5AC)

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

TOOLS-LBE-5AC= \
    am/helper_ARxxxx_11ac \
    am/cfg_part_ar9342.bin \
    am/id_rsa \
    am/id_rsa.pub \
    am/fl_lock_11ac_re


# Assign common tool for every model
TOOLS-GBE+=$(TOOLS-CONFIG)
TOOLS-PRISMAP+=$(TOOLS-CONFIG)
TOOLS-60G-LAS+=$(TOOLS-CONFIG)
TOOLS-LBE-5AC+=$(TOOLS-CONFIG)

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
$(eval $(call ProductImage,LBE-5AC,FCD_$(PRD)_LBE-5AC_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,AIRMAX,FCD_$(PRD)_AIRMAX-ALL_$(VER)))
$(eval $(call ProductCompress,GBE,FCD_$(PRD)_GBE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,PRISMAP,FCD_$(PRD)_PRISMAP_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,60G-LAS,FCD_$(PRD)_60G-LAS_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,LBE-5AC,FCD_$(PRD)_LBE-5AC_$(VER)_$(FWVER)))
