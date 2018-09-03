_APP_TITLE = "TiLD-rc"

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

# Required app variables
_CLIENT = None
_CONSOLE_BUF = None
_CONSOLE_REFRESH = 0.1
_BUF_MAX = 50
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
        show_channel_console()
    
    except:
        display_error(_ERRMSG_CONNECT_FAIL)

    finally:
        # do something else
        del _CLIENT
        del _CONSOLE_BUF
        main()

def show_channels():
    # do something
    pass

def show_channel_console():
    console_items = [
        enter_console_msg,
        send_msg,
    ]

    _CONSOLE_BUF = collections.deque(maxlen = _BUF_MAX)
    while True:
        _CONSOLE_BUF.append(retrieve_msgs())
        update_console_view()

        if buttons.ispressed(Buttons.BTN_B) or buttons.ispressed(Buttons.BTN_Menu):
            break

        time.sleep(_CONSOLE_REFRESH)

    # some other things

def enter_console_msg():
    return user_text_input(_UITEXT_INPUT_CONSOLE)

def send_msg(msg):
    _CLIENT.send_msg(msg)

def retrieve_msgs():
    # do something
    return

def update_console_view():
    # do something
    pass
### END: UI functions

# Run the app!
wifi.connect(show_wait_message = True)
main()

# App finished, time to clear up
ugfx.clear()
app.restart_to_default()