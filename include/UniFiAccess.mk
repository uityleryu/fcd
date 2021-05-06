
# Images

IMAGE-UA-GATE= \
    images/ec46* \
    ua-fw/*

IMAGE-UA+=$(IMAGE-UA-GATE)


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

TOOLS-UA+=$(TOOLS-CONFIG)

TOOLS-UA-GATE+=$(TOOLS-UA)


# Project target

$(eval $(call ProductImage,UA-GATE,FCD_$(PRD)_UA-GATE_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,UA-GATE,FCD_$(PRD)_UA-GATE_$(VER)_$(FWVER)))


# ==================================================================================================

# UA-PRO-BL
IMAGE-02966-ec60=

# -----------------------------------------------------------------------------------------

TOOLS-02966-ec60+=$(TOOLS-CONFIG)

# -----------------------------------------------------------------------------------------

$(eval $(call ProductCompress2,02966-ec60))
