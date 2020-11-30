
# Images

IMAGE-UA-PRO-BL=

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiAccess
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-UA-PRO-BL+=$(TOOLS-CONFIG)

# Project target

$(eval $(call ProductImage,UA-PRO-BL,FCD_$(PRD)_UA-PRO-BL_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,UA-PRO-BL,FCD_$(PRD)_UA-PRO-BL_$(VER)_$(FWVER)))