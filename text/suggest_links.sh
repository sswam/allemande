#!/bin/bash -eu
# suggest-links: suggest links by looking for capitalized phrases
giles_alfred_dir=$1

cat "$giles_alfred_dir"/output.*.md | grep -v '^#' |

perl -ne "$(cat <<'EOF'
	chomp;
	if (m{
	(
		(\b[A-Z][A-Za-z]+\b\s*)
		(
			(\b[A-Za-z][A-Za-z]+\b\s*)
			(\b[A-Z][A-Za-z]+\b\s*)+
		)+
	)
	}x) {
		$_ = $1;
		s/\s+$//;
		print "$_\n";
	}
EOF
)" | grep -v '^While ' |
uniqoc | sort -rn


# TODO i18n / l10n
# (
# (
# 	(\b[:upper:][:alpha:]*\b\s*)
# 	(
# 		(\b[:alpha:]+\b\s*)
# 		(\b[:upper:][:alpha:]*\b\s*)*
# 	)+
# )+
# )
