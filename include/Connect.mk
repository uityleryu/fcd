
# Images

IMAGE-UTD-7=

IMAGE-UTD-13=

IMAGE-UTD-21=

IMAGE-UTD-27=

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=Connect
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-UTD-7+=$(TOOLS-CONFIG)
TOOLS-UTD-13+=$(TOOLS-CONFIG)
TOOLS-UTD-21+=$(TOOLS-CONFIG)
TOOLS-UTD-27+=$(TOOLS-CONFIG)

# Project target

$(eval $(call ProductImage,UTD-7,FCD_$(PRD)_CONNECT-UTD-7_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UTD-13,FCD_$(PRD)_CONNECT-UTD-13_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UTD-21,FCD_$(PRD)_CONNECT-UTD-21_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UTD-27,FCD_$(PRD)_CONNECT-UTD-27_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,UTD-7,FCD_$(PRD)_CONNECT-UTD-7_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UTD-13,FCD_$(PRD)_CONNECT-UTD-13_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UTD-21,FCD_$(PRD)_CONNECT-UTD-21_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UTD-27,FCD_$(PRD)_CONNECT-UTD-27_$(VER)_$(FWVER)))
