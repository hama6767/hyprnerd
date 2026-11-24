-- GPL-3.0-or-later. Hyprland 0.57 desktop-wide workspace groups and window mode.
-- Each group owns one workspace per connected output; no fixed monitor/workspace count.
return function(api, paths)
  local M = { busy = false, managed = {}, subscriptions = {}, timers = {} }
  local primary, current, mode = nil, 1, paths.default_mode or "tiling"
  local function read(path)
    local f = io.open(path, "r"); if not f then return nil end
    local value = f:read("*l"); f:close(); return value
  end
  local function write(path, value)
    local f = io.open(path .. ".tmp", "w")
    if not f and paths.prepare then paths.prepare(); f = io.open(path .. ".tmp", "w") end
    if f then f:write(value); f:close(); os.rename(path .. ".tmp", path) end
  end
  local saved = read(paths.state_dir .. "/window-mode")
  if saved == "floating" or saved == "tiling" then mode = saved end
  primary = read(paths.state_dir .. "/primary-output")
  local function number(ws)
    if not ws or ws.special then return nil end
    local name = ws.name or ""
    return tonumber(name:match("^hyprnerd%-(%d+)%-")) or (tonumber(name) and tonumber(name) > 0 and tonumber(name))
  end
  local function monitors()
    local result = {}
    for _, mon in ipairs(api.get_monitors()) do
      if mon.enabled ~= false and not mon.is_mirror then table.insert(result, mon) end
    end
    table.sort(result, function(a,b) return a.name < b.name end)
    return result
  end
  local function choose_primary(list)
    for _, mon in ipairs(list) do if mon.name == primary then return end end
    local active = api.get_active_monitor()
    primary = active and active.name or (list[1] and list[1].name)
    if primary then write(paths.state_dir .. "/primary-output", primary) end
  end
  local function selector(id, mon)
    if mon.name == primary then return tostring(id) end
    return "name:hyprnerd-" .. id .. "-" .. mon.name
  end
  local function dispatch(dsp) api.dispatch(dsp) end
  function M.groups()
    local seen, result = { [current] = true }, {}
    for _, ws in ipairs(api.get_workspaces()) do local id=number(ws); if id then seen[id]=true end end
    for id in pairs(seen) do table.insert(result,id) end
    table.sort(result); return result
  end
  function M.publish()
    local list=monitors(); if #list == 0 then return end
    local ids=M.groups()
    write(paths.runtime_dir .. "/desktop.json", string.format(
      '{"mode":%q,"current":%d,"groups":[%s],"monitors":%d}\n', mode,current,table.concat(ids,","),#list))
  end
  function M.switch(id)
    id=tonumber(id)
    if not id or id < 1 or id % 1 ~= 0 or id > 2147483647 or M.busy then return end
    local list=monitors(); if #list == 0 then return end
    choose_primary(list)
    M.busy=true; current=id
    local focused=api.get_active_monitor()
    local cursor=api.get_cursor_pos and api.get_cursor_pos()
    local ok,err=pcall(function()
      for _, mon in ipairs(list) do
        local target=selector(id,mon)
        local ws=mon.active_workspace
        local actual=ws and (ws.addressable_name or ws.name)
        if actual ~= target and actual ~= target:gsub("^name:","") then
          dispatch(api.dsp.focus({monitor=mon.name}))
          dispatch(api.dsp.focus({workspace=target,on_current_monitor=true}))
        end
      end
      if focused then dispatch(api.dsp.focus({monitor=focused.name})) end
      if cursor and api.dsp.cursor then dispatch(api.dsp.cursor.move({x=cursor.x,y=cursor.y})) end
    end)
    M.busy=false; M.publish()
    if not ok then error(err) end
  end
  function M.step(delta) M.switch(math.max(1,current+delta)) end
  function M.new_workspace()
    local used={};for _,id in ipairs(M.groups()) do used[id]=true end
    local id=1;while used[id] do id=id+1 end;M.switch(id)
  end
  function M.move(id,follow)
    local win=api.get_active_window(); if not win or not win.monitor then return end
    id=tonumber(id);if not id or id<1 or id%1~=0 then return end
    choose_primary(monitors())
    dispatch(api.dsp.window.move({window=win,workspace=selector(id,win.monitor),follow=false}))
    if follow then M.switch(id) end
    M.publish()
  end
  function M.move_step(delta,follow) M.move(math.max(1,current+delta),follow) end
  local function normal(win)
    return win and win.mapped ~= false and win.workspace and not win.workspace.special
      and not win.pinned and (win.fullscreen or 0)==0 and win.class ~= "kitty-dropterm"
  end
  local function managed(win)
    if M.managed[win.address] then return true end
    if type(win.tags)=="table" then for _,tag in ipairs(win.tags) do if tag=="hyprnerd-floating" then return true end end
    elseif type(win.tags)=="string" then return win.tags:find("hyprnerd-floating",1,true)~=nil end
    return false
  end
  local function float_window(win)
    if not normal(win) or win.floating then return end
    M.managed[win.address]=true
    dispatch(api.dsp.window.tag({window=win,tag="+hyprnerd-floating"}))
    dispatch(api.dsp.window.float({window=win,action="on"}))
    local mon=win.monitor
    if not mon then return end
    local scale=mon.scale or 1
    local width=math.floor((mon.width or 1920)/scale)
    local height=math.floor((mon.height or 1080)/scale)
    local w=math.min(width-48,math.max(640,math.floor(width*.72)))
    local h=math.min(height-80,math.max(420,math.floor(height*.76)))
    local offset=0;for _ in pairs(M.managed) do offset=offset+1 end;offset=((offset-1)%5)*22
    local x=(mon.x or 0)+math.max(24,math.min(width-w-24,math.floor((width-w)/2)+offset))
    local y=(mon.y or 0)+math.max(45,math.min(height-h-24,math.floor((height-h)/2)+offset))
    dispatch(api.dsp.window.resize({window=win,x=w,y=h}))
    dispatch(api.dsp.window.move({window=win,x=x,y=y}))
  end
  function M.set_mode(value)
    if value ~= "floating" and value ~= "tiling" then return end
    mode=value;write(paths.state_dir.."/window-mode",mode)
    for _,win in ipairs(api.get_windows()) do
      if mode=="floating" then float_window(win)
      elseif normal(win) and managed(win) then
        dispatch(api.dsp.window.float({window=win,action="off"}));M.managed[win.address]=nil
        dispatch(api.dsp.window.tag({window=win,tag="-hyprnerd-floating"}))
      end
    end
    M.publish()
  end
  function M.toggle_mode() M.set_mode(mode=="floating" and "tiling" or "floating") end
  function M.refresh()
    local ws=api.get_active_workspace()
    current=number(ws) or current
    local list=monitors()
    if #list>0 then
      choose_primary(list)
      local connected={};for _,mon in ipairs(list) do connected[mon.name]=true end
      -- A removed output must not strand its windows on a hidden companion workspace.
      M.busy=true
      for _,win in ipairs(api.get_windows()) do
        local name=win.workspace and win.workspace.name or ""
        local id,output=name:match("^hyprnerd%-(%d+)%-(.+)$")
        if id and (not connected[output] or output==primary) then
          dispatch(api.dsp.window.move({window=win,workspace=id,follow=false}))
        end
      end
      M.busy=false
      M.switch(current)
    end
    M.publish()
  end
  function M.setup()
    local function on(event,fn) table.insert(M.subscriptions,api.on(event,fn)) end
    local function later(fn,timeout)
      local timer=api.timer(fn,{timeout=timeout or 80,type="oneshot"});table.insert(M.timers,timer)
    end
    on("window.open",function(win) if mode=="floating" then float_window(win) end;M.publish() end)
    on("window.fullscreen",function(win) if mode=="tiling" and normal(win) and managed(win) then M.set_mode(mode) end end)
    on("window.close",function(win) if win then M.managed[win.address]=nil end;M.publish() end)
    on("workspace.active",function(ws)
      local id=number(ws)
      if not M.busy and id then M.switch(id) end
    end)
    for _,event in ipairs({"workspace.created","workspace.removed","window.move_to_workspace"}) do
      on(event,function() M.publish() end)
    end
    for _,event in ipairs({"monitor.added","monitor.removed","monitor.layout_changed"}) do
      on(event,function() later(M.refresh,350) end)
    end
    on("config.unload",function()
      for _,t in ipairs(M.timers) do t:set_enabled(false) end
      for _,subscription in ipairs(M.subscriptions) do if subscription.remove then subscription:remove() end end
    end)
    -- Defer until the runtime has monitors, including on an ordinary config reload.
    local function initialize()
      if #monitors()==0 then return end
      M.refresh(); M.set_mode(mode)
    end
    on("hyprland.start",function() later(initialize,250) end)
    -- verify-config has no event loop; creating a timer there crashes Hyprland 0.57.
    if #monitors()>0 then later(initialize,250) end
    return M
  end
  M.group_number=number
  M.mode=function() return mode end
  M.current=function() return current end
  return M
end
