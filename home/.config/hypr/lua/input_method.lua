-- Native Wayland text-input for Kitty/GTK; modules for legacy X11 and Qt5.
hl.env("XMODIFIERS", "@im=fcitx")
hl.env("QT_IM_MODULE", "fcitx")
hl.env("QT_IM_MODULES", "wayland;fcitx;ibus")
hl.env("SDL_IM_MODULE", "fcitx")
-- GTK_IM_MODULE stays unset so native GTK uses Wayland text-input-v3.
