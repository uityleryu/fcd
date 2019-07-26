IMAGE-GBE= \
    images/dc9* \
    am-fw/GBE.* \
    am-fw/GP.* \
    am-fw/ubnthd-u-boot.rom

IMAGE-PRISMAP= \
    images/dc9* \
    am-fw/XC.*

IMAGE-AIRMAX+=$(IMAGE-GBE)
IMAGE-AIRMAX+=$(IMAGE-PRISMAP)

DIAG_MODEL=airMAX
DIAG_UI_MODEL=airMAX
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

UPYFCD_VER=
FCDIMG_VER=
UBNTLIB_VER=
TOOL_VER=

# Assign tools for every product
TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee

TOOLS-GBE= \
    am/cfg_part.bin \
    am/helper_IPQ40xx \
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

$(eval $(call ProductImage,AIRMAX,FCD-AIRMAX-ALL-$(VER)))
$(eval $(call ProductImage,GBE,FCD-AIRMAX-GBE-$(VER)-$(FWVER)))
$(eval $(call ProductImage,PRISMAP,FCD-AIRMAX-PRISMAP-$(VER)-$(FWVER)))
