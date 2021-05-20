

IMAGE-UCKP= \
    images/e970* \
    uck-fw/RCK2.apq8053.v0.5.1.af6ba0a.210520.1440-boot.img \
    uck-fw/CK2FCD.apq8053.v0.3.1.5f2f353.180205.1651.bootimg \
    uck-fw/UCKP-2.1.11-cd332a59cf054d5fbf22837350fc84ac.rootfs \
    uck-fw/UCKP-2.1.11-cd332a59cf054d5fbf22837350fc84ac.boot

PRD_MODEL=UniFiCK
BACKT1_PRDSRL=$(PRD_MODEL)
DRVREG_PRDSRL=$(PRD_MODEL)

TOOLS-CONFIG= \
    common/sshd_config \
    common/tmux.conf \
    common/x86-64k-ee \
    common/aarch64-rpi4-64k-ee

TOOLS-UCKP= \
    uck/ck-ee \
	uck/DRA_ed0eb1b5_helper_APQ8053_release.strip \
	uck/mmc-prep.sh

# Project target

$(eval $(call ProductImage,UCKP,FCD_$(PRD)_UCKP_$(VER)_$(FWVER)))

# Project target for RPi4

$(eval $(call ProductCompress2,02570-e970))
