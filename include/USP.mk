
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

IMAGE-USP-3-8= \
    images/e643* \
    images/e648* \
    usp/vport-fw.bin

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

TOOLS-USP-PLUG+= \
    usp/*

TOOLS-USP-3-8+= \
    usp/helper_mips32

TOOLS-USP-STRIP+= \
    usp/helper_esp8266

TOOLS-USP-STRIP+= \
    usp/helper_MT7628_release

# Project target

$(eval $(call ProductImage,USP-PLUG,FCD_$(PRD)_USP-PLUG_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USP-3-8,FCD_$(PRD)_USP-3-8_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USP-STRIP,FCD_$(PRD)_USP-STRIP_$(VER)_$(FWVER)))
$(eval $(call ProductImage,USP-PDU-PRO,FCD_$(PRD)_USP-PDU-PRO_$(VER)_$(FWVER)))
