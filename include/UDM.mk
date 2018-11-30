# UDM
IMAGE-UDM=images/ea11* \
          images/ea13* \
          images/ea15* \
          udm-fw/*

DIAG_MODEL=u1dm

UPYFCD_VER=49250ead9440898ef66a569ee4ff042e69b9175e
FCDIMG_VER=af4719c10ef69a3109dbe2d859bb94c9f5f05abc

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
