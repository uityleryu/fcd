
# Images

IMAGE-GBE= \
    images/dc9* \
    images/dca* \
    am-fw/GBE.* \
    am-fw/GP.* \
    am-fw/ubnthd-u-boot.rom \
    am-fw/gigabeam*

IMAGE-PRISMAP= \
    images/dc9* \
    am-fw/XC.*

IMAGE-AIRMAX+=$(IMAGE-GBE)
IMAGE-AIRMAX+=$(IMAGE-PRISMAP)

# Model
# This is used for adding an option in the file of BackT1.desktop
# and Factory.desktop

PRD_MODEL=airMAX
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

# Common tools

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee

# Project specific tools

TOOLS-GBE= \
    am/cfg_part.bin \
    am/helper_IPQ40xx \
    am/am_dummy_cal.bin \
    am/id_rsa \
    am/id_rsa.pub 

TOOLS-PRISMAP= \
    am/cfg_part_qca9557.bin \
    am/fl_lock \
    am/helper_ARxxxx_11ac \
    am/id_rsa \
    am/id_rsa.pub 

# Assign common tool for every model
TOOLS-GBE+=$(TOOLS-CONFIG)
TOOLS-PRISMAP+=$(TOOLS-CONFIG)

# Assign UAP series tools
TOOLS-AIRMAX+=$(TOOLS-GBE)
TOOLS-AIRMAX+=$(TOOLS-PRISMAP)

# Project target

$(eval $(call ProductImage,AIRMAX,FCD-AIRMAX-ALL-$(VER)))
$(eval $(call ProductImage,GBE,FCD-AIRMAX-GBE-$(VER)-$(FWVER)))
$(eval $(call ProductImage,PRISMAP,FCD-AIRMAX-PRISMAP-$(VER)-$(FWVER)))
