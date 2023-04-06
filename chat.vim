" For the Barbarella chat and story system, which uses the .bb extension
" we don't always want the file to end with a newline.
" This enables the AI to continue a line rather than starting a new one.

function! BarbarellaFormat()
	set binary
	set noeol
	echo "Barbarella"
endfunction

augroup BarbarellaSettings
	autocmd!
	autocmd BufEnter *.bb call BarbarellaFormat()
augroup END



" Enable autoread for all files

call plug#begin(has('nvim') ? stdpath('data') . '/plugged' : '~/.vim/plugged')
Plug 'djoshea/vim-autoread'
call plug#end()

set autoread

source ~/.local/share/nvim/plugged/vim-autoread/plugin/autoread.vim
execute WatchForChanges('*', {'autoread': 1})



" Do indentation properly!

function! Indent()
	if &expandtab
		let spaces = repeat(' ', &shiftwidth)
		s/^/\=spaces/
	else
		s/^/\t/
	endif
	noh
endfun

function! Dedent()
	if &expandtab
		let spaces = repeat(' ', &shiftwidth)
		execute 's/^\(' . spaces . '\)\?//'
		noh
	else
		s/^\t\?//
	endif
	noh
endfun

nnoremap <silent> > :call Indent()<CR>
nnoremap <silent> < :call Dedent()<CR>
vnoremap <silent> > :call Indent()<CR>gv
vnoremap <silent> < :call Dedent()<CR>gv



" Set up the tabbing

set tabstop=8
set softtabstop=8
set shiftwidth=0
set noexpandtab
let &showbreak='                '
