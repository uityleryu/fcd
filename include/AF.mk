# AF

IMAGE-AF=
#IMAGE-UDMXG=images/ea17* \
#          udm-fw/*

DIAG_MODEL=af

UPYFCD_VER=
FCDIMG_VER=
UBNTLIB_VER=
TOOL_VER=
DIAG_UI_MODEL=UniFiDream

TOOLS-AF=.tmux.conf \
          helper_UBNTAME

$(eval $(call ProductImage,AF,FCD-AF-$(VER)))
