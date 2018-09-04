_APP_TITLE = "TiLD-rc"
_APP_AUTHOR = "grufwub"
_APP_LIB_AUTHOR = "jaraco"

___name___         = _APP_TITLE
___license___      = "MIT"
___dependencies___ = ["wifi", "http", "ugfx_helper", "sleep", "app"] # TODO: add py irc dependency, figure out how this works with micro pip?
___categories___   = ["EMF"]
___bootstrapped___ = False

import ugfx_helper, wifi, ugfx, app, dialog, buttons, collections, time
import tildrc_client as tirc
from buttons import Buttons

# User-entered variables
_SERVER = ""
_PORT = -1
_SSL = False
_NICK = ""
_USER = ""
_REALNAME = ""
_PASSWORD = ""
_CHANNEL = ""

# Required app variables / strings
_CLIENT = None
_CONSOLE_BUF = None
_MAX_BUF = 50
_CONSOLE_REFRESH = 0.1
_UITEXT_MAIN = "Options:"
_UITEXT_CHANNELS = "Channels:"
_UITEXT_NONE = "Exit"
_UITEXT_INPUT_SERVER = "Enter server address:"
_UITEXT_INPUT_PORT = "Enter server port:"
_UITEXT_INPUT_SSL = "Does server use SSL?"
_UITEXT_INPUT_NICK = "Enter preferred nickname:"
_UITEXT_INPUT_USER = "Enter username:"
_UITEXT_INPUT_REAL = "Enter realname:"
_UITEXT_INPUT_PASSWORD = "Enter password:"
_UITEXT_INPUT_CHANNEL = "Enter server channel:"
_UITEXT_INPUT_CONSOLE = "Enter message:"
_ERRMSG_TITLE = "[!!] Error"
_ERRMSG_SERVER = "Please supply an IRC server address!"
_ERRMSG_PORT = "Please supply a port for the IRC server!"
_ERRMSG_CONNECT_FAIL = "Failed to connect to server!"

# App started! Time to initialize
ugfx_helper.init()

### START: abstract internal functions
def user_text_input(msg):
    ugfx.clear()
    return dialog.prompt_text(text = msg, title = _APP_TITLE)

def user_num_input(msg):
    ugfx.clear()
    return dialog.prompt_text(text = msg, title = _APP_TITLE, numeric = True)

def user_bool_input(msg):
    ugfx.clear()
    return dialog.prompt_boolean(text = msg, title = _APP_TITLE)
### END: abstract internal functions

### START: 'set' functions
def set_server():
    _SERVER = user_text_input(_UITEXT_INPUT_SERVER)
    main()

def set_port():
    in_ = user_text_input(_UITEXT_INPUT_PORT)
    # Is the following needed?
    if not str.isdigit(in_):
        display_error(_ERRMSG_PORT)
        set_port()
    else:
        _PORT = in_
        main()

def set_channel():
    _CHANNEL = user_text_input(_UITEXT_INPUT_CHANNEL)
    main()

def set_ssl():
    _SSL = user_bool_input(_UITEXT_INPUT_SSL)
    main()

def set_nick():
    _NICK = user_text_input(_UITEXT_INPUT_NICK)
    main()

def set_user():
    _USER = user_text_input(_UITEXT_INPUT_USER)
    main()

def set_realname():
    _REALNAME = user_text_input(_UITEXT_INPUT_REAL)
    main()

def set_password():
    _PASSWORD = user_text_input(_UITEXT_INPUT_PASSWORD)
    main()
### END: 'set' functions

### START: UI / app functions
def main():
    # Clear on each call as we'll be changing screens a lot...
    ugfx.clear()

    menu_items = [
        {"title": "Connect...", "function": connect},
        {"title": "Set server", "function": set_server},
        {"title": "Set port", "function": set_port},
        {"title": "Set channel", "function": set_channel},
        {"title": "Set SSL enabled", "function": set_ssl},
        {"title": "Set nickname", "function": set_nick},
        {"title": "Set username", "function": set_user},
        {"title": "Set realname", "function": set_realname},
        {"title": "Set password", "function": set_password},
    ]
    
    selection = dialog.prompt_option(menu_items, none_text = _UITEXT_NONE, text = _UITEXT_MAIN, title = _APP_TITLE)
    if selection:
        func = selection["function"]
        func()

def display_error(msg):
    dialog.notice(text = msg, title = _ERRMSG_TITLE)

def connect():
    if not _SERVER:
        display_error(_ERRMSG_SERVER)
    if _PORT == -1:
        display_error(_ERRMSG_PORT)

    try:
        if not _CHANNEL: show_channels()
        _CLIENT = tirc.Client()
        _CLIENT.connect(
            _SERVER,
            _PORT,
            _SSL,
            _NICK,
            _USER,
            _REALNAME,
            _PASSWORD,
            _CHANNEL
        )

        _CONSOLE_BUF = collections.deque(maxlen = _MAX_BUF)

        show_channel_console()
        # add UI handlers
        _CLIENT.on_pubmsg(on_pubmsg)
        _CLIENT.on_privmsg(on_privmsg)
        _CLIENT.on_join(on_join)
        _CLIENT.on_kick(on_kick)
        _CLIENT.on_nick(on_nick)
        _CLIENT.on_quit(on_quit)

        _CLIENT.process_forever()
    
    except RuntimeError:
        display_error(_ERRMSG_CONNECT_FAIL)

    finally:
        _CLIENT.disconnect()
        del _CLIENT
        del _CONSOLE_BUF
        main()

def show_channels():
    chan_list = _CLIENT.channel_list()
    menu_items = list()
    for chan in chan_list:
        item_dict = {
            "title": chan
            "function": _CLIENT.set_channel(chan)
        }
        menu_items.append(item_dict)
    
    selection = dialog.prompt_option(menu_items, none_text = _UITEXT_NONE, text = _UITEXT_CHANNELS, title = _APP_TITLE)
    if selection:
        func = selection['function']
        func()
    main_menu()

def show_channel_console():
    # console_items = [
    #     enter_console_msg,
    #     send_msg,
    # ]

    # draw_console_view()
    # while True:

    #     if buttons.ispressed(Buttons.BTN_B) or buttons.ispressed(Buttons.BTN_Menu):
    #         break

    #     time.sleep(_CONSOLE_REFRESH)
    pass

def draw_console_view():
    ugfx.clear()
    # do something
    pass

# def enter_console_msg():
#     return user_text_input(_UITEXT_INPUT_CONSOLE)

# def send_msg(msg):
#     _CLIENT.send_msg(msg)

def update_console_view():
    # do something
    pass

def on_pubmsg():
    pass

def on_privmsg():
    pass

def on_join():
    pass

def on_kick():
    pass

def on_quit():
    pass

def on_nick():
    pass
### END: UI functions

# Run the app!
wifi.connect(show_wait_message = True)
main()

# App finished, time to clear up
ugfx.clear()
app.restart_to_default()