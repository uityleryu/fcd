
# Images

IMAGE-UVC-G4PRO= \
    images/a563* \
    uvc-fw/g4pro.*

IMAGE-UVC-G3BATTERY= \
    images/a580* \
    uvc-fw/uvc.s2lb.*

IMAGE-UVC-G4PTZ= \
    images/a564* \
    uvc-fw/g4ptz.*


IMAGE-UVC-G4DOORBELL= \
    images/a571* \
    uvc-fw/g4db.*

IMAGE-UVC-G4BULLET= \
    images/a572* \
    uvc-fw/g4bullet.*

IMAGE-UVC-G4DOME= \
    images/a573* \
    uvc-fw/g4dome.*

IMAGE-UVC-G4DOORBELLPRO= \
    images/a574* \
    uvc-fw/g4dbpro.*

IMAGE-UVC-AI360= \
    images/a5a0* \
    uvc-fw/ai360.*

IMAGE-UVC-AIBULLET= \
    images/a5a2* \
    uvc-fw/aibullet.*

IMAGE-UVC-G3MINI= \
    images/a590* \
    uvc-fw/g3ins.*

IMAGE-UVC-G4INS= \
    images/a595* \
    uvc-fw/g4ins.*

IMAGE-UVC-G3FLEX= \
    images/a534* \
    uvc-fw/g3flex.*

IMAGE-UVC-G4FLOODLIGHTBATTERY= \
    images/a596* \
    uvc-fw/g4flb.*

IMAGE-UVC-G4DOORBELLBATTERY= \
    images/a597* \
    uvc-fw/g4dbb.*

IMAGE-UVC-G5BULLET= \
    images/a591* \
    uvc-fw/g5bullet.*

IMAGE-UVC-G5DOME= \
    images/a592* \
    uvc-fw/g5dome.*

IMAGE-UVC-G5FLEX= \
    images/a593* \
    uvc-fw/g5flex.*

IMAGE-UVC-G4DOORBELLPROPOE= \
    images/a575* \
    uvc-fw/g4dbpropoe.*

IMAGE-UNIFI-WAVEROVECAMERA= \
    images/a594* \
    uvc-fw/waverovecam.*

IMAGE-UVC-AIPRO= \
    images/a5a4* \
    uvc-fw/aipro.*

IMAGE-UVC-G5PRO= \
    images/a598* \
    uvc-fw/g5pro.*

IMAGE-UVC+=$(IMAGE-UVC-G4PRO)
IMAGE-UVC+=$(IMAGE-UVC-G3BATTERY)
IMAGE-UVC+=$(IMAGE-UVC-G4PTZ)
IMAGE-UVC+=$(IMAGE-UVC-G4DOORBELL)
IMAGE-UVC+=$(IMAGE-UVC-G4BULLET)
IMAGE-UVC+=$(IMAGE-UVC-G4DOME)
IMAGE-UVC+=$(IMAGE-UVC-G4DOORBELLPRO)
IMAGE-UVC+=$(IMAGE-UVC-AI360)
IMAGE-UVC+=$(IMAGE-UVC-AIBULLET)
IMAGE-UVC+=$(IMAGE-UVC-G3MINI)
IMAGE-UVC+=$(IMAGE-UVC-G4INS)
IMAGE-UVC+=$(IMAGE-UVC-G3FLEX)
IMAGE-UVC+=$(IMAGE-UVC-G4FLOODLIGHTBATTERY)
IMAGE-UVC+=$(IMAGE-UVC-G4DOORBELLBATTERY)
IMAGE-UVC+=$(IMAGE-UVC-G5BULLET)
IMAGE-UVC+=$(IMAGE-UVC-G5DOME)
IMAGE-UVC+=$(IMAGE-UVC-G5FLEX)
IMAGE-UVC+=$(IMAGE-UVC-G4DOORBELLPROPOE)
IMAGE-UVC+=$(IMAGE-UNIFI-WAVEROVECAMERA)
IMAGE-UVC+=$(IMAGE-UVC-AIPRO)
IMAGE-UVC+=$(IMAGE-UVC-G5PRO)
# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=UniFiVideo
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-UVC+=$(TOOLS-CONFIG)

TOOLS-UVC-G4PRO+=$(TOOLS-UVC)
TOOLS-UVC-G4PRO+= \
    uvc/helper_S5L_g4pro \
    uvc/m25p80_g4pro.ko \
    uvc/128k_ff.bin

