# AFi-ALN
IMAGE-AFI-ALN-R= \
    images/da11* \
    afi-fw/*

IMAGE-AFI-ALN-P= \
    images/da12* \
    afi-fw/*

IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-R)
IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-P)

DIAG_MODEL=afi_aln
DIAG_UI_MODEL=Amplifi
BACKT1_PRDSRL=$(DIAG_UI_MODEL)
DRVREG_PRDSRL=$(DIAG_UI_MODEL)

UPYFCD_VER=
FCDIMG_VER=5679ffe77adc14be8f7a3750f27ab65b21844f9a
UBNTLIB_VER=
TOOL_VER=67077d1b6f0302a09701a6d8c9e77559b7b26ea6

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf

TOOLS-AFI-ALN+=$(TOOLS-CONFIG)
TOOLS-AFI-ALN+= afi_aln/*

TOOLS-AFI-ALN-R=$(TOOLS-AFI-ALN)
TOOLS-AFI-ALN-P=$(TOOLS-AFI-ALN)

$(eval $(call ProductImage,AFI-ALN,FCD-AFI-ALN-$(VER)))
$(eval $(call ProductImage,AFI-ALN-R,FCD-AFI-ALN-R-$(VER)))
$(eval $(call ProductImage,AFI-ALN-P,FCD-AFI-ALN-P-$(VER)))
