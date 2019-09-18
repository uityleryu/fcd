
# Images

IMAGE-AFI-ALN-R= \
    images/da11* \
    afi-fw/*

IMAGE-AFI-ALN-P= \
    images/da12* \
    afi-fw/*

IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-R)
IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-P)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=Amplifi
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# FCD images repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-image.git

AFI-ALN-R_FCDIMG_HASH=
AFI-ALN-P_FCDIMG_HASH=

FCDIMG_VER=69f947129aae23f5c8d9c77d78b950cce5279264

# UBNTLIB repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-ubntlib.git

AFI-ALN-R_UBNTLIB_HASH=
AFI-ALN-P_UBNTLIB_HASH=

UBNTLIB_VER=44304f8e4d400c851b428dec20e42e72eda5b3fc

# TOOL repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-tools.git

AFI-ALN-R_TOOL_HASH=
AFI-ALN-P_TOOL_HASH=

TOOL_VER=67077d1b6f0302a09701a6d8c9e77559b7b26ea6

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf

# Project specific tools

TOOLS-AFI-ALN+=$(TOOLS-CONFIG)
TOOLS-AFI-ALN+= afi_aln/*

TOOLS-AFI-ALN-R=$(TOOLS-AFI-ALN)
TOOLS-AFI-ALN-P=$(TOOLS-AFI-ALN)

# Project target

$(eval $(call ProductImage,AFI-ALN,FCD-AFI-ALN-$(VER)))
$(eval $(call ProductImage,AFI-ALN-R,FCD-AFI-ALN-R-$(VER)))
$(eval $(call ProductImage,AFI-ALN-P,FCD-AFI-ALN-P-$(VER)))
