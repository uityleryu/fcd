IMAGE-GBE= \
    images/dc9* \
    am-fw/GBE.* \
    am-fw/GP.* \
    am-fw/ubnthd-u-boot.rom


IMAGE-AIRMAX+=$(IMAGE-GBE)

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

# Assign common tool for every model
TOOLS-GBE+=$(TOOLS-CONFIG)

# Assign UAP series tools
TOOLS-AIRMAX+=$(TOOLS-GBE)

$(eval $(call ProductImage,AIRMAX,FCD-AIRMAX-ALL-$(VER)))
$(eval $(call ProductImage,GBE,FCD-AIRMAX-GBE-$(VER)-$(FWVER)))
