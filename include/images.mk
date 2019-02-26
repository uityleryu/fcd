
# USG
USGXG8-IMAGE=e1020.bin \
             e1020.uboot \
             e1020-fcd.kernel \
             products.txt \
             images/usg-xg-8-fw.bin \
             images/usg-xg-8-kernel \
             images/UGWXG.v4.4.30.5127046.tar \
             uboot-images/usg-xg-8.bin \
             scripts/USGXG8/mmc-prep.sh \
             scripts/USGXG8/usb-prep.sh

USGPRO4-IMAGE=e221.bin \
             e220.uboot \
             e221-fcd.kernel \
             products.txt \
             images/usg-pro-4-kernel \
             images/UGW4.v4.4.36.5146617.tar \
             uboot-images/u-boot.ER-e220.e220.5102844-g4f1145c.bin.2 \
             scripts/USGPRO4/mmc-prep.sh \
             scripts/USGPRO4/usb-prep.sh

USGPRO3-IMAGE=e120.bin \
             e120.uboot \
             e120-fcd.kernel \
             products.txt \
             images/usg-pro-3-kernel \
             images/UGW3.v4.4.36.5146617.tar \
             uboot-images/u-boot.ER-e120.e120.4674499-gfa58f5d.bin.2 \
             scripts/USGPRO3/mmc-prep.sh \
             scripts/USGPRO3/usb-prep.sh

# USW
USPRO-IMAGE=eb36.bin eb36-mfg.bin \
            eb67.bin eb67-mfg.bin \
            images/unifiswitch-us24pro-fw.bin \
            images/unifiswitch-us48pro-fw.bin \
            images/unifiswitch-us24pro-mfg.bin \
            images/unifiswitch-us48pro-mfg.bin \
            images/US.bcm5616x.feature-usw-pro-dev.9306.181102.0853-uboot-mdk.bin \
            images/US.bcm5616x.v4.0.15.9872.181229.0259-uboot.bin

TOOLS=helper_ARxxxx \
      helper_ARxxxx_musl \
      helper_ARxxxx_musl_release \
      helper_ARxxxx_release.strip \
      helper_BCM4706 \
      helper_BCM4706_release.strip.039a4f0f \
      helper_BCM5334x \
      helper_BCM5334x_release.strip.039a4f0f \
      helper_VSC7514 \
      helper_CN50xx \
      ath3k-bdaddr
