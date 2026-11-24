-- GPL-3.0-or-later. Set up Hyprnerd's desktop controller after the base rules.
local home = os.getenv("HOME") or ""
local config = os.getenv("XDG_CONFIG_HOME") or home .. "/.config"
local state = (os.getenv("XDG_STATE_HOME") or home .. "/.local/state") .. "/hyprnerd"
local runtime = (os.getenv("XDG_RUNTIME_DIR") or "/tmp") .. "/hyprnerd"
local ok, options = pcall(dofile, config .. "/hypr/UserConfigs/user_desktop.lua")
if not ok then options = { default_mode = "tiling" } end
local function quote(value) return "'" .. value:gsub("'", "'\\''") .. "'" end
local factory = dofile(config .. "/hypr/lua/hyprnerd_desktop.lua")
HYPRNERD_DESKTOP = factory(hl, {
  default_mode = options.default_mode,
  state_dir = state,
  runtime_dir = runtime,
  prepare = function() os.execute("mkdir -p -- " .. quote(state) .. " " .. quote(runtime)) end,
}):setup()
hl.config({ binds = { hide_special_on_workspace_change = true } })
