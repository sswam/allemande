#!/usr/bin/env bash

# Amends a previous commit using interactive rebase

git-amend-old() {
	dry_run= d= # show what would be done without doing it
	editor= e=  # editor to use for rebase
	message= m= # new commit message

	eval "$(ally)"

	[ $# -eq 1 ] || usage

	had_changes=0 # Initialize to 0
	had_staged=0  # Track staged changes

	commit=$1

	if [ "$dry_run" = 1 ]; then
		printf >&2 "Would rebase interactively to %s\n" "${commit}"
		return 0
	fi

	# Check if we're in a git repository
	if ! git rev-parse --git-dir >/dev/null 2>&1; then
		die "not a git repository"
	fi

	# Backup staged changes if present
	if ! git diff --cached --quiet; then
		staged_patch=$(mktemp)
		git diff --cached > "$staged_patch"
		git reset --quiet
		had_staged=1
	fi

	# Stash any changes if present
	if ! git diff-index --quiet HEAD --; then
		if ! git stash push -m "git-amend-old temporary stash"; then
			rm -f "$staged_patch"
			die "failed to stash changes"
		fi
		had_changes=1
	fi

	# Prepare rebase command with either commit hash or relative reference
	if ! [[ "$commit" =~ ^[0-9a-f]{4,}$ ]]; then
		target_commit="HEAD~${commit}"
	else
		target_commit="${commit}"
	fi

	# Resolve commit hash
	if ! target_commit_hash=$(git rev-parse "${target_commit}"); then
		[ "${had_changes}" = 1 ] && git stash pop
		[ "${had_staged}" = 1 ] && rm -f "$staged_patch"
		die "invalid commit: ${commit}"
	fi

	# Determine if target commit is the root commit
	root_commit_hash=$(git rev-list --max-parents=0 HEAD)

	if [ "${target_commit_hash}" = "${root_commit_hash}" ]; then
		rebase_args=(-i --root)
	else
		rebase_base="${target_commit_hash}^"
		rebase_args=(-i "${rebase_base}")
	fi

	# Create the rebase script
	rebase_script=$(mktemp)
	printf "edit %s\n" "${target_commit_hash}" > "$rebase_script"

	if ! EDITOR="cat" git -c sequence.editor="$(printf 'cat %q' "$rebase_script")" rebase "${rebase_args[@]}" </dev/tty; then
		[ "${had_changes}" = 1 ] && git stash pop
		[ "${had_staged}" = 1 ] && rm -f "$staged_patch"
		rm -f "$rebase_script"
		die "rebase failed"
	fi
	rm -f "$rebase_script"

	# Apply any previously staged changes
	if [ "${had_staged}" = 1 ]; then
		if ! git apply --cached "$staged_patch"; then
			rm -f "$staged_patch"
			die "failed to apply staged changes"
		fi
		rm -f "$staged_patch"
	fi

	# Amend the commit
	if [ -n "$message" ]; then
		git commit --amend -m "$message" || die "commit amend failed"
	else
		git commit --amend || die "commit amend failed"
	fi

	# Continue the rebase
	if ! git rebase --continue; then
		if [ -t 0 ]; then # If interactive shell
			printf >&2 "Please resolve conflicts and run 'git rebase --continue'\n"
			${SHELL:-/bin/bash}
			if ! git rebase --continue; then
				[ "${had_changes}" = 1 ] && git stash pop
				die "rebase continue failed"
			fi
		else
			[ "${had_changes}" = 1 ] && git stash pop
			die "rebase continue failed"
		fi
	fi

	# Restore stashed changes if any
	if [ "${had_changes}" = 1 ]; then
		if ! git stash pop; then
			die "failed to restore stashed changes"
		fi
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	git-amend-old "$@"
fi

# version: 0.1.3
