CP:=cp
TAR:=tar
RM:=rm
MKDIR:=mkdir

CDBUILDDIR ?= ~/live_cdx_3.0
ROOT = $(CDBUILDDIR)/edit
BINDIR := usr/local/sbin
TFTPDIR := tftpboot
SHORTCUTDIR := etc/skel/Desktop

all:
	@echo "Building uap"
	@./gen_build_properties.sh $(CDBUILDDIR)/build.properties $(BRANCH)
	$(CP) $(CDBUILDDIR)/build.properties $(ROOT)/lib
	(cd target ; $(TAR) cf - * | $(TAR) xf - -C $(CDBUILDDIR) ; cd -)
	@(eval `cat $(CDBUILDDIR)/build.properties`; \
	if [ "$${scm_dirty}" != "true" ]; then \
		SCMVER=$${scm_refname}_$${scm_distance}; \
	else \
		SCMVER=$${scm_refname}_$${scm_distance}_$${build_user}_$${build_host}_`date -d "$${build_date} $${build_time}" +%y%m%d_%H%M`; \
	fi; \
	for f in `ls target/edit/$(BINDIR)`; do \
		[ ! -f $$f ] || sed -i "s,SCMVER,$${SCMVER},g" $(ROOT)/$(BINDIR)/$$f; \
	done)
	./make_readme.sh $(CDBUILDDIR)
	$(CP) build-cd.sh $(CDBUILDDIR)

clean:
	$(RM) -fr $(ROOT)/$(TFTPDIR)/*
	$(RM) -fr $(ROOT)/$(BINDIR)/*
	$(RM) -fr $(ROOT)/$(SHORTCUTDIR)/*

