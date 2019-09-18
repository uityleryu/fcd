
# Images

IMAGE-UVP-FLEX= \
    images/ef0d* \
    uvp-fw/uvp-flex_1.0.8.bin.unsign

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiVOIP
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# FCD images repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-image.git

UVP-FLEX_FCDIMG_HASH=

FCDIMG_VER=

# UBNTLIB repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-ubntlib.git

UVP-FLEX_UBNTLIB_HASH=

UBNTLIB_VER=

# TOOL repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-tools.git

UVP-FLEX_TOOL_HASH=

TOOL_VER=

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee

# Project specific tools

TOOLS-UVP-FLEX+=$(TOOLS-CONFIG)
TOOLS-UVP-FLEX+= uvp/*

# Project target

$(eval $(call ProductImage,UVP-FLEX,FCD-UVP-FLEX-$(VER)-$(FWVER)))
