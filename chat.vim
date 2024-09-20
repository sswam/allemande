" For the Allemande chat and story system, which uses the .bb extension
" we don't always want the file to end with a newline.
" This enables the AI to continue a line rather than starting a new one.

" Do indentation properly!

function! Indent()
	let indent = &expandtab ? repeat(' ', &shiftwidth) : '\t'
	execute 'silent! s/^..*/' . indent . '&/'
endfun

function! Dedent()
	let indent = &expandtab ? repeat(' ', &shiftwidth) : '\t'
	let lines = visualmode() !=# '' ? [getline('.')] : getline("'<", "'>")
	let can_dedent = match(lines, '^' . indent) >= 0
	execute 'silent! ' . (can_dedent ? 's/^' . indent . '//' : 's/^\s*//')
	noh
endfun

" Comment and Uncomment
function! Comment()
	if &ft=='go' || &ft=='c' || &ft=='cpp' || &ft=='java' || &ft=='javascript' ||
		\ &ft=='typescript' || &ft == 'css' || &ft == 'scss' || &ft == 'less' ||
		\ &ft == 'sass' || &ft == 'vue' || &ft == 'php' || &ft == 'svelte'
		s,^,// ,
	elseif &ft=='vim'
		s,^," ,
	elseif &ft=='scheme' || &ft=='lisp'
		s,^,; ,
	elseif &ft=='lua' || &ft=='sql'
		s,^,-- ,
	else
		s,^,# ,
	endif
	noh
endfun

function! Uncomment()
	if &ft=='go' || &ft=='c' || &ft=='cpp' || &ft=='java' || &ft=='javascript' ||
		\ &ft=='typescript' || &ft == 'css' || &ft == 'scss' || &ft == 'less' ||
		\ &ft == 'sass' || &ft == 'vue' || &ft == 'php' || &ft == 'svelte'
		silent! s,^// \?,,
	elseif &ft=='vim'
		silent! s,^" \?,,
	elseif &ft=='scheme' || &ft=='lisp'
		silent! s,^; \?,,
	elseif &ft=='lua' || &ft=='sql'
		silent! s,^-- \?,,
	else
		silent! s,^# \?,,
	endif
	noh
endfun

function! AllemandeRaw()
	set binary
	set noeol
	echo "Allemande raw"
endfunction


function! AllemandeChat()
	set nobinary
	set eol
	echo "Allemande chat"
endfunction


function! Allemande(format)
	if a:format == "raw"
		call AllemandeRaw()
	else
		call AllemandeChat()
	endif

	nnoremap <silent> > :call Indent()<CR>
	nnoremap <silent> < :call Dedent()<CR>
	vnoremap <silent> > :call Indent()<CR>gv
	vnoremap <silent> < :call Dedent()<CR>gv

	nnoremap <F2> :call Uncomment()<CR>
	nnoremap <F3> :call Comment()<CR>
	vnoremap <F2> :call Uncomment()<CR>gv
	vnoremap <F3> :call Comment()<CR>gv

	" Set up the tabbing
	set tabstop=8
	set softtabstop=8
	set shiftwidth=0
	set noexpandtab
	let &showbreak='                '
	set syntax=markdown
endfunction


" a command Allemande to call Allemande
" usage:
" allemande raw
" allemande chat
command! -nargs=1 Allemande call Allemande(<f-args>)


augroup AllemandeSettings
	autocmd!
	autocmd BufEnter *.bb call Allemande("chat")
augroup END


" Enable autoread for all files

function! AllemandeAutoread()
	call plug#begin(has('nvim') ? stdpath('data') . '/plugged' : '~/.vim/plugged')
	Plug 'djoshea/vim-autoread'
	call plug#end()

	set autoread

	source ~/.local/share/nvim/plugged/vim-autoread/plugin/autoread.vim
	execute WatchForChanges('*', {'autoread': 1})
endfunction

command! -nargs=0 AllemandeAutoread call AllemandeAutoread()
