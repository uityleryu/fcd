include include/image-install.mk

# For build environmental variables
OUTDIR      = $(shell pwd)/output
APP_DIR     = usr/local/sbin
EXLIVECD    = $(OUTDIR)/ExtractLivedCD
EXSQUASHFS  = $(OUTDIR)/ExtractLivedSquashfs
STAGEDIR    = $(OUTDIR)/stage
NEWLIVEDCD  = $(STAGEDIR)/NewLiveCD
NEWSQUASHFS = $(STAGEDIR)/NewSquashfs
BUILD_DIR   = $(shell pwd)
FCDAPP_DIR  = $(BUILD_DIR)/config/includes.chroot
FWIMG_DIR   = $(BUILD_DIR)/fcd-image
TOOLS_DIR   = $(BUILD_DIR)/fcd-script-tools
UBNTLIB_DIR = $(BUILD_DIR)/fcd-ubntlib
BASE_OS     = FCD-base.iso
NEW_LABEL   = UBNT_FCD
FCD_ISO     = $(OUTDIR)/FCD*$(VER)*.iso

# Mount Checking LiveCD
MCLiveCD=$(shell mount | grep -o "$(EXLIVECD) type iso9660")

# Mount Checking Squaschfs
MCSQUASHFS=$(shell mount | grep -o "$(EXSQUASHFS) type squashfs")

check_params: help
ifeq ($(origin PRD),undefined)
	@echo "PRD is empty, please refer help"
	@exit 1
endif
ifeq ($(origin VER),undefined)
	@echo "VER is empty, please refer help"
	@exit 1
endif

help:
	@echo " ****************************************************************** "
	@echo "                   FCD build configuration                          "
	@echo " ****************************************************************** "
	@echo "   OUTDIR         = $(OUTDIR)                                       "
	@echo "   EXLIVECD       = $(EXLIVECD)                                     "
	@echo "   EXSQUASHFS     = $(EXSQUASHFS)                                   "
	@echo "   STAGEDIR       = $(STAGEDIR)                                     "
	@echo "   NEWLIVEDCD     = $(NEWLIVEDCD)                                   "
	@echo "   NEWSQUASHFS    = $(NEWSQUASHFS)                                  "
	@echo "   BUILD_DIR      = $(BUILD_DIR)                                    "
	@echo "   FCDAPP_DIR     = $(FCDAPP_DIR)                                   "
	@echo "   FWIMG_DIR      = $(FWIMG_DIR)$(FWIMG_HASH)                      "
	@echo "   TOOLS_DIR      = $(TOOLS_DIR)$(TOOLS_HASH)                      "
	@echo "   UBNTLIB_DIR    = $(UBNTLIB_DIR)$(UBNTLIB_HASH)                  "
	@echo "   BASE_OS        = $(BASE_OS)                                      "
	@echo "   PRD            = $(PRD)                                          "
	@echo "   VER            = $(VER)                                          "
	@echo " ****************************************************************** "
	@echo "fcdmaker32 usage:"
	@echo "sudo make -f fcdmaker32.mk PRD=UDM VER=1.6.1 UDMPRO"

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

# Import and Initialize Product specific Targets
ifdef PRD
    include include/$(PRD).mk
endif   

# Create a whole new ISO from a downloaded ISO with cloning dependency libs
new-rootfs: check_params clean clean-repo prep mount_livedcd mount_livedcd_squashfs prep_new_livedcd prep_new_squashfs
# Create a whole new ISO from a downloaded ISO with existing dependency libs
rootfs: check_params clean prep mount_livedcd mount_livedcd_squashfs prep_new_livedcd prep_new_squashfs

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

gitrepo: fcd-image fcd-script-tools fcd-ubntlib

fcd-image:
	@if [ -d "$(BUILD_DIR)/$@" ]; then \
		cd $(BUILD_DIR)/$@; git pull --depth=1; \
	else \
		git clone --depth=1 git@10.2.0.33:Ubiquiti-BSP/fcd-image.git -b master $(BUILD_DIR)/$@; \
	fi
	@echo "$(BUILD_DIR)/$@ HASH: `git --git-dir $(BUILD_DIR)/$@/.git rev-parse HEAD`"

fcd-script-tools:
	@if [ -d "$(BUILD_DIR)/$@" ]; then \
		cd $(BUILD_DIR)/$@; git pull --depth=1; \
	else \
		git clone --depth=1 git@10.2.0.33:Ubiquiti-BSP/$@.git -b master $(BUILD_DIR)/$@; \
	fi
	@echo "$(BUILD_DIR)/$@ HASH: `git --git-dir $(BUILD_DIR)/$@/.git rev-parse HEAD`"

fcd-ubntlib:
	@if [ -d "$(BUILD_DIR)/$@" ]; then \
		cd $(BUILD_DIR)/$@; git pull; \
	else \
		git clone git@10.2.0.33:Ubiquiti-BSP/$@.git -b master $(BUILD_DIR)/$@; \
	fi
	@echo "$(BUILD_DIR)/$@ HASH: `git --git-dir $(BUILD_DIR)/$@/.git rev-parse HEAD`"

clean: check_root check_params
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
	@echo " >> Deleting $(FCD_ISO) "
	@rm -rf $(FCD_ISO)

clean-repo:
	@echo "Cleaning all dependency libs"
	@if [ -d $(BUILD_DIR)/fcd-image ]; then \
		rm -rf $(BUILD_DIR)/fcd-image; \
	fi
	@if [ -d $(BUILD_DIR)/fcd-ubntlib ]; then \
		rm -rf $(BUILD_DIR)/fcd-ubntlib; \
	fi
	@if [ -d $(BUILD_DIR)/fcd-script-tools ]; then \
		rm -rf $(BUILD_DIR)/fcd-script-tools; \
	fi
