
# Images

IMAGE-AF= \
    images/dc9b* \
    af-fw/*.bin

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=AirFiber
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# FCD images repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-image.git

AF_FCDIMG_HASH=

FCDIMG_VER=

# UBNTLIB repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-ubntlib.git

AF_UBNTLIB_HASH=

UBNTLIB_VER=

# TOOL repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-tools.git

AF_TOOL_HASH=

TOOL_VER=

# Common tools

TOOLS-CONFIG= \
    common/x86-64k-ee \
    common/sshd_config \
    common/tmux.conf

# Project specific tools

TOOLS-AF+= \
    af_af60/cfg_part.bin \
    af_af60/helper_IPQ40xx \
    af_af60/id_rsa \
    af_af60/id_rsa.pub 

TOOLS-AF+=$(TOOLS-CONFIG)
TOOLS-AF+= af_ltu5/helper_UBNTAME

# Project target

$(eval $(call ProductImage,AF,FCD-AF-ALL-$(VER)-$(FWVER)))
