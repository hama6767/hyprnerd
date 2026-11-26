-- GPL-3.0-or-later. Confirm browser closes without putting a process on the key path.
return function(api)
  local M = {}
  local pending, timer, notification
  local function protected(win)
    local class = ((win and win.class) or ""):lower()
    for _, name in ipairs({"firefox", "chrome", "chromium", "vivaldi", "brave", "librewolf", "waterfox", "floorp", "microsoft-edge"}) do
      if class:find(name, 1, true) then return true end
    end
    return false
  end
  function M.cancel()
    pending = nil
    if timer then timer:set_enabled(false); timer = nil end
    -- Notification handles can expire; clearing must never block a key action.
    if notification then pcall(function() notification:dismiss() end); notification = nil end
  end
  function M.press()
    local win = api.get_active_window()
    if not win then M.cancel(); return end
    if not protected(win) or pending == win.address then
      M.cancel()
      api.dispatch(api.dsp.window.close({ window = win }))
      return
    end
    M.cancel()
    pending = win.address
    timer = api.timer(M.cancel, { timeout = 4000, type = "oneshot" })
    notification = api.notification.create({
      text = "ブラウザーを閉じますか？ 4秒以内にもう一度 Windows+Q（別のウィンドウを選ぶと取消）",
      timeout = 4000, icon = "info", color = "rgb(72c8c8)",
    })
  end
  api.on("window.active", function(win)
    if pending and (not win or win.address ~= pending) then M.cancel() end
  end)
  api.on("window.close", function(win)
    if win and win.address == pending then M.cancel() end
  end)
  api.on("config.unload", M.cancel)
  M.protected = protected
  return M
end
