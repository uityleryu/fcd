# UDM
IMAGE-UDM=images/ea11* \
          udm-fw/*

IMAGE-UDMSE=images/ea13* \
          udm-fw/*

IMAGE-UDMPRO=images/ea15* \
          udm-fw/*

IMAGE-UDMALL+=$(IMAGE-UDM)
IMAGE-UDMALL+=$(IMAGE-UDMSE)
IMAGE-UDMALL+=$(IMAGE-UDMPRO)

DIAG_MODEL=udm

UPYFCD_VER=73e96fae471eec6d22d2660c97160094ec80996e
FCDIMG_VER=0b07082f116a03de72116a1759322a7bb879a66e

TOOLS=.tmux.conf \
      al324-ee \
      helper_AL324_release \
      evtest \
      dfu-util \
      spidev_test \
      dreammachine-se-lcm-fw.dfu \
      ftu_system_udm.cfg \
      ftu-tool.sh \
      ftu-tool-common.sh \
      ftu-tool-platform.sh \
      dropbear_arm64 \
      dropbearkey_arm64 \
      sshd_config \
      ubios-udapi-server.default


$(eval $(call ProductImage,UDM,FCD-UDM-$(VER)))
$(eval $(call ProductImage,UDMSE,FCD-UDMSE-$(VER)))
$(eval $(call ProductImage,UDMPRO,FCD-UDMPRO-$(VER)))
$(eval $(call ProductImage,UDMALL,FCD-UDMALL-$(VER)))
