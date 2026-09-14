
.PHONY: clean

default: all

MAKEDIRS := $(patsubst %/Makefile, %, $(shell ls */Makefile))
MAKECLEANS := $(addsuffix .clean, ${MAKEDIRS})

%.clean : %
	@-cd $< ; $(MAKE) clean

clean: ${MAKECLEANS}

default : all

lib_mods_base : qepy_modules qepy_upflib qepy_xclib qepy_fftxlib qepy_laxlib qepy_utilxlib qepy_mbd

lib_mods_pw : qepy_pw qepy_ks_solvers qepy_dft_d3 lib_mods_base

lib_mods_lr : qepy_lr_modules lib_mods_pw

qepy_atomic : lib_mods_base
	if test -d atomic; then \
	(cd atomic; $(MAKE) || exit 1) ; fi

qepy_cpv : lib_mods_base
	if test -d cpv; then \
	(cd cpv; $(MAKE) || exit 1) ; fi

qepy_dft_d3 : qepy_modules qepy_utilxlib qepy_laxlib
	if test -d dft_d3; then \
	(cd dft_d3; $(MAKE) || exit 1) ; fi

qepy_fftxlib : qepy_utilxlib
	if test -d fftxlib; then \
	(cd fftxlib; $(MAKE) || exit 1) ; fi

qepy_gww_bse : qepy_gww_gww qepy_gww_minpack lib_mods_pw
	if test -d gww_bse; then \
	(cd gww_bse; $(MAKE) || exit 1) ; fi

qepy_gww_gww : qepy_gww_minpack lib_mods_base
	if test -d gww_gww; then \
	(cd gww_gww; $(MAKE) || exit 1) ; fi

qepy_gww_head : qepy_gww_minpack qepy_phonon_ph lib_mods_lr
	if test -d gww_head; then \
	(cd gww_head; $(MAKE) || exit 1) ; fi

qepy_gww_minpack : lib_mods_base
	if test -d gww_minpack; then \
	(cd gww_minpack; $(MAKE) || exit 1) ; fi

qepy_gww_pw4gww : qepy_phonon_gamma lib_mods_lr
	if test -d gww_pw4gww; then \
	(cd gww_pw4gww; $(MAKE) || exit 1) ; fi

qepy_gww_simple : qepy_gww_gww qepy_gww_pw4gww lib_mods_pw
	if test -d gww_simple; then \
	(cd gww_simple; $(MAKE) || exit 1) ; fi

qepy_gww_simple_bse : qepy_gww_gww lib_mods_base
	if test -d gww_simple_bse; then \
	(cd gww_simple_bse; $(MAKE) || exit 1) ; fi

qepy_gww_simple_ip : qepy_gww_pw4gww lib_mods_pw
	if test -d gww_simple_ip; then \
	(cd gww_simple_ip; $(MAKE) || exit 1) ; fi

qepy_hp : lib_mods_lr
	if test -d hp; then \
	(cd hp; $(MAKE) || exit 1) ; fi

qepy_kcw : lib_mods_lr
	if test -d kcw; then \
	(cd kcw; $(MAKE) || exit 1) ; fi

qepy_kcw_pp : qepy_kcw lib_mods_lr
	if test -d kcw_pp; then \
	(cd kcw_pp; $(MAKE) || exit 1) ; fi

qepy_ks_solvers : qepy_utilxlib qepy_laxlib qepy_modules
	if ! test -f libqepy_pw.so; then cp libqepy_utilxlib.so libqepy_pw.so; fi
	if test -d ks_solvers; then \
	(cd ks_solvers; $(MAKE) || exit 1) ; fi

qepy_ks_solvers_pw :
	rm -f ks_solvers/*so
	if test -d ks_solvers; then \
	(cd ks_solvers; $(MAKE) || exit 1) ; fi

qepy_laxlib : qepy_utilxlib
	if test -d laxlib; then \
	(cd laxlib; $(MAKE) || exit 1) ; fi

qepy_lr_modules : lib_mods_pw
	if test -d lr_modules; then \
	(cd lr_modules; $(MAKE) || exit 1) ; fi

qepy_mbd : 
	if test -d mbd; then \
	(cd mbd; $(MAKE) || exit 1) ; fi

qepy_modules : qepy_upflib qepy_xclib qepy_fftxlib qepy_laxlib qepy_utilxlib qepy_mbd
	if test -d modules; then \
	(cd modules; $(MAKE) || exit 1) ; fi

qepy_neb : lib_mods_pw
	if test -d neb; then \
	(cd neb; $(MAKE) || exit 1) ; fi

qepy_phonon_gamma : lib_mods_lr
	if test -d phonon_gamma; then \
	(cd phonon_gamma; $(MAKE) || exit 1) ; fi

qepy_phonon_ph : lib_mods_lr
	if test -d phonon_ph; then \
	(cd phonon_ph; $(MAKE) || exit 1) ; fi

qepy_pioud : lib_mods_pw
	if test -d pioud; then \
	(cd pioud; $(MAKE) || exit 1) ; fi

qepy_pp : lib_mods_pw
	if test -d pp; then \
	(cd pp; $(MAKE) || exit 1) ; fi

qepy_pw : qepy_ks_solvers qepy_dft_d3 lib_mods_base
	if test -d pw; then \
	(cd pw; $(MAKE) || exit 1) ; fi
	$(MAKE) qepy_ks_solvers_pw

qepy_pwcond : lib_mods_pw
	if test -d pwcond; then \
	(cd pwcond; $(MAKE) || exit 1) ; fi

qepy_tddfpt : lib_mods_lr
	if test -d tddfpt; then \
	(cd tddfpt; $(MAKE) || exit 1) ; fi

qepy_upflib : qepy_utilxlib
	if test -d upflib; then \
	(cd upflib; $(MAKE) || exit 1) ; fi

qepy_utilxlib : 
	if test -d utilxlib; then \
	(cd utilxlib; $(MAKE) || exit 1) ; fi

qepy_xclib : qepy_upflib
	if test -d xclib; then \
	(cd xclib; $(MAKE) || exit 1) ; fi

qepy_xspectra : lib_mods_pw
	if test -d xspectra; then \
	(cd xspectra; $(MAKE) || exit 1) ; fi

all : qepy_atomic qepy_cpv qepy_gww_bse qepy_gww_head qepy_gww_simple qepy_gww_simple_bse qepy_gww_simple_ip qepy_hp qepy_kcw_pp qepy_neb qepy_pioud qepy_pp qepy_pwcond qepy_tddfpt qepy_xspectra

qepy_cetddft : lib_mods_lr
	if test -d cetddft; then \
	(cd cetddft; $(MAKE) || exit 1) ; fi

