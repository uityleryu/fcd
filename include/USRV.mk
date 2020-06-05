
# Images

IMAGE-SERVER=

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiServer
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

TOOLS-SERVER=$(TOOLS-CONFIG)
TOOLS-SERVER+= \
    usrv/helper_AST2500*

# Project target

$(eval $(call ProductImage,SERVER,FCD_$(PRD)_SERVER_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,SERVER,FCD_$(PRD)_SERVER_$(VER)_$(FWVER)))
