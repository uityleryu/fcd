
IMAGE-UVC-G4PRO= \
    images/a563* \
    uvc-fw/*

IMAGE-UVC-G3BATTERY= \
    images/a580* \
    uvc-fw/*

DIAG_UI_MODEL=UniFiVideo
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


TOOLS-UVC+=$(TOOLS-CONFIG)


TOOLS-UVC-G4PRO+=$(TOOLS-UVC)
TOOLS-UVC-G4PRO+= \
    uvc/helper_S5L_g4pro \
    uvc/m25p80_g4pro.ko

TOOLS-UVC-G3BATTERY+=$(TOOLS-UVC)
TOOLS-UVC-G3BATTERY+= \
    uvc/helper_S2LM_g3battery \
    uvc/m25p80_g3battery.ko \
    uvc/eegen-ascii_g3battery.bin


$(eval $(call ProductImage,UVC-G4PRO,FCD-UVC-G4PRO-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UVC-G3BATTERY,FCD-UVC-G3BATTERY-$(VER)-$(FWVER)))







