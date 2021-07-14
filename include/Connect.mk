
# Images

IMAGE-UC-DISPLAY-7=

IMAGE-UC-DISPLAY-13=

IMAGE-UC-DISPLAY-21=

IMAGE-UC-DISPLAY-27=

IMAGE-LVDU-4-24= \
    images/ec3d* \
    images/ec41* \
    lvdu-fw/lvdu-4-fw.bin \
    lvdu-fw/LH*

IMAGE-LVDU-1= \
    images/ec48* \
    lvdu-fw/lvdu-1/*


IMAGE-LVDU+=$(IMAGE-LVDU-4-24)
IMAGE-LVDU+=$(IMAGE-LVDU-1)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=Connect
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

# Project specific tools

TOOLS-UC-DISPLAY-7+=$(TOOLS-CONFIG)
TOOLS-UC-DISPLAY-13+=$(TOOLS-CONFIG)
TOOLS-UC-DISPLAY-21+=$(TOOLS-CONFIG)
TOOLS-UC-DISPLAY-27+=$(TOOLS-CONFIG)

TOOLS-LVDU-4-24+=$(TOOLS-CONFIG)
TOOLS-LVDU-4-24+= \
    lvdu_4_24/helper*

TOOLS-LVDU-1= \
    $(TOOLS-CONFIG) \
    common/aarch64-rpi4-4k-ee

# Project target

$(eval $(call ProductImage,UC-DISPLAY-7,FCD_$(PRD)_UC-DISPLAY-7_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-DISPLAY-13,FCD_$(PRD)_UC-DISPLAY-13_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-DISPLAY-21,FCD_$(PRD)_UC-DISPLAY-21_$(VER)_$(FWVER)))
$(eval $(call ProductImage,UC-DISPLAY-27,FCD_$(PRD)_UC-DISPLAY-27_$(VER)_$(FWVER)))
$(eval $(call ProductImage,LVDU-4-24,FCD_$(PRD)_LVDU-4-24_$(VER)_$(FWVER)))
$(eval $(call ProductImage,LVDU-1,FCD_$(PRD)_LVDU-1_$(VER)_$(FWVER)))

# Project compressed file for RPi FCD host

$(eval $(call ProductCompress,UC-DISPLAY-7,FCD_$(PRD)_UC-DISPLAY-7_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-DISPLAY-13,FCD_$(PRD)_UC-DISPLAY-13_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-DISPLAY-21,FCD_$(PRD)_UC-DISPLAY-21_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,UC-DISPLAY-27,FCD_$(PRD)_UC-DISPLAY-27_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,LVDU-4-24,FCD_$(PRD)_LVDU-4-24_$(VER)_$(FWVER)))
$(eval $(call ProductCompress,LVDU-1,FCD_$(PRD)_LVDU-1_$(VER)_$(FWVER)))

# ==================================================================================================
IMAGE-03168-ef80=
IMAGE-03182-ef81=
IMAGE-03287-ef83=
IMAGE-03256-ef84=
IMAGE-03383-ef87=
IMAGE-03396-ef88=

# ---------------------------------------------------------------------------------------------------

TOOLS-03168-ef80=$(TOOLS-CONFIG)
TOOLS-03182-ef81=$(TOOLS-CONFIG)
TOOLS-03287-ef83=$(TOOLS-CONFIG)
TOOLS-03256-ef84=$(TOOLS-CONFIG)
TOOLS-03383-ef87=$(TOOLS-CONFIG)
TOOLS-03396-ef88=$(TOOLS-CONFIG)


# ==================================================================================================
# Product series definition
# ==================================================================================================

IMAGE-UCD-SERIES+=$(IMAGE-03168-ef80)
IMAGE-UCD-SERIES+=$(IMAGE-03182-ef81)
IMAGE-UCD-SERIES+=$(IMAGE-03287-ef83)
IMAGE-UCD-SERIES+=$(IMAGE-03256-ef84)
IMAGE-UCD-SERIES+=$(IMAGE-03383-ef87)
IMAGE-UCD-SERIES+=$(IMAGE-03396-ef88)

TOOLS-UCD-SERIES+=$(TOOLS-03168-ef80)
TOOLS-UCD-SERIES+=$(TOOLS-03182-ef81)
TOOLS-UCD-SERIES+=$(TOOLS-03287-ef83)
TOOLS-UCD-SERIES+=$(TOOLS-03256-ef84)
TOOLS-UCD-SERIES+=$(TOOLS-03383-ef87)
TOOLS-UCD-SERIES+=$(TOOLS-03396-ef88)

PRODUCT-UCD-SERIES+=03168-ef80
PRODUCT-UCD-SERIES+=03182-ef81
PRODUCT-UCD-SERIES+=03287-ef83
PRODUCT-UCD-SERIES+=03256-ef84
PRODUCT-UCD-SERIES+=03383-ef87
PRODUCT-UCD-SERIES+=03396-ef88

# Project compressed type2 file for RPi FCD host

$(eval $(call ProductCompress2,03168-ef80))
$(eval $(call ProductCompress2,03182-ef81))
$(eval $(call ProductCompress2,03287-ef83))
$(eval $(call ProductCompress2,03256-ef84))
$(eval $(call ProductCompress2,03383-ef87))
$(eval $(call ProductCompress2,03396-ef88))
$(eval $(call ProductCompress2,UCD-SERIES))
