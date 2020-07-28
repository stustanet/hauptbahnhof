import gc

print("GC preboot", gc.mem_free())
try:
    import rupprecht

    import webrepl

    webrepl.start()
    gc.collect()

    import network

    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)

    rupprecht.main()
except KeyboardInterrupt:
    pass
except Exception as e:
    print("error", e)
    import sys

    sys.print_exception(e)
    import machine

    machine.reset()
