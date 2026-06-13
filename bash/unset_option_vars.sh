function unset-vars() {
    local line varname
    while read -r line; do
        # Match lowercase vars or single uppercase letter vars
        # exceptions: http_proxy https_proxy
        if [[ $line =~ ^[a-z][a-zA-Z0-9_]*= || $line =~ ^[A-Z]= ]]; then
            varname=${line%%=*}
            if [ "$varname" = http_proxy -o "$varname" = https_proxy ]; then
                continue
            fi
            unset "$varname"
        fi
    done < <(set)
}

unset-vars
unset line varname
