# AFi-AX
IMAGE-AFI-AX-R=images/da11* \
               afi-fw/*

IMAGE-AFI-AX-P=images/da12* \
               afi-fw/*

IMAGE-AFI-AX+=$(IMAGE-AFI-AX-R)
IMAGE-AFI-AX+=$(IMAGE-AFI-AX-P)

DIAG_MODEL=afi_aln

UPYFCD_VER=fc1f83db144854329575dd44fb190831eccfe656
FCDIMG_VER=ee721f686c4e5dffa121f67cf7209a9504a23433

TOOLS-AFI-AX=.tmux.conf \
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

TOOLS-AFI-AX-R=$(TOOLS-AFI-AX)
TOOLS-AFI-AX-P=$(TOOLS-AFI-AX)

$(eval $(call ProductImage,AFI-AX,FCD-AFI-AX-$(VER)))
$(eval $(call ProductImage,AFI-AX-R,FCD-AFI-AX-R-$(VER)))
$(eval $(call ProductImage,AFI-AX-P,FCD-AFI-AX-P-$(VER)))
