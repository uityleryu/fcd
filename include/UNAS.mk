IMAGE-UNAS4= \
    images/ea16* \
    unas/*

IMAGE-UNAS8= \
    images/ea18* \
    unas/*

IMAGE-UNAS+=$(IMAGE-UNAS4)
IMAGE-UNAS+=$(IMAGE-UNAS8)

DIAG_MODEL=null
DIAG_UI_MODEL=UniFiNAS
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

UPYFCD_VER=
FCDIMG_VER=
UBNTLIB_VER=
TOOL_VER=

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf

TOOLS-UNAS+=$(TOOLS-CONFIG)
TOOLS-UNAS+= \
    unas/*


TOOLS-UNAS4+=$(TOOLS-UNAS)
TOOLS-UNAS8+=$(TOOLS-UNAS)

$(eval $(call ProductImage,UNAS,FCD-UNAS-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UNAS4,FCD-UNAS4-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UNAS8,FCD-UNAS8-$(VER)-$(FWVER)))
