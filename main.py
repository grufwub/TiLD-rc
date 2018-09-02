___name___         = "TiLD-rc"
___license___      = "MIT"
___dependencies___ = ["wifi", "http", "ugfx_helper", "sleep", "app"] # TODO: add py irc dependency, figure out how this works with micro pip?
___categories___   = ["EMF"]
___bootstrapped___ = False

import ugfx_helper, os, wifi, ugfx, http, time, sleep, app
from tilda import Buttons

ugfx_helper.init()
ugfx.clear()



# ugfx.text(5, 5, "Loading...", ugfx.BLACK)
# try:
#     image = http.get("http://s3.amazonaws.com/tilda-badge/sponsors/screen.png").raise_for_status().content
#     ugfx.display_image(0,0,bytearray(image))
# except:
#     ugfx.clear()
#     ugfx.text(5, 5, "Couldn't download sponsors", ugfx.BLACK)

# while (not Buttons.is_pressed(Buttons.BTN_A)) and (not Buttons.is_pressed(Buttons.BTN_B)) and (not Buttons.is_pressed(Buttons.BTN_Menu)):
#     sleep.wfi()

ugfx.clear()
app.restart_to_default()