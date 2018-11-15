include include/image-install.mk

# For build environmental variables
OUTDIR=$(shell pwd)/output
APP_DIR=usr/local/sbin
EXLIVECD=$(OUTDIR)/ExtractLivedCD
EXSQUASHFS=$(OUTDIR)/ExtractLivedSquashfs
STAGEDIR=$(OUTDIR)/stage
NEWLIVEDCD=$(STAGEDIR)/NewLiveCD
NEWSQUASHFS=$(STAGEDIR)/NewSquashfs

BUILD_DIR=$(shell pwd)
FCDAPP_DIR=$(BUILD_DIR)/config/includes.chroot

BASE_OS=FCD-base.iso
NEW_LABEL=UBNT_FCD
LIVE_CD_VER=$(VER).iso
FCD_ISO_NAME=FCD-$(PRD)-$(VER)

# Mount Checking LiveCD
MCLiveCD=$(shell mount | grep -o "$(EXLIVECD) type iso9660")

# Mount Checking Squaschfs
MCSQUASHFS=$(shell mount | grep -o "$(EXSQUASHFS) type squashfs")

# Create a whole new ISO from a downloaded ISO
new-rootfs: help clean prep mount_livedcd mount_livedcd_squashfs prep_new_livedcd prep_new_squashfs gitrepo

# Import and Initialize Product specific Targets
include include/$(PRD).mk

