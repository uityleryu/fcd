
# Images

IMAGE-UC-DISPLAY-7=

IMAGE-UC-DISPLAY-13=

IMAGE-UC-DISPLAY-21=

IMAGE-UC-DISPLAY-27=

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

TOOLS-UC-DISPLAY-7+=$(TOOLS-CONFIG)
TOOLS-UC-DISPLAY-13+=$(TOOLS-CONFIG)
TOOLS-UC-DISPLAY-21+=$(TOOLS-CONFIG)
TOOLS-UC-DISPLAY-27+=$(TOOLS-CONFIG)

# Project target

$(eval $(call ProductImage,UC-DISPLAY-7,FCD_$(PRD)_UC-DISPLAY-7_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-DISPLAY-13,FCD_$(PRD)_UC-DISPLAY-13_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-DISPLAY-21,FCD_$(PRD)_UC-DISPLAY-21_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-DISPLAY-27,FCD_$(PRD)_UC-DISPLAY-27_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,UC-DISPLAY-7,FCD_$(PRD)_UC-DISPLAY-7_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-DISPLAY-13,FCD_$(PRD)_UC-DISPLAY-13_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-DISPLAY-21,FCD_$(PRD)_UC-DISPLAY-21_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-DISPLAY-27,FCD_$(PRD)_UC-DISPLAY-27_$(VER)_$(FWVER)))


# ==================================================================================================
IMAGE-ef80=
IMAGE-ef81=
IMAGE-ef83=
IMAGE-ef84=


# ---------------------------------------------------------------------------------------------------
TOOLS-ef80=$(TOOLS-CONFIG)
TOOLS-ef81=$(TOOLS-CONFIG)
TOOLS-ef83=$(TOOLS-CONFIG)
TOOLS-ef84=$(TOOLS-CONFIG)

# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,ef80,FCD_$(PRD)_ef80_$(VER)_$(FWVER),$(ALL)))
$(eval $(call ProductCompress2,ef81,FCD_$(PRD)_ef81_$(VER)_$(FWVER),$(ALL)))
$(eval $(call ProductCompress2,ef83,FCD_$(PRD)_ef83_$(VER)_$(FWVER),$(ALL)))
$(eval $(call ProductCompress2,ef84,FCD_$(PRD)_ef84_$(VER)_$(FWVER),$(ALL)))
