" For the Allemande chat and story system, which uses the .bb extension
" we don't always want the file to end with a newline.
" This enables the AI to continue a line rather than starting a new one.


" Do indentation properly!

fun! Indent()
	let indent = &expandtab ? repeat(' ', &shiftwidth) : '\t'
	execute 'silent! s/^..*/' . indent . '&/'
endfun

fun! Dedent() range
	let indent = &expandtab ? repeat(' ', &shiftwidth) : '\t'
	let lines = getline(a:firstline, a:lastline)
	let can_dedent = match(lines, '^' . indent) >= 0
	execute 'silent! ' . a:firstline . ',' . a:lastline . (can_dedent ? 's/^' . indent . '//' : 's/^\s*//')
	noh
endfun


" Comment and Uncomment
fun! Comment()
	if &ft=='go' || &ft=='c' || &ft=='cpp' || &ft=='rust' || &ft=='java' || &ft=='javascript' ||
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
	silent! s,  *$,, " remove trailing spaces
	noh
endfun

fun! Uncomment()
	if &ft=='go' || &ft=='c' || &ft=='cpp' || &ft=='rust' || &ft=='java' || &ft=='javascript' ||
		\ &ft=='typescript' || &ft == 'css' || &ft == 'scss' || &ft == 'less' ||
		\ &ft == 'sass' || &ft == 'vue' || &ft == 'php' || &ft == 'svelte'
		silent! s,^\(\s*\)// \?,\1,
	elseif &ft=='vim'
		silent! s,^\(\s*\)" \?,\1,
	elseif &ft=='scheme' || &ft=='lisp'
		silent! s,^\(\s*\); \?,\1,
	elseif &ft=='lua' || &ft=='sql'
		silent! s,^\(\s*\)-- \?,\1,
	endif
	" always try to remove a # comment, because my scripts add them
	" to the wrong types of files pretty often
	silent! s,^\(\s*\)# ,\1,
	silent! s,^\(\s*\)#$,\1,
	noh
endfun

fun! AllemandeRaw()
	set binary
	set noeol
	echo "Allemande raw"
endfun


fun! AllemandeChat()
	set nobinary
	set eol
	echo "Allemande chat"
endfun


fun! Allemande(format)
	if a:format == "raw"
		call AllemandeRaw()
	else
		call AllemandeChat()
	endif

	nnoremap <silent> > :call Indent()<CR>
	nnoremap <silent> < :call Dedent()<CR>
	vnoremap <silent> > :call Indent()<CR>gv
	vnoremap <silent> < :call Dedent()<CR>gv

	nnoremap <F1> :call Uncomment()<CR>
	nnoremap <F2> :call Comment()<CR>
	vnoremap <F1> :call Uncomment()<CR>gv
	vnoremap <F2> :call Comment()<CR>gv

	" Set up the tabbing
	set tabstop=8
	set softtabstop=8
	set shiftwidth=0
	set noexpandtab
	let &showbreak='                '
	set syntax=markdown
endfun


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

fun! AllemandeAutoread()
	call plug#begin(has('nvim') ? stdpath('data') . '/plugged' : '~/.vim/plugged')
	Plug 'djoshea/vim-autoread'
	call plug#end()

	set autoread

	source ~/.local/share/nvim/plugged/vim-autoread/plugin/autoread.vim
	execute WatchForChanges('*', {'autoread': 1})
endfun

command! -nargs=0 AllemandeAutoread call AllemandeAutoread()


" Set FILETYPE env-var for tools to know what language we are working on

augroup SetCodeLang
	autocmd!
	autocmd FileType * let $FILETYPE = expand('<amatch>')
augroup END


" Detect and set indentation settings using aligno

function! DetectAndSetIndent()
	" Save current cursor position
	let l:save_cursor = getpos(".")

	" Get entire buffer content
	let l:content = join(getline(1, '$'), "\n")

	" Run aligno with buffer content as stdin
	let l:result = system('aligno', l:content)

	" Check first two characters of output
	let l:indent_type = l:result[0:1]

	" Echo the setting
	" echo "Detected indent type: " . l:indent_type

	if l:indent_type == '2s'
		" 2 space indentation
		setlocal tabstop=2
		setlocal softtabstop=2
		setlocal shiftwidth=2
		setlocal expandtab
		let &showbreak='    '
	elseif l:indent_type == '4s'
		" 4 space indentation
		setlocal tabstop=4
		setlocal softtabstop=4
		setlocal shiftwidth=4
		setlocal expandtab
		let &showbreak='        '
	else
		" Tab indentation
		setlocal tabstop=8
		setlocal softtabstop=8
		setlocal shiftwidth=0
		setlocal noexpandtab
		let &showbreak='                '
	endif

	" Restore cursor position
	call setpos('.', l:save_cursor)
endfunction

" Run on file load after everything else
autocmd BufReadPost * call timer_start(0, {-> DetectAndSetIndent()})
