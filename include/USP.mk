IMAGE-USP-PLUG= \
    images/ee71*

IMAGE-USP-3-8= \
    images/e643* \
    images/e648* \
	usp/vport-fw.bin

DIAG_MODEL=null
DIAG_UI_MODEL=USP
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

UPYFCD_VER=
FCDIMG_VER=
UBNTLIB_VER=
TOOL_VER=

TOOLS-CONFIG= \
    common/*

TOOLS-USP-PLUG +=$(TOOLS-CONFIG)
TOOLS-USP-3-8 +=$(TOOLS-CONFIG)

TOOLS-USP-PLUG+= \
    usp/*

TOOLS-USP-3-8+= \
    usp/helper_mips32

$(eval $(call ProductImage,USP-PLUG,FCD-USP-PLUG-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USP-3-8,FCD-USP-3-8-$(VER)-$(FWVER)))

