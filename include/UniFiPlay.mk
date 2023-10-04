
# Images

IMAGE-UPL-AMP= \
    image/aa03* \
    upl-fw/*

IMAGE-ALN+=$(IMAGE-UPL-AMP)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiPlay
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-UC-UPS+=$(TOOLS-CONFIG)
TOOLS-ALN+=$(TOOLS-CONFIG)
TOOLS-ALN+= afi_aln/*


TOOLS-UPL-AMP=$(TOOLS-ALN)

# Project target

## Project compressed file for RPi FCD host
$(eval $(call ProductCompress,AMP,FCD_$(PRD)_UPL-AMP_$(VER)_$(FWVER)))

# Project compressed type2 file for RPi FCD host
$(eval $(call ProductCompress2,08740_aa03))
