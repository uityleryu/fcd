
# Images

IMAGE-ALN-R= \
    images/da11* \
    afi-fw/*

IMAGE-ALN-P= \
    images/da12* \
    afi-fw/*

IMAGE-ALN-R-EU= \
    images/da13* \
    afi-fw/*

IMAGE-ALN-P-EU= \
    images/da14* \
    afi-fw/*


IMAGE-ALN+=$(IMAGE-ALN-R)
IMAGE-ALN+=$(IMAGE-ALN-P)
IMAGE-ALN+=$(IMAGE-ALN-R-EU)
IMAGE-ALN+=$(IMAGE-ALN-P-EU)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=Amplifi
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-ALN+=$(TOOLS-CONFIG)
TOOLS-ALN+= afi_aln/*

TOOLS-ALN-R=$(TOOLS-ALN)
TOOLS-ALN-P=$(TOOLS-ALN)
TOOLS-ALN-R-EU=$(TOOLS-ALN)
TOOLS-ALN-P-EU=$(TOOLS-ALN)


# Project target
$(eval $(call ProductImage,ALN,FCD_$(PRD)_ALN_$(VER)_$(FWVER)))

## Project compressed file for RPi FCD host
$(eval $(call ProductCompress,ALN,FCD_$(PRD)_ALN_$(VER)_$(FWVER)))

