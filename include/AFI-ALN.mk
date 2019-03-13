# AFi-ALN
IMAGE-AFI-ALN-R=images/da11* \
               afi-fw/*

IMAGE-AFI-ALN-P=images/da12* \
               afi-fw/*

IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-R)
IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-P)

DIAG_MODEL=afi_aln
DIAG_UI_MODEL=Amplifi

UPYFCD_VER=3f2a5bc9e913712d5bc0dc12ea571e02b473e078
FCDIMG_VER=0dffee025f079090aa65619ccab01d1cbf1cda54
UBNTLIB_VER=72b30eac32ad2f7af7031028bfb3a1461c7573e0
TOOL_VER=74c8923269a05dceb708134b9d14aa6de231a193
TOOLS-AFI-ALN=.tmux.conf \
      ax_gen_eeprom.py \
      evtest \
      helper_IPQ807x_release \
      ipq807x-aarch64-ee \
      sshd_config \
      stop_daemons.sh \
      DUT_wireless_radio0 \
      DUT_wireless_radio1 \
      DUT_wireless_radio2 \
      golden_ax_dev.sh \
      afi_aln_image \
      as.txt

TOOLS-AFI-ALN-R=$(TOOLS-AFI-ALN)
TOOLS-AFI-ALN-P=$(TOOLS-AFI-ALN)

$(eval $(call ProductImage,AFI-ALN,FCD-AFI-ALN-$(VER)))
$(eval $(call ProductImage,AFI-ALN-R,FCD-AFI-ALN-R-$(VER)))
$(eval $(call ProductImage,AFI-ALN-P,FCD-AFI-ALN-P-$(VER)))
