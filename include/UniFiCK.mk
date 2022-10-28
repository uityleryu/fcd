

IMAGE-UCKP= \
    images/e970* \
    uck-fw/CK2FCD.apq8053.v0.6.0.8f96a48.220617.1815-boot.img \
    uck-fw/RCK2.apq8053.v0.6.0.8f96a48.220617.1815-boot.img \
    uck-fw/UCKP.apq8053.v2.5.11.b2ebfc7.220801.1419.boot \
    uck-fw/UCKP.apq8053.v2.5.11.b2ebfc7.220801.1419.rootfs

PRD_MODEL=UniFiCK
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

TOOLS-UCKP=$(TOOLS-CONFIG)
TOOLS-UCKP+= \
    uck/ck-ee \
    uck/DRA_ed0eb1b5_helper_APQ8053_release.strip \
    uck/mmc-prep.sh \
    uck/check-part.sh \
    uck/check-part.txt

# Project target

$(eval $(call ProductImage,UCKP,FCD_$(PRD)_UCKP_$(VER)_$(FWVER)))


$(eval $(call ProductImage2,02570_e970))

# Project target for RPi4

$(eval $(call ProductCompress2,02570_e960))
$(eval $(call ProductCompress2,02570_e970))
$(eval $(call ProductCompress2,01166_e990))
