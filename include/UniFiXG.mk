
# Images

IMAGE-UXGLITE= \
    images/b080* \
	uxg-fw/uxg-lite-20200905-uImage \
	uxg-fw/UXG.mt7622.v0.4.0-pre+ubnt.3142.00a2f2c.200903.1424.bin

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiXG
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

TOOLS-UXGLITE+=$(TOOLS-CONFIG)
TOOLS-UXGLITE+= uxg/*

# Project target

$(eval $(call ProductImage,UXGLITE,FCD_$(PRD)_UXGLITE_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,UXGLITE,FCD_$(PRD)_UXGLITE_$(VER)_$(FWVER)))


# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,00778_b080))
