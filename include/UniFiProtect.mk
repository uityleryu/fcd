
# Images

IMAGE-SENSE=

IMAGE-LOCK-R=

IMAGE-ULM=

TOOLS-TAG-COMBO=

TOOLS-CARD-COMBO=

IMAGE-GARAGE=

IMAGE-UFP+=$(IMAGE-SENSE)
IMAGE-UFP+=$(IMAGE-LOCK-R)
IMAGE-UFP+=$(IMAGE-TAG-COMBO)
IMAGE-UFP+=$(IMAGE-ULM)
IMAGE-UFP+=$(IMAGE-CARD-COMBO)

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

TOOLS-SENSE=$(TOOLS-UFP)

TOOLS-LOCK-R=$(TOOLS-UFP)

TOOLS-ULM=$(TOOLS-UFP)

TOOLS-GARAGE=$(TOOLS-UFP)

TOOLS-TAG-COMBO=$(TOOLS-UFP)
TOOLS-TAG-COMBO+= \
    ufp/nxp-nfc-nci

TOOLS-CARD-COMBO=$(TOOLS-UFP)
TOOLS-CARD-COMBO+= \
    ufp/nxp-nfc-nci



# Project target

$(eval $(call ProductImage,SENSE,FCD_$(PRD)_SENSE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,LOCK-R,FCD_$(PRD)_LOCK-R_$(VER)_$(FWVER)))
$(eval $(call ProductImage,TAG-COMBO,FCD_$(PRD)_TAG-COMBO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,ULM,FCD_$(PRD)_ULM_$(VER)_$(FWVER)))
$(eval $(call ProductImage,CARD-COMBO,FCD_$(PRD)_CARD-COMBO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,GARAGE,FCD_$(PRD)_UFP-GARAGE_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,SENSE,FCD_$(PRD)_SENSE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,LOCK-R,FCD_$(PRD)_LOCK-R_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,TAG-COMBO,FCD_$(PRD)_TAG-COMBO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,ULM,FCD_$(PRD)_ULM_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,CARD-COMBO,FCD_$(PRD)_CARD-COMBO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,GARAGE,FCD_$(PRD)_UFP-GARAGE_$(VER)_$(FWVER)))
