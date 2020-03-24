
# Images

IMAGE-UNMS-R-PRO= \
    images/ee6a* \
    unms-fw/ubnt_unmsr_rev1_boot.img \
    unms-fw/UNMSR.* \

IMAGE-UNMS+=$(IMAGE-UNMS-R-PRO)
# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UbiquitiNMS
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee

# Project specific tools

TOOLS-UNMS+=$(TOOLS-CONFIG)
TOOLS-UNMS+= unms/*

TOOLS-UNMS-R-PRO=$(TOOLS-UNMS)

# Project target

$(eval $(call ProductImage,UNMS,FCD-UNMS-$(VER)-$(FWVER)))
$(eval $(call ProductImage,UNMS-R-PRO,FCD-UNMS-R-PRO-$(VER)-$(FWVER)))
