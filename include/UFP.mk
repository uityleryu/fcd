
IMAGE-UFP-SENSE=

IMAGE-UFP+=$(IMAGE-UFP-SENSE)

DIAG_UI_MODEL=UniFiProtect
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

UPYFCD_VER =
FCDIMG_VER =
UBNTLIB_VER=
TOOL_VER   =

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/helper_UNIFI_MT7621_release

TOOLS-UFP+=$(TOOLS-CONFIG)

TOOLS-UFP-SENSE=$(TOOLS-UFP)

$(eval $(call ProductImage,UFP-SENSE,FCD-UFP-SENSE-$(VER)-$(FWVER)))
