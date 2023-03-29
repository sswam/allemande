call plug#begin(has('nvim') ? stdpath('data') . '/plugged' : '~/.vim/plugged')
Plug 'djoshea/vim-autoread'
call plug#end()

set autoread

source ~/.local/share/nvim/plugged/vim-autoread/plugin/autoread.vim
execute WatchForChanges('*', {'autoread': 1})

function! BarbarellaFormat()
  set binary
  set noeol
  echo "Barbarella"
endfunction

augroup BarbarellaSettings
  autocmd!
  autocmd BufEnter *.bb call BarbarellaFormat()
augroup END
