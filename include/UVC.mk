







IMAGE-UVC-G4PRO= \
      uvc-fw/ubnt-aircam-fw.bin


DIAG_UI_MODEL=UniFiVideo
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)


TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee 


TOOLS-UVC+=$(TOOLS-CONFIG)


TOOLS-UVC-G4PRO+=$(TOOLS-UVC)
TOOLS-UVC-G4PRO+= \
    uvc/helper_S5L \
    uvc/m25p80.ko

$(eval $(call ProductImage,UVC-G4PRO,FCD-UVC-G4PRO-$(VER)-$(FWVER)))





