var_uniq() {
    local var_name=$1
    local IFS=$2
    local var_value="${!var_name}"
    local -A seen=()
    local result=''
    local element
    local -a elements

    IFS=$2 read -ra elements <<< "$var_value"

    for element in "${elements[@]}"; do
            [[ -z $element ]] && continue
            if [[ -z "${seen[$element]}" ]]; then
                seen["$element"]=1
                result+="${result:+$IFS}$element"
            fi
    done
    printf '%s\n' "$result"
}

PATH=$(var_uniq PATH :)
LD_LIBRARY_PATH=$(var_uniq LD_LIBRARY_PATH :)
PYTHONPATH=$(var_uniq PYTHONPATH :)
PERL5LIB=$(var_uniq PERL5LIB :)
MANPATH=$(var_uniq MANPATH :)
INFOPATH=$(var_uniq INFOPATH :)
