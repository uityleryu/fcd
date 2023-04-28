
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

IMAGE-6-Extender= \
    images/a666* \
    afi-fw/*

IMAGE-6-Router= \
    images/a665* \
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

IMAGE-ALN-E= \
    images/da15* \
    afi-fw/*

IMAGE-100W-USB-C= \
    images/da20* \
    afi-fw/afi-100w-usb-usb-c/*

IMAGE-ALN-PE= \
    images/da21* \
    afi-fw/afi-aln-pe/*

IMAGE-AMP= \
    image/aa02* \
    afi-fw/*

IMAGE-ALN+=$(IMAGE-6-ISP)
IMAGE-ALN+=$(IMAGE-6-Instant)
IMAGE-ALN+=$(IMAGE-6-Mesh)
IMAGE-ALN+=$(IMAGE-ALN-R)
IMAGE-ALN+=$(IMAGE-ALN-P)
IMAGE-ALN+=$(IMAGE-ALN-R-EU)
IMAGE-ALN+=$(IMAGE-ALN-P-EU)
IMAGE-ALN+=$(IMAGE-ALN-E)
IMAGE-ALN+=$(IMAGE-100W-USB-C)
IMAGE-ALN+=$(IMAGE-6-Extender)
IMAGE-ALN+=$(IMAGE-6-Router)
IMAGE-ALN+=$(IMAGE-ALN-PE)
IMAGE-ALN+=$(IMAGE-AMP)

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
TOOLS-ALN-E=$(TOOLS-ALN)
TOOLS-100W-USB-C=$(TOOLS-ALN)
TOOLS-6-Extender=$(TOOLS-ALN)
TOOLS-6-Router=$(TOOLS-ALN)
TOOLS-ALN-PE=$(TOOLS-ALN)
TOOLS-AMP=$(TOOLS-ALN)

# Project target
$(eval $(call ProductImage,ALN,FCD_$(PRD)_ALN_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UPS,FCD_$(PRD)_UC-UPS_$(VER)_$(FWVER)))
$(eval $(call ProductImage,6-Instant,FCD_$(PRD)_6-Instant$(VER)_$(FWVER)))
$(eval $(call ProductImage,6-Mesh,FCD_$(PRD)_6-Mesh_$(VER)_$(FWVER)))
$(eval $(call ProductImage,100W-USB-C,FCD_$(PRD)_100W-USB-C_$(VER)_$(FWVER)))
$(eval $(call ProductImage,6-Extender,FCD_$(PRD)_6-Extender_$(VER)_$(FWVER)))
$(eval $(call ProductImage,6-Router,FCD_$(PRD)_6-Router$(VER)_$(FWVER)))
$(eval $(call ProductImage,ALN-E,FCD_$(PRD)_AFi-ALN-E$(VER)_$(FWVER)))
$(eval $(call ProductImage,ALN-PE,FCD_$(PRD)_AFi-ALN-PE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,AMP,FCD_$(PRD)_AFi-AMP_$(VER)_$(FWVER)))

## Project compressed file for RPi FCD host
$(eval $(call ProductCompress,ALN,FCD_$(PRD)_ALN_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UPS,FCD_$(PRD)_UC-UPS_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,6-Instant,FCD_$(PRD)_6-Instant$(VER)_$(FWVER)))
$(eval $(call ProductCompress,6-Mesh,FCD_$(PRD)_6-Mesh_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,100W-USB-C,FCD_$(PRD)_100W-USB-C_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,6-Extender,FCD_$(PRD)_6-Extender_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,6-Router,FCD_$(PRD)_6-Router$(VER)_$(FWVER)))
$(eval $(call ProductCompress,ALN-E,FCD_$(PRD)_AFi-ALN-E$(VER)_$(FWVER)))
$(eval $(call ProductCompress,ALN-PE,FCD_$(PRD)_AFi-ALN-PE_$(VER)_$(FWVER)))
<<<<<<< HEAD
$(eval $(call ProductCompress,AMP,FCD_$(PRD)_AFi-AMP_$(VER)_$(FWVER)))


=======
$(eval $(call ProductCompress,Cinema-Bridge,FCD_$(PRD)_Cinema-Bridge$(VER)_$(FWVER)))
$(eval $(call ProductCompress,AMP,FCD_$(PRD)_AFi-AMP_$(VER)_$(FWVER)))
>>>>>>> develop
# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,00775_a616))
$(eval $(call ProductCompress2,01135_a641))
$(eval $(call ProductCompress2,01136_a639))
$(eval $(call ProductCompress2,01136_a666))
$(eval $(call ProductCompress2,01135_a665))
$(eval $(call ProductCompress2,01905_da13))
$(eval $(call ProductCompress2,00657_da12))
$(eval $(call ProductCompress2,00957_da14))
$(eval $(call ProductCompress2,01150_da15))
$(eval $(call ProductCompress2,01605_da11))
$(eval $(call ProductCompress2,01039_da20))
$(eval $(call ProductCompress2,01033_ed14))
$(eval $(call ProductCompress2,01033_da21))
$(eval $(call ProductCompress2,04137_aa01))
$(eval $(call ProductCompress2,AFI_ALNMAX-SERIES))
$(eval $(call ProductCompress2,04120_aa02))
