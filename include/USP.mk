IMAGE-USP-PLUG= \
    images/ee71*


IMAGE-USP+=$(IMAGE-USP-PLUG)


DIAG_MODEL=null
DIAG_UI_MODEL=na
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

UPYFCD_VER=
FCDIMG_VER=
UBNTLIB_VER=
TOOL_VER=

TOOLS-CONFIG= \
    common/*

TOOLS-USP-PLUG+=$(TOOLS-CONFIG)
TOOLS-USP-PLUG+= \
    usp/*


TOOLS-USP+=$(TOOLS-USP-PLUG)


$(eval $(call ProductImage,USP,FCD-USP-$(VER)-$(FWVER)))
$(eval $(call ProductImage,USP-PLUG,FCD-USP-PLUG-$(VER)-$(FWVER)))

