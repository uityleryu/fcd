
# Images

IMAGE-AF60= \
    images/dc9b* \
    af-fw/*.bin

IMAGE-AF60-LR= \
    images/dc9e* \
    af-fw/*.bin

IMAGE-AF+=$(IMAGE-AF60)
IMAGE-AF+=$(IMAGE-AF60-LR)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=AirFiber
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# FCD images repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-image.git

AF60_FCDIMG_HASH=
AF60-LR_FCDIMG_HASH=

FCDIMG_VER=

# UBNTLIB repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-ubntlib.git

AF60_UBNTLIB_HASH=
AF60-LR_UBNTLIB_HASH=

UBNTLIB_VER=

# TOOL repo hash
# git@wingchun.corp.ubnt.com:Ubiquiti-BSP/fcd-tools.git

AF60_TOOL_HASH=
AF60-LR_TOOL_HASH=

TOOL_VER=

# Common tools

TOOLS-CONFIG= \
    common/x86-64k-ee \
    common/sshd_config \
    common/tmux.conf

# Project specific tools

TOOLS-AF60+=$(TOOLS-CONFIG)
TOOLS-AF60+= \
    af_af60/cfg_part.bin \
    af_af60/helper_IPQ40xx \
    af_af60/id_rsa \
    af_af60/id_rsa.pub \
    af_ltu5/helper_UBNTAME

TOOLS-AF60-LR+=$(TOOLS-AF60)

# Project target

$(eval $(call ProductImage,AF,FCD-AF-ALL-$(VER)-$(FWVER)))
$(eval $(call ProductImage,AF60,FCD-AF60-$(VER)-$(FWVER)))
$(eval $(call ProductImage,AF60-LR,FCD-AF60-LR-$(VER)-$(FWVER)))
