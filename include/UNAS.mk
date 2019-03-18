IMAGE-UNAS4= \
    images/ea16* \
    unas/*

IMAGE-UNAS8= \
    images/ea18* \
    unas/*

IMAGE-UNAS+=$(IMAGE-UNAS4)
IMAGE-UNAS+=$(IMAGE-UNAS8)

DIAG_MODEL=unas
DIAG_UI_MODEL=UniFiNAS

UPYFCD_VER=
FCDIMG_VER=
UBNTLIB_VER=
TOOL_VER=

TOOLS-CONFIG= \
    .tmux.conf \
    sshd_config

TOOLS-UNAS+=$(TOOLS-CONFIG)
TOOLS-UNAS+= \
    unas/helper_UNAS-AL324_release \
    unas/al324-ee

TOOLS-UNAS4+=$(TOOLS-UNAS)
TOOLS-UNAS8+=$(TOOLS-UNAS)

$(eval $(call ProductImage,UNAS,FCD-UNAS-$(VER)))
$(eval $(call ProductImage,UNAS4,FCD-UNAS4-$(VER)))
$(eval $(call ProductImage,UNAS8,FCD-UNAS8-$(VER)))
