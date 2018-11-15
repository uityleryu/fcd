
define ProductImage

image-install-$1:
	@echo " ****************************************************************** "
	@echo "   FCD ISO NAME   = $2                                              "
	@echo "   DIAG MODEL     = $(DIAG_MODEL)                                   "
	@echo " ****************************************************************** "
	@echo " >> copy prep scripts to new squashfs "
	sed -e s/FCDVERSION/$2/g $(FCDAPP_DIR)/etc/skel/Desktop/version.txt.template > $(FCDAPP_DIR)/etc/skel/Desktop/version.txt
	sed -e s/MODEL/$(DIAG_NAME)/g $(FCDAPP_DIR)/etc/skel/Desktop/DIAG.desktop.template > $(FCDAPP_DIR)/etc/skel/Desktop/DIAG.desktop
	cp -rf $(FCDAPP_DIR)/usr/local/sbin/* $(NEWSQUASHFS)/usr/local/sbin
	# copy the desktop icons to new squash folder
	cp -rf $(FCDAPP_DIR)/etc/skel/Desktop/DIAG.desktop $(NEWSQUASHFS)/etc/skel/Desktop/
	cp -rf $(FCDAPP_DIR)/etc/skel/Desktop/Factory.desktop $(NEWSQUASHFS)/etc/skel/Desktop/
	cp -rf $(FCDAPP_DIR)/etc/skel/Desktop/version.txt $(NEWSQUASHFS)/etc/skel/Desktop/
	sh include/cp2tftp.sh $(IMAGE)
	sh include/cp2tftp.sh $(TOOLS)

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

$1-update: image-install-$1 packiso-$1
$1: new-rootfs image-install-$1 packiso-$1

endef
