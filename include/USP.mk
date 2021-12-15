
# Images

IMAGE-USP-PLUG= \
    images/ee73* \
    usp/plug/*

IMAGE-USP-STRIP= \
    images/ee74* \
    usp/strip/*

IMAGE-USP-PDU-PRO= \
    images/ed12* \
    usp/pdu-pro/*

IMAGE-USP-PRO-PDU-HD= \
    images/ed15* \
    usp/pdu-pro-hd/*

IMAGE-USP-3-8= \
    images/e643* \
    images/e648* \
    usp/vport-fw.bin


IMAGE-USP-RPS-PRO= \
    images/ed13* \
    usp/rps-pro/*

IMAGE-USP-RPS= \
    images/ed11* \
    usp/rps/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
    usp/rps/unifi-v1.1.2.71-gd9df1cea_usw-mt7621-16MB_u-boot.bin \
    usp/rps/US.mt7621*


IMAGE-USP-RPS= \
    images/ee76* \
    
# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=USP
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/*

# Project specific tools

TOOLS-USP-PLUG +=$(TOOLS-CONFIG)
TOOLS-USP-3-8 +=$(TOOLS-CONFIG)
TOOLS-USP-STRIP +=$(TOOLS-CONFIG)
TOOLS-USP-PDU-PRO +=$(TOOLS-CONFIG)
TOOLS-USP-PRO-PDU-HD +=$(TOOLS-CONFIG)
TOOLS-USP-RPS-PRO +=$(TOOLS-CONFIG)
TOOLS-USP-RPS +=$(TOOLS-CONFIG)
TOOLS-USP-Battery +=$(TOOLS-CONFIG)

TOOLS-USP-PLUG+= \
    usp/*

TOOLS-USP-3-8+= \
    usp/helper_mips32

TOOLS-USP-STRIP+= \
    usp/helper_esp8266 \
    usp/gen-cert.sh

TOOLS-USP-PDU-PRO+= \
    pdu_pro/helper_MT7628_release

TOOLS-USP-RPS+= \
    usp_rps/helper_UNIFI_MT7621_release

# Project target

$(eval $(call ProductImage,USP-PLUG,FCD_$(PRD)_USP-PLUG_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USP-3-8,FCD_$(PRD)_USP-3-8_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USP-STRIP,FCD_$(PRD)_USP-STRIP_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USP-PDU-PRO,FCD_$(PRD)_USP-PDU-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USP-PDU-PRO,FCD_$(PRD)_USP-PRO-PDU-HD_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USP-RPS-PRO,FCD_$(PRD)_USP-RPS-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USP-RPS,FCD_$(PRD)_USP-RPS_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USP-Battery,FCD_$(PRD)_USP-Battery_$(VER)_$(FWVER)))


# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,USP-PLUG,FCD_$(PRD)_USP-PLUG_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USP-3-8,FCD_$(PRD)_USP-3-8_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USP-STRIP,FCD_$(PRD)_USP-STRIP_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USP-PDU-PRO,FCD_$(PRD)_USP-PDU-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USP-PDU-PRO,FCD_$(PRD)_USP-PRO-PDU-HD_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USP-RPS-PRO,FCD_$(PRD)_USP-RPS-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USP-RPS,FCD_$(PRD)_USP-RPS_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,USP-Battery,FCD_$(PRD)_USP-Battery_$(VER)_$(FWVER)))

# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,00731_ee73))
$(eval $(call ProductCompress2,00896_ee74))
$(eval $(call ProductCompress2,00365_e648))
$(eval $(call ProductCompress2,00986_ed12))
$(eval $(call ProductCompress2,01036_ed15))
$(eval $(call ProductCompress2,00777_ee74))
$(eval $(call ProductCompress2,00364_e643))
$(eval $(call ProductCompress2,02781_ed11))
$(eval $(call ProductCompress2,03086_ed13))
$(eval $(call ProductCompress2,03491_ee76))
