
# UDM
UDM-IMAGE=images/ea11/fcd/diag-905.tar \
          images/ea11/fw/uImage-bf97538 \
          images/ea11/fw/upgrade-0.9.0.417-gf934c2d.tar \
          images/u1-diag.tar \
          images/u1-fwcommon-uImage \
          images/u1-fwcommon-upgrade.tar

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


TOOLS=tools/al324-ee \
      tools/ax_gen_eeprom.py \
      tools/evtest \
      tools/helper_AL324_release \
      tools/helper_IPQ807x_release \
      tools/ipq807x-aarch64-ee \
