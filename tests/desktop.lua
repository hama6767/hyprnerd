-- Pure integration model for the actual Lua desktop controller. No compositor needed.
local factory=dofile(arg[1])
local dir=arg[2]
local function fixture(label)
  local callbacks,workspaces,windows={}, {}, {}
  local a={name="DP-1",enabled=true,width=1920,height=1080,scale=1,x=0,y=0}
  local b={name="HDMI-A-1",enabled=true,width=2560,height=1440,scale=1.5,x=1920,y=0}
  local outputs={a,b};local active=a
  local function workspace(selector,mon)
    local name=tostring(selector):gsub("^name:","")
    local ws=workspaces[name]
    if not ws then ws={name=name,addressable_name=selector,special=false,monitor=mon};workspaces[name]=ws end
    return ws
  end
  a.active_workspace=workspace("1",a);b.active_workspace=workspace("2",b)
  local api={dsp={window={},cursor={}}}
  api.get_monitors=function() return outputs end
  api.get_active_monitor=function() return active end
  api.get_active_workspace=function() return active.active_workspace end
  api.get_cursor_pos=function() return {x=200,y=300} end
  api.get_workspaces=function() local t={};for _,ws in pairs(workspaces) do t[#t+1]=ws end;return t end
  api.get_windows=function() return windows end
  api.get_active_window=function() return windows[1] end
  local function dsp(kind) return function(args) return {kind=kind,args=args} end end
  api.dsp.focus=dsp('focus');api.dsp.cursor.move=dsp('cursor')
  for _,name in ipairs({'move','float','resize','tag'}) do api.dsp.window[name]=dsp(name) end
  api.dispatch=function(command)
    local v=command.args
    if command.kind=='focus' then
      if v.monitor then for _,mon in ipairs(outputs) do if mon.name==v.monitor then active=mon end end
      elseif v.workspace then
        active.active_workspace=workspace(v.workspace,active);active.active_workspace.monitor=active
        for _,fn in ipairs(callbacks['workspace.active'] or {}) do fn(active.active_workspace) end
      end
    elseif command.kind=='float' then v.window.floating=v.action=='on'
    elseif command.kind=='resize' then v.window.size={x=v.x,y=v.y}
    elseif command.kind=='move' then
      if v.workspace then v.window.workspace=workspace(v.workspace,active)
      else v.window.at={x=v.x,y=v.y} end
    elseif command.kind=='tag' then
      if v.tag:sub(1,1)=='+' then v.window.tags={v.tag:sub(2)} else v.window.tags={} end
    end
  end
  api.on=function(event,fn) callbacks[event]=callbacks[event] or {};table.insert(callbacks[event],fn);return {remove=function() for i=#callbacks[event],1,-1 do if callbacks[event][i]==fn then table.remove(callbacks[event],i) end end end} end
  api.timer=function(fn,opts) return {set_enabled=function() end} end
  local paths={state_dir=dir..'/'..label,runtime_dir=dir..'/'..label,default_mode='tiling'}
  os.execute('mkdir -p '..string.format('%q',paths.state_dir))
  local controller=factory(api,paths):setup()
  local function add(class,floating,ws,mon)
    local win={class=class,address='win-'..(#windows+1),mapped=true,floating=floating,workspace=workspace(ws,mon),monitor=mon,tags={},fullscreen=0}
    windows[#windows+1]=win;return win
  end
  return {api=api,d=controller,a=a,b=b,outputs=outputs,windows=windows,workspaces=workspaces,paths=paths,add=add,emit=function(event,win) for _,fn in ipairs(callbacks[event] or {}) do fn(win) end end}
end
local f=fixture('groups')
f.d.switch(3)
assert(f.a.active_workspace.name=='3' and f.b.active_workspace.name=='hyprnerd-3-HDMI-A-1')
assert(f.api.get_active_monitor()==f.a,'switching must preserve focused monitor')
f.d.step(1);assert(f.a.active_workspace.name=='4' and f.b.active_workspace.name=='hyprnerd-4-HDMI-A-1')
f.d.switch(42);assert(f.d.current()==42,'workspace count must not be limited to ten')
f.d.new_workspace();assert(f.d.current()==5,'new must choose the first unused positive workspace')
-- Native workspace activation (e.g. a dock click) also synchronizes the other output.
f.api.dispatch(f.api.dsp.focus({workspace='7'}));assert(f.b.active_workspace.name=='hyprnerd-7-HDMI-A-1')
local w=f.add('kitty',false,'hyprnerd-7-HDMI-A-1',f.b)
f.d.move(8,false);assert(w.workspace.name=='hyprnerd-8-HDMI-A-1');assert(f.d.current()==7)
f.d.move(8,true);assert(f.d.current()==8 and f.a.active_workspace.name=='8')
-- Unplugging the secondary monitor preserves access to its windows.
table.remove(f.outputs,2);f.d.refresh();assert(w.workspace.name=='8','orphaned windows must migrate to the surviving group')
table.insert(f.outputs,f.b);f.d.refresh();assert(f.b.active_workspace.name=='hyprnerd-8-HDMI-A-1')
-- Adding a third monitor is discovered dynamically.
local c={name='DP-3',enabled=true,width=1920,height=1080,scale=1,x=4480,y=0};table.insert(f.outputs,c)
f.d.switch(9);assert(c.active_workspace.name=='hyprnerd-9-DP-3')
assert(f.d.group_number({name='special:scratchpad',special=true})==nil)
f.d.switch(-3);assert(f.d.current()==9)
local g=fixture('modes')
local tiled=g.add('kitty',false,'1',g.a)
local dialog=g.add('pavucontrol',true,'1',g.a)
local drop=g.add('kitty-dropterm',true,'special:scratchpad',g.a);drop.workspace.special=true
assert(g.d.mode()=='tiling')
g.d.toggle_mode();assert(tiled.floating and tiled.size.x<1920);assert(dialog.floating and dialog.size==nil)
-- Tag ownership survives config reloads; switching back restores only managed windows.
g.emit('config.unload');g.d=factory(g.api,g.paths);assert(g.d.mode()=='floating');g.d.set_mode('tiling')
assert(not tiled.floating and dialog.floating and drop.floating)
g.d.set_mode('floating');g.d.setup()
local new=g.add('firefox',false,'1',g.a);g.emit('window.open',new);assert(new.floating)
g.d.set_mode('tiling');local later=g.add('editor',false,'1',g.a);g.emit('window.open',later);assert(not later.floating)
print('PASS: synchronized desktops, native activation, >10 workspaces, add/move, hotplug, floating ownership and persisted mode')
