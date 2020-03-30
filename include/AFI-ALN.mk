
# Images

IMAGE-AFI-ALN-R= \
    images/da11* \
    afi-fw/*

IMAGE-AFI-ALN-P= \
    images/da12* \
    afi-fw/*

IMAGE-AFI-ALN-R-EU= \
    images/da13* \
    afi-fw/*

IMAGE-AFI-ALN-P-EU= \
    images/da14* \
    afi-fw/*


IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-R)
IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-P)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=Amplifi
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf

# Project specific tools

TOOLS-AFI-ALN+=$(TOOLS-CONFIG)
TOOLS-AFI-ALN+= afi_aln/*

TOOLS-AFI-ALN-R=$(TOOLS-AFI-ALN)
TOOLS-AFI-ALN-P=$(TOOLS-AFI-ALN)
TOOLS-AFI-ALN-R-EU=$(TOOLS-AFI-ALN)
TOOLS-AFI-ALN-P-EU=$(TOOLS-AFI-ALN)


# Project target
$(eval $(call ProductImage,AFI-ALN,FCD_$(PRD)_ALN_$(VER)))
$(eval $(call ProductImage,AFI-ALN-R,FCD_$(PRD)_ALN-R_$(VER)))
$(eval $(call ProductImage,AFI-ALN-P,FCD_$(PRD)_ALN-P_$(VER)))
$(eval $(call ProductImage,AFI-ALN-R,FCD_$(PRD)_ALN-R-EU_$(VER)))
$(eval $(call ProductImage,AFI-ALN-P,FCD_$(PRD)_ALN-P-EU_$(VER)))