# Create a whole new ISO from a downloaded ISO
create_live_cd: help clean prep mount_livedcd mount_livedcd_squashfs prep_new_livedcd prep_new_squashfs gitrepo
	@echo " >> copy prep scripts to new squashfs "
	cp -rf $(FCDAPP_DIR)/usr/local/* $(NEWSQUASHFS)/usr/local/
	cp -rf $(FCDAPP_DIR)/srv/tftp/* $(NEWSQUASHFS)/srv/tftp/
	cp -rf $(FCDAPP_DIR)/etc/skel/Desktop/* $(NEWSQUASHFS)/etc/skel/Desktop/

	@echo ">> change the FCD version to the desktop"
	cp -f xfce-teal.jpg $(NEWSQUASHFS)/usr/share/backgrounds/xfce/xfce-teal.orig.jpg
	convert -gravity southeast -fill white -font DejaVu-Sans -pointsize 60 -draw "text 40,40 '$(VER)'" $(NEWSQUASHFS)/usr/share/backgrounds/xfce/xfce-teal.orig.jpg $(NEWSQUASHFS)/usr/share/backgrounds/xfce/xfce-teal.jpg

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
	genisoimage -r -V "$(NEW_LABEL)" -cache-inodes -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o $(OUTDIR)/$(LIVE_CD_VER) .
	chmod 777 $(OUTDIR)/$(LIVE_CD_VER)

help:
	@echo " ****************************************************************** "
	@echo "                   FCD build configuration                          "
	@echo " ****************************************************************** "
	@echo "   OUTDIR         = $(OUTDIR)"
	@echo "   EXLIVECD       = $(EXLIVECD)"
	@echo "   EXSQUASHFS     = $(EXSQUASHFS)"
	@echo "   STAGEDIR       = $(STAGEDIR)"
	@echo "   NEWLIVEDCD     = $(NEWLIVEDCD)"
	@echo "   NEWSQUASHFS    = $(NEWSQUASHFS)"
	@echo "   BUILD_DIR      = $(BUILD_DIR)"
	@echo "   FCDAPP_DIR     = $(FCDAPP_DIR)"
	@echo "   BASE_OS        = $(BASE_OS)"
	@echo " ****************************************************************** "

check_root:
	@if ! [ "$$(whoami)" = "root" ]; then \
		echo ""; \
		echo "$${UID}"; \
		echo "*******************************"; \
		echo " Please run as root!"; \
		echo " ex: sudo make <target> "; \
		echo "*******************************"; \
		echo ""; \
		exit 1; \
	fi

prep: check_root
	@echo " *** Creating all prerequisite directories *** "
ifndef VER
	@echo "fcdmaker usage:"
	@echo "example1: sudo make VER=0.9.1-d9e5388-3 -f fcdmaker32.mk fcd-UDM-new"
	@echo "example2: sudo make VER=FCD-USW-UAP-4.0.4 -f fcdmaker32.mk create_live_cd"
	@exit 1
endif
	@if [ ! -d $(EXLIVECD) ]; then \
		mkdir -p $(EXLIVECD); \
	fi
	@if [ ! -d $(EXSQUASHFS) ]; then \
		mkdir -p $(EXSQUASHFS); \
	fi
	@if [ ! -d $(STAGEDIR)/NewLiveCD ]; then \
		mkdir -p $(STAGEDIR)/NewLiveCD; \
	fi
	@if [ ! -d $(STAGEDIR)/NewSquashfs ]; then \
		mkdir -p $(STAGEDIR)/NewSquashfs; \
	fi
	@chmod -R 777 $(OUTDIR)

download_livecd:
	@if [ ! -f "$(OUTDIR)/$(BASE_OS)" ]; then \
		echo ">> Download $(BASE_OS)"; \
		cd $(OUTDIR); \
		wget $(WEBLINK)/$(BASE_OS); \
		sleep 2; \
	else \
		echo ">> ISO: $(BASE_OS) is existed"; \
	fi

mount_livedcd: check_root
	@echo " *** Mounting LivedCD ISO *** "
	mount -o loop $(OUTDIR)/$(BASE_OS) $(EXLIVECD)

mount_livedcd_squashfs: check_root
	@echo " *** Mounting LivedCD Squashfs *** "
	modprobe squashfs
	mount -t squashfs -o loop $(EXLIVECD)/live/filesystem.squashfs $(EXSQUASHFS)

prep_new_livedcd: check_root
	@echo " *** rsync LivedCD to NewliveCD in excludsive of LivedCD_Squashfs *** "
	rsync --exclude=/live/filesystem.squashfs -a $(EXLIVECD)/ $(NEWLIVEDCD)

prep_new_squashfs: check_root
	@echo " *** rsync LivedCD_Squashfs to NewliveCD_Squashfs *** "
	cp -a $(EXSQUASHFS)/* $(NEWSQUASHFS)

new_livedcd_pkg: check_root
	@echo " *** Packaging the New LiveCD *** "
	@echo "  >> Regenerating manifest files in NewLivedCD "
	chmod +w $(NEWLIVEDCD)/casper/filesystem.manifest
	chroot $(NEWSQUASHFS) dpkg-query -W --showformat='${Package} ${Version}\n' > $(NEWLIVEDCD)/casper/filesystem.manifest
	cp $(NEWLIVEDCD)/casper/filesystem.manifest $(NEWLIVEDCD)/casper/filesystem.manifest-desktop

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
	genisoimage -r -V "$(NEW_LABEL)" -cache-inodes -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o $(OUTDIR)/$(VERSION) .

gitrepo: UPyFCD

UPyFCD:
	@git clone git@10.2.128.30:Ubiquiti-BSP/$@.git -b master $(STAGEDIR)/$@
	@cd $(STAGEDIR)/$@; git reset --hard $(UPYFCD_VER)
	@rm -rf $(NEWSQUASHFS)/usr/local/sbin/DIAG
	@mv $(STAGEDIR)/$@/DIAG $(NEWSQUASHFS)/usr/local/sbin/

clean: check_root
	@echo " *** Cleaning all files under $(OUTDIR) *** "
	@echo " >> Checking if $(EXLIVECD) is mounted ... "
	@if [ -d "$(EXLIVECD)" ]; then \
		if [ "$(MCLiveCD)" != "" ]; then \
			echo " >> $(EXLIVECD) is mounted, umounting ... "; \
			umount -l $(EXLIVECD); \
		fi; \
	fi; \
	echo " >> Deleting $(EXLIVECD) ... "; \
	rm -rf $(EXLIVECD)

	@echo " >> Checking if $(EXSQUASHFS) is mounted ... "
	@if [ -d "$(EXSQUASHFS)" ]; then \
		if [ "$(MCSQUASHFS)" != "" ]; then \
			echo ">> $(EXSQUASHFS) is mounted, umounting ..."; \
			umount -fl $(EXSQUASHFS); \
		fi; \
		echo " >> Deleting $(EXSQUASHFS) ... "; \
		rm -rf $(EXSQUASHFS); \
	fi

	@echo " >> Deleting $(STAGEDIR) "
	@rm -rf $(STAGEDIR)
	@rm -rf $(OUTDIR)/$(LIVE_CD_VER)

