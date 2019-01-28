# UDM
IMAGE-UDM=images/ea11* \
          udm-fw/*

IMAGE-UDMSE=images/ea13* \
          udm-fw/*

IMAGE-UDMPRO=images/ea15* \
          udm-fw/*

IMAGE-UDMXG=
#IMAGE-UDMXG=images/ea17* \
#          udm-fw/*

IMAGE-UDMB=images/ec25* \
           udm-fw/udm-b-* \
           udm-fw/uap_km-uap-ramips-factory_7559_9984a40_lede-ramips-mt7621-UAP-NANO-HD-initramfs-kernel.bin \
           udm-fw/unifi-v1.0.9.57-gd7bab423_uap-mt7621-32MB_u-boot.bin \
           udm-fw/BZ.mt7621.*

IMAGE-UDMALL+=$(IMAGE-UDM)
IMAGE-UDMALL+=$(IMAGE-UDMSE)
IMAGE-UDMALL+=$(IMAGE-UDMPRO)
#IMAGE-UDMALL+=$(IMAGE-UDMXG)

DIAG_MODEL=udm

UPYFCD_VER=73e96fae471eec6d22d2660c97160094ec80996e
FCDIMG_VER=43c32d6d03b1605587eb42211868d56ed49a160a

TOOLS-UDM=.tmux.conf \
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

TOOLS-UDMXG=.tmux.conf \
      xeon1521-ee \
      helper_XEON1521_release \
      eeupdate64e \
      lib/

TOOLS-UDMALL+=$(TOOLS-UDM)
#TOOLS-UDMALL+=$(TOOLS-UDMXG)

TOOLS-UDMB=.tmux.conf \
           mt7621-ee \
           helper_UNIFI_MT7621_release

$(eval $(call ProductImage,UDM,FCD-UDM-$(VER)))
$(eval $(call ProductImage,UDMSE,FCD-UDMSE-$(VER)))
$(eval $(call ProductImage,UDMPRO,FCD-UDMPRO-$(VER)))
$(eval $(call ProductImage,UDMXG,FCD-UDMXG-$(VER)))
$(eval $(call ProductImage,UDMALL,FCD-UDMALL-$(VER)))

$(eval $(call ProductImage,UDMB,FCD-UDMB-$(VER)))
