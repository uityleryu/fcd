# AF

IMAGE-AF= \
    images/dc9b* \
    af-fw/*.bin

DIAG_MODEL=af

UPYFCD_VER=
FCDIMG_VER=
UBNTLIB_VER=
TOOL_VER=
DIAG_UI_MODEL=AirFiber
DIAG_MODEL=AirFiber
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

TOOLS-CONFIG= \
    common/x86-64k-ee \
    common/sshd_config \
    common/tmux.conf

TOOLS-AF+= \
    af_af60/cfg_part.bin \
    af_af60/helper_IPQ40xx \
    af_af60/id_rsa \
    af_af60/id_rsa.pub 

TOOLS-AF+=$(TOOLS-CONFIG)
TOOLS-AF+= af_ltu5/helper_UBNTAME

$(eval $(call ProductImage,AF,FCD-AF-ALL-$(VER)-$(FWVER)))
