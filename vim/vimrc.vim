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


fun! Comment(visual)
	" This comment function adds comments at the minimum indent level

	" Handle single line when no visual selection
	if a:visual
		let l:first_line = line("'<")
		let l:last_line = line("'>")
	else
		let l:first_line = line(".")
		let l:last_line = line(".")
	endif

	" Find minimum indent level in selection
	let l:min_indent = -1
	for l:lnum in range(l:first_line, l:last_line)
		let l:line = getline(l:lnum)
		let l:indent = len(matchstr(l:line, '^\s*'))
		if l:min_indent == -1 || (l:indent < l:min_indent && l:line !~ '^\s*$')
			let l:min_indent = l:indent
		endif
	endfor

	" If no non-empty lines found, default to 0
	if l:min_indent == -1
		let l:min_indent = 0
	endif

	" Create the indent pattern
	let l:indent_pattern = '^\s\{' . l:min_indent . '}'

	let l:range = l:first_line . ',' . l:last_line

	if &ft=='go' || &ft=='c' || &ft=='cpp' || &ft=='rust' || &ft=='java' || &ft=='javascript' ||
		\ &ft=='typescript' || &ft == 'css' || &ft == 'scss' || &ft == 'less' ||
		\ &ft == 'sass' || &ft == 'vue' || &ft == 'php' || &ft == 'svelte'
		exe l:range . 's,' . l:indent_pattern . ',\0// ,'
	elseif &ft=='vim'
		exe l:range . 's,' . l:indent_pattern . ',\0" ,'
	elseif &ft=='scheme' || &ft=='lisp'
		exe l:range . 's,' . l:indent_pattern . ',\0; ,'
	elseif &ft=='lua' || &ft=='sql'
		exe l:range . 's,' . l:indent_pattern . ',\0-- ,'
	else
		exe l:range . 's,' . l:indent_pattern . ',\0# ,'
	endif

	silent! exe l:range . 's,\s\+$,,' " remove trailing spaces
	noh
endfun

fun! Uncomment(visual)
	" Handle single line when no visual selection
	if a:visual
		let l:first_line = line("'<")
		let l:last_line = line("'>")
	else
		let l:first_line = line(".")
		let l:last_line = line(".")
	endif

	let l:range = l:first_line . ',' . l:last_line

	if &ft=='go' || &ft=='c' || &ft=='cpp' || &ft=='rust' || &ft=='java' || &ft=='javascript' ||
		\ &ft=='typescript' || &ft == 'css' || &ft == 'scss' || &ft == 'less' ||
		\ &ft == 'sass' || &ft == 'vue' || &ft == 'php' || &ft == 'svelte'
		silent! exe l:range . 's,^\(\s*\)// \?,\1,'
	elseif &ft=='vim'
		silent! exe l:range . 's,^\(\s*\)" \?,\1,'
	elseif &ft=='scheme' || &ft=='lisp'
		silent! exe l:range . 's,^\(\s*\); \?,\1,'
	elseif &ft=='lua' || &ft=='sql'
		silent! exe l:range . 's,^\(\s*\)-- \?,\1,'
	endif
	" always try to remove a # comment, because my scripts add them
	" to the wrong types of files pretty often
	silent! exe l:range . 's,^\(\s*\)# ,\1,'
	silent! exe l:range . 's,^\(\s*\)#$,\1,'
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

	nnoremap <F1> :<C-U>call Uncomment()<CR>
	nnoremap <F2> :<C-U>call Comment()<CR>
	vnoremap <F1> :<C-U>call Uncomment(1)<CR>gv
	vnoremap <F2> :<C-U>call Comment(1)<CR>gv

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
