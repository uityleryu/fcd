
# Images

IMAGE-SENSE=

IMAGE-LOCK-R=

IMAGE-ULM=

TOOLS-TAG-COMBO=

TOOLS-CARD-COMBO=

IMAGE-GARAGE=

IMAGE-RADAR= \
    images/dcb0* \
    up-fw/UP-Radar*

IMAGE-KEYPAD=

IMAGE-UP-Chime= \
    images/ab12* \
    up-fw/up-chime/*

IMAGE-UFP+=$(IMAGE-SENSE)
IMAGE-UFP+=$(IMAGE-LOCK-R)
IMAGE-UFP+=$(IMAGE-TAG-COMBO)
IMAGE-UFP+=$(IMAGE-ULM)
IMAGE-UFP+=$(IMAGE-CARD-COMBO)
IMAGE-UFP+=$(IMAGE-RADAR)
IMAGE-UFP+=$(IMAGE-KEYPAD)
IMAGE-UFP+=$(IMAGE-UP-Chime)


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
    common/x86-4k-ee \
    common/aarch64-rpi4-64k-ee \
    common/aarch64-rpi4-4k-ee

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

TOOLS-RADAR=$(TOOLS-UFP)
TOOLS-RADAR+= \
    ufp_radar/helper_IPQ40xx

TOOLS-KEYPAD=$(TOOLS-UFP)

TOOLS-UP-Chime=$(TOOLS-UFP)

# Project target

$(eval $(call ProductImage,SENSE,FCD_$(PRD)_SENSE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,LOCK-R,FCD_$(PRD)_LOCK-R_$(VER)_$(FWVER)))
$(eval $(call ProductImage,TAG-COMBO,FCD_$(PRD)_TAG-COMBO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,ULM,FCD_$(PRD)_ULM_$(VER)_$(FWVER)))
$(eval $(call ProductImage,CARD-COMBO,FCD_$(PRD)_CARD-COMBO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,GARAGE,FCD_$(PRD)_UFP-GARAGE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,RADAR,FCD_$(PRD)_UFP-RADAR_$(VER)_$(FWVER)))
$(eval $(call ProductImage,KEYPAD,FCD_$(PRD)_UFP-KEYPAD_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UP-Chime,FCD_$(PRD)_UP-Chime_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,SENSE,FCD_$(PRD)_SENSE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,LOCK-R,FCD_$(PRD)_LOCK-R_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,TAG-COMBO,FCD_$(PRD)_TAG-COMBO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,ULM,FCD_$(PRD)_ULM_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,CARD-COMBO,FCD_$(PRD)_CARD-COMBO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,GARAGE,FCD_$(PRD)_UFP-GARAGE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,RADAR,FCD_$(PRD)_UFP-RADAR_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,KEYPAD,FCD_$(PRD)_UFP-KEYPAD_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UP-Chime,FCD_$(PRD)_UP-Chime_$(VER)_$(FWVER)))

# ==================================================================================================
IMAGE-a920=

# -----------------------------------------------------------------------------------------

TOOLS-a920+=$(TOOLS-CONFIG)


# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,a920,FCD_$(PRD)_a920_$(VER)_$(FWVER),$(ALL)))
