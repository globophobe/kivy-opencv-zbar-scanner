import os

# b/c pyinstaller
try:
    os.environ["KIVY_WINDOW"] = "sdl2,pygame"
    os.environ["KIVY_IMAGE"] = "pil,sdl2"
    os.environ["KIVY_AUDIO"] = "pygame,sdl2"
except Exception:
    pass
else:
    from kivy.config import Config

    from simplecamera.app import SimpleCamera

    # Copied from tendo, b/c pbr build errors
    from simplecamera.lib import singleton

if __name__ == "__main__":
    Config.set("kivy", "desktop", 1)
    # Config.set("kivy", "window_icon", "assets/icon.ico")
    Config.set("kivy", "pause_on_minimize", 1)
    Config.set("kivy", "log_enable", 0)
    Config.set("input", "mouse", "mouse,disable_multitouch")
    Config.set("graphics", "maxfps", 30)
    Config.set("graphics", "borderless", 0)
    # Config.set("graphics", "fullscreen", "auto")
    Config.set("graphics", "fullscreen", 0)
    Config.set("graphics", "allow_screensaver", 0)
    Config.set("graphics", "window_state", "maximized")
    Config.write()
    try:
        lock = singleton.SingleInstance()
        app = SimpleCamera(
            https=False,
            settings={
                "domain": "localhost:8000",
                "token": "",
            },
        )
        app.run()
    except BaseException as e:
        is_system_exit = isinstance(e, SystemExit)
        is_singleton = isinstance(e, singleton.SingleInstanceException)
        if is_system_exit or is_singleton:
            pass
        else:
            raise e
