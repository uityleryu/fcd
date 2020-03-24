
# Images

IMAGE-UVC-G4PRO= \
    images/a563* \
    uvc-fw/*

IMAGE-UVC-G3BATTERY= \
    images/a580* \
    uvc-fw/*

IMAGE-UVC+=$(IMAGE-UVC-G4PRO)
IMAGE-UVC+=$(IMAGE-UVC-G3BATTERY)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiVideo
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee

# Project specific tools

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

# Project target

$(eval $(call ProductImage,UVC-G4PRO,FCD_$(PRD)_UVC-G4PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G3BATTERY,FCD_$(PRD)_UVC-G3BATTERY_$(VER)_$(FWVER)))







