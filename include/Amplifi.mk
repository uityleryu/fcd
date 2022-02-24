
# Images

IMAGE-6-ISP= \
    images/a616* \
    afi-fw/*

IMAGE-6-Instant= \
    images/a641* \
    afi-fw/*

IMAGE-6-Mesh= \
    images/a639* \
    afi-fw/*

IMAGE-UPS= \
    images/ed14*

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

IMAGE-ALN+=$(IMAGE-6-ISP)
IMAGE-ALN+=$(IMAGE-6-Instant)
IMAGE-ALN+=$(IMAGE-6-Mesh)
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

TOOLS-UC-UPS+=$(TOOLS-CONFIG)
TOOLS-ALN+=$(TOOLS-CONFIG)
TOOLS-ALN+= afi_aln/*

TOOLS-6-ISP=$(TOOLS-ALN)
TOOLS-6-Instant=$(TOOLS-ALN)
TOOLS-6-Mesh=$(TOOLS-ALN)
TOOLS-ALN-R=$(TOOLS-ALN)
TOOLS-ALN-P=$(TOOLS-ALN)
TOOLS-ALN-R-EU=$(TOOLS-ALN)
TOOLS-ALN-P-EU=$(TOOLS-ALN)


# Project target
$(eval $(call ProductImage,ALN,FCD_$(PRD)_ALN_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UPS,FCD_$(PRD)_UC-UPS_$(VER)_$(FWVER)))
$(eval $(call ProductImage,6-Instant,FCD_$(PRD)_6-Instant$(VER)_$(FWVER)))
$(eval $(call ProductImage,6-Mesh,FCD_$(PRD)_6-Mesh_$(VER)_$(FWVER)))

## Project compressed file for RPi FCD host
$(eval $(call ProductCompress,ALN,FCD_$(PRD)_ALN_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UPS,FCD_$(PRD)_UC-UPS_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,6-Instant,FCD_$(PRD)_6-Instant$(VER)_$(FWVER)))
$(eval $(call ProductCompress,6-Mesh,FCD_$(PRD)_6-Mesh_$(VER)_$(FWVER)))

# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,00775_a616))
$(eval $(call ProductCompress2,01135_a641))
$(eval $(call ProductCompress2,01136_a639))
$(eval $(call ProductCompress2,01905_da13))
$(eval $(call ProductCompress2,00657_da12))
$(eval $(call ProductCompress2,00957_da14))
$(eval $(call ProductCompress2,01605_da11))
$(eval $(call ProductCompress2,01033_ed14))
