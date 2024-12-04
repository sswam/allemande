check-for-bugs() {
    model="$1"
    echo "Checking for bugs using $(model-name "$model") ..."
    if [ -e "$review" ]; then
        echo >&2 "Code review already exists: $review, moving it to rubbish."
        $MR "$review"
    fi
    run-git-diff --color
    run-git-diff | proc -m="$model" "Please carefully review this patch with a fine-tooth comb
Answer LGTM if it is bug-free and you see no issues, or list bugs still present
in the patched code. Do NOT list bugs in the original code that are fixed by
the patch. Also list other issues or suggestions if they seem worthwhile.
Especially, check for sensitive information such as private keys or email
addresses that should not be committed to git. Adding the author's email
deliberately is okay. Also note any grossly bad code or gross inefficiencies.
If you don't find anything wrong, just say 'LGTM' only, so as not to waste both of our time. Thanks!

Expected format:

1. bug or issue
2. another bug or issue

or if nothing is wrong, please just wrte 'LGTM'.
" | fmt -s -w 78 -g 78 | tee "$review"
    echo
}

    if [ "$initial_bug_check" -eq 1 ]; then
        check-for-bugs "$model"
    fi
