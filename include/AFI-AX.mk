# AFi-AX
IMAGE-AFI-AX-R=images/da11* \
               afi-fw/*

IMAGE-AFI-AX-P=images/da12* \
               afi-fw/*

IMAGE-AFI-AX+=$(IMAGE-AFI-AX-R)
IMAGE-AFI-AX+=$(IMAGE-AFI-AX-P)

DIAG_MODEL=afi_ax_r

UPYFCD_VER=4416bf52c96e2ba0977e4a9858ac3aab4f9a53eb
FCDIMG_VER=

TOOLS=.tmux.conf \
      ax_gen_eeprom.py \
      evtest \
      helper_IPQ807x_release \
      ipq807x-aarch64-ee \
      sshd_config \
      stop_daemons.sh \
      DUT_wireless \
      golden_ax_dev.sh \
      Golden_wireless \
      as.txt

$(eval $(call ProductImage,AFI-AX,FCD-AFI-AX-$(VER)))
$(eval $(call ProductImage,AFI-AX-R,FCD-AFI-AX-R-$(VER)))
$(eval $(call ProductImage,AFI-AX-P,FCD-AFI-AX-P-$(VER)))