TOOLS-UVC-G3BATTERY+=$(TOOLS-UVC)
TOOLS-UVC-G3BATTERY+= \
    uvc/helper_S2LM_g3battery \
    uvc/m25p80_g3battery.ko \
    uvc/eegen-ascii_g3battery.bin

TOOLS-UVC-G4PTZ+=$(TOOLS-UVC)
TOOLS-UVC-G4PTZ+= \
    uvc/helper_uvcg4ptz \
    uvc/m25p80_uvcg4ptz.ko \
    uvc/128k_ff.bin

TOOLS-UVC-G4DOORBELL+=$(TOOLS-UVC)
TOOLS-UVC-G4DOORBELL+= \
    uvc/helper_uvcg4doorbell \
    uvc/m25p80_uvcg4doorbell.ko \
    uvc/128k_ff.bin


TOOLS-UVC-G4BULLET+=$(TOOLS-UVC)
TOOLS-UVC-G4BULLET+= \
    uvc/helper_uvcg4bullet \
    uvc/m25p80_uvcg4bullet.ko \
    uvc/128k_ff.bin


TOOLS-UVC-G4DOME+=$(TOOLS-UVC)
TOOLS-UVC-G4DOME+= \
    uvc/helper_uvcg4dome \
    uvc/m25p80_uvcg4dome.ko \
    uvc/128k_ff.bin


TOOLS-UVC-G4DOORBELLPRO+=$(TOOLS-UVC)
TOOLS-UVC-G4DOORBELLPRO+= \
    uvc/helper_uvcg4doorbellpro \
    uvc/m25p80_uvcg4doorbellpro.ko \
    uvc/128k_ff.bin

TOOLS-UVC-AI360+=$(TOOLS-UVC)
TOOLS-UVC-AI360+= \
    uvc/helper_uvcai360 \
    uvc/128k_ff.bin

TOOLS-UVC-AIBULLET+=$(TOOLS-UVC)
TOOLS-UVC-AIBULLET+= \
    uvc/128k_ff.bin

TOOLS-UVC-G3MINI+=$(TOOLS-UVC)
TOOLS-UVC-G3MINI+= \
    uvc/helper_uvcg3flexmini \
    uvc/m25p80_uvcg3flexmini.ko \
    uvc/128k_ff.bin

TOOLS-UVC-G4INS+=$(TOOLS-UVC)
TOOLS-UVC-G4INS+= \
    uvc/helper_uvcg4ins \
    uvc/m25p80_uvcg4ins.ko \
    uvc/128k_ff.bin

TOOLS-UVC-G4FLOODLIGHTBATTERY+=$(TOOLS-UVC)
TOOLS-UVC-G4FLOODLIGHTBATTERY+= \
    uvc/128k_ff.bin

TOOLS-UVC-G4DOORBELLBATTERY+=$(TOOLS-UVC)
TOOLS-UVC-G4DOORBELLBATTERY+= \
    uvc/128k_ff.bin

TOOLS-UVC-G5BULLET+=$(TOOLS-UVC)
TOOLS-UVC-G5BULLET+= \
    uvc/128k_ff.bin

TOOLS-UVC-G3FLEX+=$(TOOLS-UVC)
TOOLS-UVC-G3FLEX+= \
    uvc/128k_ff.bin

TOOLS-UVC-G5DOME+=$(TOOLS-UVC)
TOOLS-UVC-G5DOME+= \
    uvc/128k_ff.bin

TOOLS-UVC-G5FLEX+=$(TOOLS-UVC)
TOOLS-UVC-G5FLEX+= \
    uvc/128k_ff.bin

TOOLS-UVC-G4DOORBELLPROPOE+=$(TOOLS-UVC)
TOOLS-UVC-G4DOORBELLPROPOE+= \
    uvc/128k_ff.bin

TOOLS-UNIFI-WAVEROVECAMERA+=$(TOOLS-UVC)
TOOLS-UNIFI-WAVEROVECAMERA+= \
    uvc/128k_ff.bin

TOOLS-UVC-AIPRO+=$(TOOLS-UVC)
TOOLS-UVC-AIPRO+= \
    uvc/128k_ff.bin

