define ProductImage

$1: new-rootfs gitrepo image-install-$1 packiso-$1
$1-local: rootfs gitrepo image-install-$1 packiso-$1
$1-update: image-install-$1 packiso-$1

$1-namechk:
	python3 include/namechk.py $2

image-install-$1: $1-namechk
	@echo " ****************************************************************** "
	@echo "   FCD ISO NAME          = $2                                              "
	@echo "   PRD_MODEL             = $(PRD_MODEL)                                    "
	@echo " ****************************************************************** "
	@echo " >> copy prep scripts to new squashfs "
	cp -a $(FCDAPP_DIR)/etc/skel/Desktop/version.txt.template $(FCDAPP_DIR)/etc/skel/Desktop/version.txt
	cp -a $(FCDAPP_DIR)/etc/skel/Desktop/BackT1.desktop.template $(FCDAPP_DIR)/etc/skel/Desktop/BackT1.desktop
	cp -a $(FCDAPP_DIR)/etc/skel/Desktop/Factory.desktop.template $(FCDAPP_DIR)/etc/skel/Desktop/Factory.desktop
	sed -i s/FCDVERSION/$2/g $(FCDAPP_DIR)/etc/skel/Desktop/version.txt
	sed -i s/PRODUCTSRL/$(BACKT1_PRDSRL)/g $(FCDAPP_DIR)/etc/skel/Desktop/BackT1.desktop
	sed -i s/PRODUCTSRL/$(DRVREG_PRDSRL)/g $(FCDAPP_DIR)/etc/skel/Desktop/Factory.desktop
	cp -rf $(FCDAPP_DIR)/usr/local/sbin/* $(NEWSQUASHFS)/usr/local/sbin
	# copy the desktop icons to new squash folder
	rm -rf $(NEWSQUASHFS)/etc/skel/Desktop/*
	cp -rf $(FCDAPP_DIR)/etc/skel/Desktop/Factory.desktop $(NEWSQUASHFS)/etc/skel/Desktop/
	cp -rf $(FCDAPP_DIR)/etc/skel/Desktop/BackT1.desktop $(NEWSQUASHFS)/etc/skel/Desktop/
	cp -rf $(FCDAPP_DIR)/etc/skel/Desktop/FWLoader.desktop $(NEWSQUASHFS)/etc/skel/Desktop/
	cp -rf $(FCDAPP_DIR)/etc/skel/Desktop/Logsync.desktop $(NEWSQUASHFS)/etc/skel/Desktop/
	cp -rf $(FCDAPP_DIR)/etc/skel/Desktop/version.txt $(NEWSQUASHFS)/etc/skel/Desktop/
	rm -rf $(NEWSQUASHFS)/usr/local/sbin/ubntlib
	mkdir -p $(NEWSQUASHFS)/usr/local/sbin/ubntlib
	cp -rf $(UBNTLIB_DIR)/ubntlib/* $(NEWSQUASHFS)/usr/local/sbin/ubntlib/
	rm -rf ${NEWSQUASHFS}/srv/tftp/*
	sh include/cp2tftp.sh $(IMAGE-$1)
	sh include/tar2tftp.sh $(TOOLS-$1)

	@echo ">> change the FCD version to the desktop"
	cp -f xfce-teal.jpg $(NEWSQUASHFS)/usr/share/backgrounds/xfce/xfce-teal.orig.jpg
	convert -gravity southeast -fill white -font DejaVu-Sans -pointsize 60 -draw "text 40,40 '$2'" $(NEWSQUASHFS)/usr/share/backgrounds/xfce/xfce-teal.orig.jpg $(NEWSQUASHFS)/usr/share/backgrounds/xfce/xfce-teal.jpg

packiso-$1:
	@echo " >> Regenerating NewSquashfs file "
	if [ -f "$(NEWLIVEDCD)/live/filesystem.squashfs" ]; then \
		rm $(NEWLIVEDCD)/live/filesystem.squashfs; \
	fi
	mksquashfs $(NEWSQUASHFS) $(NEWLIVEDCD)/live/filesystem.squashfs

	@echo " >> Update MD5 sums "
	@if [ -f "$(NEWLIVEDCD)/md5sum.txt" ]; then \
		rm $(NEWLIVEDCD)/md5sum.txt; \
	fi
	bash -c "cd $(NEWLIVEDCD)/ && find . -type f -exec md5sum {} + > $(NEWLIVEDCD)/md5sum.txt"

	echo " >> Generating NewLivedCD ISO "
	cd $(NEWLIVEDCD); \
	genisoimage -r -V "$(NEW_LABEL)" -cache-inodes -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o $(OUTDIR)/$2.iso .
	chmod 777 $(OUTDIR)/$2.iso

endef
