
# Images

IMAGE-UNVR4= \
    images/ea1a* \
    unas/unifinvr-4-fw.bin \
    unas/UNVR4*

IMAGE-UNVR-PRO= \
    images/ea20* \
    unas/unifinvr-pro-fw.bin \
    unas/UNVRPRO*

IMAGE-UNVR-AI= \
    images/ea21* \
    unas/unifinvr-ai-fw.bin \
    unas/UNVRAI*

IMAGE-UNVR-HD= \
    images/ea30* \
    unas/unifinvr-hd-fw.bin \
    unas/UNVRHD*

IMAGE-UNVR+=$(IMAGE-UNVR4)
IMAGE-UNVR+=$(IMAGE-UNVR-PRO)
IMAGE-UNVR+=$(IMAGE-UNVR-AI)
IMAGE-UNVR+=$(IMAGE-UNVR-HD)

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
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-UNVR+=$(TOOLS-CONFIG)
TOOLS-UNVR+= \
    unas/al324-ee \
    unas/helper_UNVR-AL324 \
    unas/config_gu.sh \
    unas/enp0s1.network \
    unas/enp0s2.network

TOOLS-UNVR4+=$(TOOLS-UNVR)
TOOLS-UNVR-PRO+=$(TOOLS-UNVR)
TOOLS-UNVR-AI+=$(TOOLS-UNVR)
TOOLS-UNVR-HD+=$(TOOLS-UNVR)

# Project target

$(eval $(call ProductImage,UNVR4,FCD_$(PRD)_UNVR4_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UNVR-PRO,FCD_$(PRD)_UNVR-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UNVR-AI,FCD_$(PRD)_UNVR-AI_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UNVR-HD,FCD_$(PRD)_UNVR-HD_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,UNVR4,FCD_$(PRD)_UNVR4_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UNVR-PRO,FCD_$(PRD)_UNVR-PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UNVR-AI,FCD_$(PRD)_UNVR-AI_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UNVR-HD,FCD_$(PRD)_UNVR-HD_$(VER)_$(FWVER)))

# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,03137_ea20))
$(eval $(call ProductCompress2,03192_ea1a))
$(eval $(call ProductCompress2,03026_ea21))
$(eval $(call ProductCompress2,03298_ea30))
