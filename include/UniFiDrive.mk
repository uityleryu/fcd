# Images
IMAGE-UNAS-Pro= \
    images/ea51* \
    unas/unas-pro* \
    unas/uImage \
	unas/UNAS*

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop
PRD_MODEL=UniFiDrive
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools
TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

# Project specific tools
TOOLS-UNAS+= \
    unas/al324-ee \
    unas/helper_UNVR-AL324 \
    unas/config_gu.sh \
    unas/enp0s1.network \
    unas/enp0s2.network \
    unas/nvr-lcm-tools* 

TOOLS-UNAS-Pro+=$(TOOLS-UNAS)
TOOLS-UNAS-Pro+=$(TOOLS-CONFIG)

# Project target
$(eval $(call ProductImage,UNAS-Pro,FCD_$(PRD)_UNAS-Pro_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,UNAS-Pro,FCD_$(PRD)_UNAS-Pro_$(VER)_$(FWVER)))

# Project compressed type2 file for RPi FCD host
$(eval $(call ProductCompress2,03751_ea51))
$(eval $(call ProductCompress2,03756_ea50))
