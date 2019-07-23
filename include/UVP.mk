
IMAGE-UVP-FLEX= \
    images/ef0d* \
    uvp-fw/uvp-flex_1.0.8.bin.unsign

DIAG_MODEL=uvp
DIAG_UI_MODEL=UniFiVOIP
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

UPYFCD_VER=
FCDIMG_VER=
UBNTLIB_VER=
TOOL_VER=

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee

TOOLS-UVP-FLEX+=$(TOOLS-CONFIG)
TOOLS-UVP-FLEX+= uvp/*

$(eval $(call ProductImage,UVP-FLEX,FCD-UVP-FLEX-$(VER)-$(FWVER)))
