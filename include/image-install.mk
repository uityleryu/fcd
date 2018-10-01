
define ProductImage
USW-PRODUCT-LINE+=image-install-$1

image-install-$1:
	@echo " ****************************************************************** "
	@echo "   FCD ISO NAME   = $3"
	@echo " ****************************************************************** "
	@echo " >> copy prep scripts to new squashfs "
	rm -rf $(NEWSQUASHFS)/usr/local/ubnt-expect/*
	rm -rf $(NEWSQUASHFS)/usr/local/sbin/*
	rm -rf $(NEWSQUASHFS)/srv/tftp/*
	mkdir -p $(NEWSQUASHFS)/srv/tftp/images
	mkdir -p $(NEWSQUASHFS)/srv/tftp/uboot-images
	mkdir -p $(NEWSQUASHFS)/srv/tftp/scripts/$1
	cp -rf $(FCDAPP_DIR)/usr/local/sbin/* $(NEWSQUASHFS)/usr/local/sbin
	cp -rf $(FCDAPP_DIR)/usr/local/ubnt-expect/* $(NEWSQUASHFS)/usr/local/ubnt-expect
	cp -rf $(FCDAPP_DIR)/etc/skel/Desktop/* $(NEWSQUASHFS)/etc/skel/Desktop/
	for image in $2; do \
		cp -rfp $(FCDAPP_DIR)/srv/tftp/$$$$image $(NEWSQUASHFS)/srv/tftp/$$$$image; \
	done
	for tool in $(TOOLS); do \
		cp -rfp $(FCDAPP_DIR)/srv/tftp/$$$$tool $(NEWSQUASHFS)/srv/tftp/$$$$tool; \
	done

	@echo ">> change the FCD version to the desktop"
	cp -f xfce-teal.jpg $(NEWSQUASHFS)/usr/share/backgrounds/xfce/xfce-teal.orig.jpg
	convert -gravity southeast -fill white -font DejaVu-Sans -pointsize 60 -draw "text 40,40 '$3'" $(NEWSQUASHFS)/usr/share/backgrounds/xfce/xfce-teal.orig.jpg $(NEWSQUASHFS)/usr/share/backgrounds/xfce/xfce-teal.jpg


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
	genisoimage -r -V "$(NEW_LABEL)" -cache-inodes -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o $(OUTDIR)/$3.iso .
	chmod 777 $(OUTDIR)/$3.iso

fcd-$1: new-rootfs image-install-$1 packiso-$1
endef


