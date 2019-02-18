# UDM
IMAGE-UDM-BASIC=udm-fw/ubnt_udm_all_v1_sigined_20181017_boot.img \
                udm-fw/ubnt-upgrade-compat.tgz \
                udm-fw/uImage-0.9.4-a9df305.r \
                udm-fw/uImage-0.9.5.r

IMAGE-UDM+=$(IMAGE-UDM-BASIC)
IMAGE-UDM+=images/ea11* \
          udm-fw/UDM.alpinev2.v0.9.5.f18c4d1.190128.1425.bin \

IMAGE-UDMSE+=$(IMAGE-UDM-BASIC)
IMAGE-UDMSE+=images/ea13* \
          udm-fw/UDM.alpinev2.v0.9.4+builder.836.a9df305.190115.1113.bin

IMAGE-UDMPRO+=$(IMAGE-UDM-BASIC)
IMAGE-UDMPRO+=images/ea15* \
          udm-fw/UDM.alpinev2.v0.9.4+builder.836.a9df305.190115.1113.bin

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

UPYFCD_VER=
FCDIMG_VER=
DIAG_UI_MODEL=UniFiDream
TOOLS-UDM=.tmux.conf \
      al324-ee \
      helper_AL324_release \
      evtest \
      dfu-util \
      spidev_test \
      dreammachine-se-lcm-fw.dfu \
      dreammachine-pro-lcm-fw.dfu \
      ftu_system_udm.cfg \
      ftu-tool.sh \
      ftu-tool-common.sh \
      ftu-tool-platform.sh \
      dropbear_arm64 \
      dropbearkey_arm64 \
      sshd_config \
      ubios-udapi-server.default \
      rtl8370mb_rw

TOOLS-UDMXG=.tmux.conf \
      xeon1521-ee \
      helper_XEON1521_release \
      eeupdate64e \
      dropbearkey \
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
$(eval $(call ProductImage,UDMB,FCD-UDMB-$(VER)))
$(eval $(call ProductImage,UDMALL,FCD-UDMALL-$(VER)))
