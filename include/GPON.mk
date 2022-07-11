
# Images
IMAGE-UF-WiFi6= \
    images/eec5* \
    uf-fw/* 

IMAGE-GPON+=$(IMAGE-UF-WiFi6)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop
PRD_MODEL=GPON
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools
TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

# Project specific tools
TOOLS-UF-WiFi6+=$(TOOLS-CONFIG)
TOOLS-UF-WiFi6+= \
    uf_wifi6/helper_ECNT7528_debug

# ALL
TOOLS-GPON+=$(TOOLS-CONFIG)
TOOLS-US-GEN1+=$(TOOLS-GPON)

# Project target
$(eval $(call ProductImage,UF-WiFi6,FCD_$(PRD)_UF-WiFi6_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,UF-WiFi6,FCD_$(PRD)_UF-WiFi6_$(VER)_$(FWVER)))

# Project compressed type2 file for RPi FCD host
$(eval $(call ProductCompress2,03376_eec5))
$(eval $(call ProductCompress2,03685_eec8))
