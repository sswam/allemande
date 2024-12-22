var_uniq() {
	local var=$1
	local old_IFS=$IFS
	IFS=$2
	lecho ${!var} | uniqo | grep . | tr '\n' "$IFS" | sed "s/$IFS$//"
	IFS=$old_IFS
}

PATH=$(var_uniq PATH :)
LD_LIBRARY_PATH=$(var_uniq LD_LIBRARY_PATH :)
PYTHONPATH=$(var_uniq PYTHONPATH :)
PERL5LIB=$(var_uniq PERL5LIB :)
MANPATH=$(var_uniq MANPATH :)
INFOPATH=$(var_uniq INFOPATH :)
