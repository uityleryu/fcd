# AFi-AX
IMAGE-AFI-ALN-R=images/da11* \
               afi-fw/*

IMAGE-AFI-ALN-P=images/da12* \
               afi-fw/*

IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-R)
IMAGE-AFI-ALN+=$(IMAGE-AFI-ALN-P)

DIAG_MODEL=afi_aln

UPYFCD_VER=38b40fee823617b1314484ced88437f34a0cbf09
FCDIMG_VER=ce2b541fabe05c95418894046ad337f582f7d83b

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
