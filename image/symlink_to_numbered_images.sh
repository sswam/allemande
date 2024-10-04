ls *.png | perl -ne 'chomp; $a=$_; s/_\d+//; symlink $a, $_'
