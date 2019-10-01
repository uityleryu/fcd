
# Images

IMAGE-UNVR4= \
    images/ea16* \
    unas/*

IMAGE-UNVR8= \
    images/ea18* \
    unas/*

IMAGE-UNVR+=$(IMAGE-UNVR4)
IMAGE-UNVR+=$(IMAGE-UNVR8)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiNAS
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# FCD images repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-image.git

UNVR4_FCDIMG_HASH=
UNVR8_FCDIMG_HASH=

FCDIMG_VER=

# UBNTLIB repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-ubntlib.git

UNVR4_UBNTLIB_HASH=
UNVR8_UBNTLIB_HASH=

UBNTLIB_VER=

# TOOL repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-tools.git

UNVR4_TOOL_HASH=
UNVR8_TOOL_HASH=

TOOL_VER=

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee

# Project specific tools

TOOLS-UNVR+=$(TOOLS-CONFIG)
TOOLS-UNVR+= \
    unas/al324-ee \
    unas/helper_UNAS-AL324_release \
    unas/config_gu.sh \
    unas/enp0s1.network \
    unas/enp0s2.network

TOOLS-UNVR4+=$(TOOLS-UNVR)
TOOLS-UNVR8+=$(TOOLS-UNVR)

# Project target

$(eval $(call ProductImage,UNVR,FCD-UNVR-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UNVR4,FCD-UNVR4-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UNVR8,FCD-UNVR8-$(VER)-$(FWVER)))
