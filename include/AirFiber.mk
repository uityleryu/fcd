
# Images

IMAGE-AF60= \
    images/dc9b* \
    af-fw/*.bin

IMAGE-AF60-LR= \
    images/dc9e* \
    af-fw/*.bin

IMAGE-AF60-XG= \
    images/dd1* \
    af-fw/AF60*.bin \
    af-fw/AIROS*.bin \
    af-fw/af60-xg*.bin \
    af-fw/NAND_factory_ubi.img

IMAGE-WAVE-BRIDGE= \
    images/ac11* \
    af-fw/XR*.bin \
    af-fw/af60-xr-spf*.bin \
    af-fw/u-boot*

IMAGE-WAVE-AP= \
    images/dc9f* \
    af-fw/GMP*.bin \
    af-fw/af60-spf6.1.1_nor-v1.bin \
    af-fw/u-boot*

IMAGE-LTU = 

IMAGE-AF+=$(IMAGE-AF60)
IMAGE-AF+=$(IMAGE-AF60-LR)
IMAGE-AF+=$(IMAGE-AF60-XG)
IMAGE-AF+=$(IMAGE-WAVE-BRIDGE)
IMAGE-AF+=$(IMAGE-WAVE-AP)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=AirFiber
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/x86-64k-ee \
    common/sshd_config \
    common/tmux.conf \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-AF60+=$(TOOLS-CONFIG)
TOOLS-AF60+= \
    af_af60/cfg_part.bin \
    af_af60/helper_IPQ40xx \
    af_af60/helper_IPQ807x \
    af_af60/id_rsa \
    af_af60/id_rsa.pub \
    af_af60/af_af60_dummy_cal.bin

TOOLS-AF60-LR+=$(TOOLS-AF60)
TOOLS-AF60-XG+=$(TOOLS-AF60)
TOOLS-WAVE-BRIDGE+=$(TOOLS-AF60)
TOOLS-WAVE-AP+=$(TOOLS-AF60)

TOOLS-LTU+=$(TOOLS-CONFIG)
TOOLS-LTU+=af_ltu5/helper_UBNTAME

# Project target

$(eval $(call ProductImage,AF-ALL,FCD_$(PRD)_AF-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductImage,AF60,FCD_$(PRD)_AF60_$(VER)_$(FWVER)))
$(eval $(call ProductImage,AF60-LR,FCD_$(PRD)_AF60-LR_$(VER)_$(FWVER)))
$(eval $(call ProductImage,AF60-XG,FCD_$(PRD)_AF60-XG_$(VER)_$(FWVER)))
$(eval $(call ProductImage,WAVE-BRIDGE,FCD_$(PRD)_WAVE-BRIDGE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,WAVE-AP,FCD_$(PRD)_WAVE-AP_$(VER)_$(FWVER)))
$(eval $(call ProductImage,LTU,FCD_$(PRD)_LTU_$(VER)_$(FWVER)))
$(eval $(call ProductImage,AirFiber_WAVE-SERIES,FCD_$(PRD)_WAVE-SERIES_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,AF-ALL,FCD_$(PRD)_AF-ALL_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,AF60,FCD_$(PRD)_AF60_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,AF60-LR,FCD_$(PRD)_AF60-LR_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,AF60-XG,FCD_$(PRD)_AF60-XG_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,WAVE-BRIDGE,FCD_$(PRD)_WAVE-BRIDGE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,WAVE-AP,FCD_$(PRD)_WAVE-AP_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,LTU,FCD_$(PRD)_LTU_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,AirFiber_WAVE-SERIES,FCD_$(PRD)_WAVE-SERIES_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,AirFiber_XG-SERIES,FCD_$(PRD)_XG-SERIES_$(VER)_$(FWVER)))

# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,00927_ae10))
$(eval $(call ProductCompress2,00966_ae11))
$(eval $(call ProductCompress2,00809_dd11))
$(eval $(call ProductCompress2,00680_ae06))
$(eval $(call ProductCompress2,00708_ae08))
$(eval $(call ProductCompress2,00720_dc9b))
$(eval $(call ProductCompress2,00953_dc9f))
$(eval $(call ProductCompress2,00719_ac11))
$(eval $(call ProductCompress2,00738_dc9e))
$(eval $(call ProductCompress2,00871_dd13))
$(eval $(call ProductCompress2,00727_ae0b))
$(eval $(call ProductCompress2,01066_ac14))
$(eval $(call ProductCompress2,01070_a658))
$(eval $(call ProductCompress2,00979_a664))
$(eval $(call ProductCompress2,AirFiber_WAVE-SERIES,FCD_$(PRD)_WAVE-SERIES_$(VER)_$(FWVER)))
$(eval $(call ProductCompress2,AirFiber_LTU-SERIES,FCD_$(PRD)_WAVE-SERIES_$(VER)_$(FWVER)))
$(eval $(call ProductCompress2,AirFiber_XG-SERIES,FCD_$(PRD)_XG-SERIES_$(VER)_$(FWVER)))