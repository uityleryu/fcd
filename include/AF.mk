# AF

IMAGE-AF=

DIAG_MODEL=af

UPYFCD_VER=
FCDIMG_VER=
UBNTLIB_VER=
TOOL_VER=
DIAG_UI_MODEL=AirFiber
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf

TOOLS-AF+=$(TOOLS-CONFIG)
TOOLS-AF+= helper_UBNTAME

$(eval $(call ProductImage,AF,FCD-AF-$(VER)))
