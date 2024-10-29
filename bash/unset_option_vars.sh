function unset-vars() {
    local line varname
    while read -r line; do
        # Match lowercase vars or single uppercase letter vars
        if [[ $line =~ ^[a-z][a-zA-Z0-9_]*= || $line =~ ^[A-Z]= ]]; then
            varname=${line%%=*}
            unset "$varname"
        fi
    done < <(set)
}

unset-vars
unset line varname
