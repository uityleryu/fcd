IMAGE-USP-PLUG= \
    images/ee71*

IMAGE-USP3= \
    images/e643* \
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
TOOLS-USP3     +=$(TOOLS-CONFIG)

TOOLS-USP-PLUG+= \
    usp/*

TOOLS-USP3+= \
    usp/helper_mips32

$(eval $(call ProductImage,USP-PLUG,FCD-USP-PLUG-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USP3,FCD-USP3-$(VER)-$(FWVER)))

