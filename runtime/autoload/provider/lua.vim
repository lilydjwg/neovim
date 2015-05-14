" The Lua provider uses a Lua host to emulate an environment for running
" lua-vim plugins. See ":help nvim-provider" for more information.
"
" Associating the plugin with the Lua host is the first step because plugins
" will be passed as command-line arguments

if exists('g:loaded_lua_provider')
  finish
endif
let g:loaded_lua_provider = 1

let [s:prog, s:err] = provider#pythonx#Detect(2)
if s:prog == ''
  " Detection failed
  finish
endif

function! provider#lua#Prog()
  return s:prog
endfunction

function! provider#lua#Error()
  return s:err
endfunction

let s:plugin_path = expand('<sfile>:p:h').'/script_host_lua.py'

" The Lua provider plugin will run in a separate instance of the Lua
" host.
call remote#host#RegisterClone('legacy-lua-provider', 'python')
call remote#host#RegisterPlugin('legacy-lua-provider', s:plugin_path, [])

function! provider#lua#Call(method, args)
  if !exists('s:host')
    let s:rpcrequest = function('rpcrequest')

    " Ensure that we can load the Lua host before bootstrapping
    try
      let s:host = remote#host#Require('legacy-lua-provider')
    catch
      echomsg v:exception
      finish
    endtry
  endif
  return call(s:rpcrequest, insert(insert(a:args, 'lua_'.a:method), s:host))
endfunction
