#!/usr/bin/env python3

"""Legacy lua-vim emulation."""
import logging
import os
import sys
from collections import defaultdict

import neovim
import lupa

__all__ = ('ScriptHost',)


logger = logging.getLogger(__name__)
debug, info, warn = (logger.debug, logger.info, logger.warn,)

IS_PYTHON3 = sys.version_info >= (3, 0)

@neovim.plugin
class ScriptHost(object):

    """Provides an environment for running python plugins created for Vim."""

    def __init__(self, nvim):
        """Initialize lua environment."""
        self.setup(nvim)

    def setup(self, nvim):
        """Setup import hooks and global streams."""
        self.nvim = nvim
        self.lua = lupa.LuaRuntime()
        _G = self.lua.globals()
        _G.vim = LuaVim(nvim, self.lua)
        stdout = RedirectStream(lambda data: nvim.out_write(data))
        _G.io.stdout = stdout
        _G.io.stderr = RedirectStream(lambda data: nvim.err_write(data))
        _G.print = stdout.write

    def teardown(self):
        """Restore state modified from the `setup` call."""
        for plugin in self.installed_plugins:
            if hasattr(plugin, 'on_teardown'):
                plugin.teardown()

    @neovim.rpc_export('lua_execute', sync=True)
    def lua_execute(self, script, range_start, range_stop):
        """Handle the `lua` ex command."""
        self.lua.execute(script)

class RedirectStream(object):
    def __init__(self, redirect_handler):
        self.redirect_handler = redirect_handler

    def write(self, data):
        self.redirect_handler(data)

    def flush(self):
        pass

class LuaVim(object):
    def __init__(self, nvim, lua):
        self.nvim = nvim
        self.lua = lua
        methods = defaultdict(lambda: None, {
            'add': lua.globals().table.insert,
        })
        self._vim_dict_metatable = lua.table(
            __len = len,
            __index = methods,
        )

    def eval(self, expr):
        ret = orig = self.nvim.eval(expr)
        if isinstance(ret, (dict, list)):
            lua = self.lua
            if isinstance(ret, dict):
                ret = lua.table(**ret)
            else:
                ret = lua.table(*ret)
            lua.globals().setmetatable(
                ret, self._vim_dict_metatable)
        warn('%r -> %r -> %r', expr, orig, ret)
        return ret

    def buffer(self):
        return self.nvim.current.buffer

    def list(self):
        lua = self.lua
        t = lua.table()
        lua.globals().setmetatable(
            t, self._vim_dict_metatable)
        return t
