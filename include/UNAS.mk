
# Images

IMAGE-UNAS4= \
    images/ea16* \
    unas/*

IMAGE-UNAS8= \
    images/ea18* \
    unas/*

IMAGE-UNAS+=$(IMAGE-UNAS4)
IMAGE-UNAS+=$(IMAGE-UNAS8)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiNAS
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# FCD images repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-image.git

UNAS4_FCDIMG_HASH=
UNAS8_FCDIMG_HASH=

FCDIMG_VER=

# UBNTLIB repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-ubntlib.git

UNAS4_UBNTLIB_HASH=
UNAS8_UBNTLIB_HASH=

UBNTLIB_VER=

# TOOL repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-tools.git

UNAS4_TOOL_HASH=
UNAS8_TOOL_HASH=

TOOL_VER=

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee

# Project specific tools

TOOLS-UNAS+=$(TOOLS-CONFIG)
TOOLS-UNAS+= \
    unas/al324-ee \
    unas/helper_UNAS-AL324_release \
    unas/config_gu.sh \
    unas/enp0s1.network \
    unas/enp0s2.network

TOOLS-UNAS4+=$(TOOLS-UNAS)
TOOLS-UNAS8+=$(TOOLS-UNAS)

# Project target

$(eval $(call ProductImage,UNAS,FCD-UNAS-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UNAS4,FCD-UNAS4-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UNAS8,FCD-UNAS8-$(VER)-$(FWVER)))
