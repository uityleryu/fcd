
# USG
USGXG8-IMAGE=e1020.bin \
             e1020.uboot \
             e1020-fcd.kernel \
             products.txt \
             images/usg-xg-8-fw.bin \
             images/usg-xg-8-kernel \
             images/UGWXG.v4.4.28.5118795.tar \
             uboot-images/usg-xg-8.bin \
             scripts/mmc-prep.sh \
             scripts/usb-prep.sh

# USW
USPRO-IMAGE=eb36.bin eb36-mfg.bin \
            eb67.bin eb67-mfg.bin \
            images/unifiswitch-us24pro-fw.bin \
            images/unifiswitch-us48pro-fw.bin \
            images/unifiswitch-us24pro-mfg.bin \
            images/unifiswitch-us48pro-mfg.bin \
            images/US.bcm5616x.feature-usw-pro-dev.9260.180917.1531-uboot.bin \
            images/US.bcm5616x.feature-usw-pro-dev.9260.180917.1542-mfg-uboot-mdk.bin

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
