" Open task files in a 3x2 grid layout in Vim

split
vsplit
vsplit
wincmd j
vsplit
vsplit
wincmd k

e 1-crisis.md
" go to top of file
normal gg
wincmd w

e 2-plan.md
normal gg
wincmd w

e mission.m
normal gg
wincmd w

e 3-interrupt.md
normal gg
wincmd w

e 4-distract.md
normal gg
wincmd w

e comments.md
normal gg
wincmd w