TOOLS-UVC-G5PRO+=$(TOOLS-UVC)
TOOLS-UVC-G5PRO+= \
    uvc/128k_ff.bin

# Project target
$(eval $(call ProductImage,UVC-G4PRO,FCD_$(PRD)_G4PRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G3BATTERY,FCD_$(PRD)_G3BATTERY_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G4PTZ,FCD_$(PRD)_G4PTZ_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G4DOORBELL,FCD_$(PRD)_G4DOORBELL_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G4BULLET,FCD_$(PRD)_G4BULLET_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G4DOME,FCD_$(PRD)_G4DOME_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G4DOORBELLPRO,FCD_$(PRD)_G4DOORBELLPRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-AI360,FCD_$(PRD)_AI360_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-AIBULLET,FCD_$(PRD)_AIBULLET_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G3MINI,FCD_$(PRD)_G3MINI_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G4INS,FCD_$(PRD)_G4INS_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G3FLEX,FCD_$(PRD)_G3FLEX_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G4FLOODLIGHTBATTERY,FCD_$(PRD)_G4FLOODLIGHTBATTERY_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G4DOORBELLBATTERY,FCD_$(PRD)_G4DOORBELLBATTERY_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G5BULLET,FCD_$(PRD)_G5BULLET_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G5DOME,FCD_$(PRD)_G5DOME_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G5FLEX,FCD_$(PRD)_G5FLEX_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G4DOORBELLPROPOE,FCD_$(PRD)_G4DOORBELLPROPOE_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UNIFI-WAVEROVECAMERA,FCD_$(PRD)_WAVEROVECAMERA_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-AIPRO,FCD_$(PRD)_AIPRO_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UVC-G5PRO,FCD_$(PRD)_G5PRO_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host
$(eval $(call ProductCompress,UVC-G4PRO,FCD_$(PRD)_G4PRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G3BATTERY,FCD_$(PRD)_G3BATTERY_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G4PTZ,FCD_$(PRD)_G4PTZ_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G4DOORBELL,FCD_$(PRD)_G4DOORBELL_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G4BULLET,FCD_$(PRD)_G4BULLET_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G4DOME,FCD_$(PRD)_G4DOME_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G4DOORBELLPRO,FCD_$(PRD)_G4DOORBELLPRO_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-AI360,FCD_$(PRD)_AI360_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-AIBULLET,FCD_$(PRD)_AIBULLET_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G3MINI,FCD_$(PRD)_G3MINI_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G4INS,FCD_$(PRD)_G4INS_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-AITHETA,FCD_$(PRD)_AITHETA_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-DSLRBULLET,FCD_$(PRD)_DSLRBULLET_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G3FLEX,FCD_$(PRD)_G3FLEX_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G4FLOODLIGHTBATTERY,FCD_$(PRD)_G4FLOODLIGHTBATTERY_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G4DOORBELLBATTERY,FCD_$(PRD)_G4DOORBELLBATTERY_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G5BULLET,FCD_$(PRD)_G5BULLET_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G5DOME,FCD_$(PRD)_G5DOME_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G5FLEX,FCD_$(PRD)_G5FLEX_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UVC-G4DOORBELLPROPOE,FCD_$(PRD)_G4DOORBELLPROPOE_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UNIFI-WAVEROVECAMERA,FCD_$(PRD)_WAVEROVECAMERA_$(VER)_$(FWVER)))
# Project compressed type2 file for RPi FCD host
$(eval $(call ProductCompress2,03268_a5a0))
$(eval $(call ProductCompress2,02574_a563))
$(eval $(call ProductCompress2,03194_a574))
$(eval $(call ProductCompress2,02967_a564))
$(eval $(call ProductCompress2,02987_a572))
$(eval $(call ProductCompress2,03346_a595))
$(eval $(call ProductCompress2,03132_a590))
$(eval $(call ProductCompress2,02712_a571))
$(eval $(call ProductCompress2,02998_a573))
$(eval $(call ProductCompress2,02692_a580))
$(eval $(call ProductCompress2,03422_a5a3))
$(eval $(call ProductCompress2,03377_a5b0))
$(eval $(call ProductCompress2,02591_a534))
$(eval $(call ProductCompress2,03815_a591))
$(eval $(call ProductCompress2,03455_a596))
$(eval $(call ProductCompress2,03465_a597))