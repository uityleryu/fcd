# Images

IMAGE-ROVR-WAVE-CONSOLE= \
	images/ea01* \
	rovr-fw/rovr-wave-console/*


# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=RovR
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/helper_UNIFI_MT7621_release \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-ROVR-WAVE-CONSOLE=$(TOOLS-UWR)
TOOLS-ROVR-WAVE-CONSOLE+=rovr-wave-console/*

# Project target
$(eval $(call ProductImage,ROVR-WAVE-CONSOLE,FCD_$(PRD)_ROVR-WAVE-CONSOLE_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,ROVR-WAVE-CONSOLE,FCD_$(PRD)_ROVR-WAVE-CONSOLE_$(VER)_$(FWVER)))

# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,03854_ea01))