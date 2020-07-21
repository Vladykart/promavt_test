# This file is executed on every boot (including wake-boot from deepsleep)
# import esp
# esp.osdebug(None)
# uos.dupterm(None, 1) # disable REPL on UART(0)

import gc
from utime import sleep_ms


def no_debug():
    import esp
    # you can run this from the REPL as well
    esp.osdebug(None)


def webrepl_mode():
    from machine import Pin
    p0 = Pin(0, Pin.IN)
    if p0.value() == 0:
        import webrepl
        webrepl.start_foreground()
    else:
        pass


no_debug()

webrepl_mode()
sleep_ms(10000)
gc.collect()
