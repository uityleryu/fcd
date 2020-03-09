
# Images

IMAGE-UFP-SENSE=

IMAGE-UFP-LOCK-R=

IMAGE-UFP+=$(IMAGE-UFP-SENSE)
IMAGE-UFP+=$(IMAGE-UFP-LOCK-R)

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
    common/helper_UNIFI_MT7621_release

# Project specific tools

TOOLS-UFP+=$(TOOLS-CONFIG)

TOOLS-UFP-SENSE=$(TOOLS-UFP)

TOOLS-UFP-LOCK-R=$(TOOLS-UFP)

# Project target

$(eval $(call ProductImage,UFP-SENSE,FCD-UFP-SENSE-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UFP-LOCK-R,FCD-UFP-LOCK-R-$(VER)-$(FWVER)))
