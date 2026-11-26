local active,closed,notice,timers,events=nil,{},nil,{},{}
local api={dsp={window={close=function(x)return x end}}}
function api.get_active_window()return active end
function api.dispatch(x)table.insert(closed,x.window.address)end
function api.timer(fn,opts)
  assert(opts.timeout==4000);local t={fn=fn,enabled=true}
  function t:set_enabled(value)self.enabled=value end
  table.insert(timers,t);return t
end
api.notification={create=function(opts)
  notice={text=opts.text,dismissed=false}
  function notice:dismiss()self.dismissed=true end
  return notice
end}
function api.on(name,fn)events[name]=fn end
local guard=dofile(arg[1])(api)
active={address='1',class='firefox_firefox'};guard.press();assert(#closed==0 and notice.text:find('Windows%+Q'))
guard.press();assert(#closed==1 and closed[1]=='1' and notice.dismissed)
active={address='2',class='Vivaldi-stable'};guard.press();timers[#timers].fn();guard.press();assert(#closed==1)
active={address='3',class='Google-chrome'};events['window.active'](active);guard.press();assert(#closed==1)
guard.press();assert(#closed==2 and closed[2]=='3')
active={address='4',class='kitty'};guard.press();assert(#closed==3 and closed[3]=='4')
active={address='5',class='org.mozilla.firefox'};guard.press();events['window.active'](nil);guard.press();assert(#closed==3)
events['config.unload']();guard.press();assert(#closed==3)
assert(guard.protected({class='chromium'}) and not guard.protected({class='org.example.Editor'}))
print('PASS: browser close confirmation, timeout, focus cancellation, ordinary close and reload')
