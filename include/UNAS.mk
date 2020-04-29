
# Images

IMAGE-UNVR4= \
    images/ea16* \
    unas/*

IMAGE-UNVR-BT= \
    images/ea1a* \
    unas/*

IMAGE-UNVR+=$(IMAGE-UNVR4)
IMAGE-UNVR+=$(IMAGE-UNVR-BT)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiNVR
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

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
TOOLS-UNVR-BT+=$(TOOLS-UNVR)

# Project target

$(eval $(call ProductImage,UNVR,FCD_$(PRD)_UNVR_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UNVR4,FCD_$(PRD)_UNVR4_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UNVR-BT,FCD_$(PRD)_UNVR-BT_$(VER)_$(FWVER)))
