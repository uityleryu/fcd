# AFi-ALN
IMAGE-AFI-ALN-R=images/da11* \
               afi-fw/*

IMAGE-AFI-ALN-P=images/da12* \
               afi-fw/*

IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-R)
IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-P)

DIAG_MODEL=afi_aln
DIAG_UI_MODEL=Amplifi

UPYFCD_VER=04ef504c496215db2ca39c324b8943085f4b3eb6
FCDIMG_VER=9f3de24127a29bef646f352e9512838996dacc33
UBNTLIB_VER=
TOOL_VER=
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
