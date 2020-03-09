
# Images

IMAGE-USP-PLUG= \
    images/ee73* \
    usp/plug/*

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

TOOLS-USP-PLUG+= \
    usp/*

TOOLS-USP-3-8+= \
    usp/helper_mips32

# Project target

$(eval $(call ProductImage,USP-PLUG,FCD-USP-PLUG-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USP-3-8,FCD-USP-3-8-$(VER)-$(FWVER)))
