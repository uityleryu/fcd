include include/images.mk
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
VER=FCD-Amplifi-[0.0.5]
LIVE_CD_VER=$(VER).iso
UPYFCD_VER=5b72f6e359f395ef874a2fabbf5fbff93a03f07f

# Mount Checking LiveCD
MCLiveCD=$(shell mount | grep -o "$(EXLIVECD) type iso9660")

# Mount Checking Squaschfs
MCSQUASHFS=$(shell mount | grep -o "$(EXSQUASHFS) type squashfs")

# UDM product line
UDM-PRODUCT-LINE=""
$(eval $(call ProductImage,UDM,FCD-UDM-$(VER),u1dm))

# Amplifi product line
AFI-PRODUCT-LINE=""
$(eval $(call ProductImage,AFI,FCD-Amplifi-$(VER),afi_ax_r))

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


# Create a whole new ISO from a downloaded ISO
new-rootfs: help clean prep mount_livedcd mount_livedcd_squashfs prep_new_livedcd prep_new_squashfs


prep: check_root
	@echo " *** Creating all prerequisite directories *** "
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
	@git clone git@github.com:Ubiquiti-BSP/$@.git -b master $(STAGEDIR)/$@
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

