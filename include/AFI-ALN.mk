# AFi-ALN
IMAGE-AFI-ALN-R=images/da11* \
               afi-fw/*

IMAGE-AFI-ALN-P=images/da12* \
               afi-fw/*

IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-R)
IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-P)

DIAG_MODEL=afi_aln
DIAG_UI_MODEL=Amplifi

UPYFCD_VER=5e8397521210d4fde93e64e57cfc4f1c1ac94e89
FCDIMG_VER=0dffee025f079090aa65619ccab01d1cbf1cda54
UBNTLIB_VER=28999e4934c068d2c43470a34707072529485f45
TOOL_VER=bcacb75ec7305ef40068e739383c04c27074cb59
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
      as.txt

TOOLS-AFI-ALN-R=$(TOOLS-AFI-ALN)
TOOLS-AFI-ALN-P=$(TOOLS-AFI-ALN)

$(eval $(call ProductImage,AFI-ALN,FCD-AFI-ALN-$(VER)))
$(eval $(call ProductImage,AFI-ALN-R,FCD-AFI-ALN-R-$(VER)))
$(eval $(call ProductImage,AFI-ALN-P,FCD-AFI-ALN-P-$(VER)))
