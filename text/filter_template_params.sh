# perl -pe 'sub f { $_=$_[0]; s/-/_/g; uc; "{$_}"; } s/{([\w-]+)}/f($1)/eg;'
grep -o '{[^}]*}' template/tourism.txt | uniqo
# grep -o '\(id\|class\)="[^"]*"' template/tourism.txt | uniqo | less
