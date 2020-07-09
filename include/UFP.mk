
# Images

IMAGE-UFP-SENSE=

IMAGE-UFP-LOCK-R=

TOOLS-UFP-TAG-COMBO=

IMAGE-UFP+=$(IMAGE-UFP-SENSE)
IMAGE-UFP+=$(IMAGE-UFP-LOCK-R)
IMAGE-UFP+=$(IMAGE-UFP-TAG-COMBO)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiProtect
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

TOOLS-UFP+=$(TOOLS-CONFIG)

TOOLS-UFP-SENSE=$(TOOLS-UFP)

TOOLS-UFP-LOCK-R=$(TOOLS-UFP)

TOOLS-UFP-TAG-COMBO=$(TOOLS-UFP)
TOOLS-UFP-TAG-COMBO+= \
    ufp/nxp-nfc-nci





# Project target

$(eval $(call ProductImage,UFP-SENSE,FCD_$(PRD)_UFP-SENSE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UFP-LOCK-R,FCD_$(PRD)_UFP-LOCK-R_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UFP-TAG-COMBO,FCD_$(PRD)_UFP-TAG-COMBO_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,UFP-SENSE,FCD_$(PRD)_UFP-SENSE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UFP-LOCK-R,FCD_$(PRD)_UFP-LOCK-R_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UFP-TAG-COMBO,FCD_$(PRD)_UFP-TAG-COMBO_$(VER)_$(FWVER)))

