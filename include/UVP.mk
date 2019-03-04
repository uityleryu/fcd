
IMAGE-UVP-FLEX=

DIAG_MODEL=uvp
DIAG_UI_MODEL=UniFiVOIP

UPYFCD_VER=
FCDIMG_VER=
UBNTLIB_VER=
TOOL_VER=

TOOLS-CONFIG=.tmux.conf \
             sshd_config

TOOLS-UVP-FLEX+=$(TOOLS-CONFIG)
TOOLS-UVP-FLEX+= \
    uvp/helper_DVF99_release \
    uvp/dropbearkey_dvf9918 \
    uvp/dropbearkey \
    uvp/dvf9918-arm64-ee

$(eval $(call ProductImage,UVP-FLEX,FCD-UVP-FLEX-$(VER)))
