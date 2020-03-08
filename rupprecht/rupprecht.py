import machine
from machine import Pin
from umqtt.simple import MQTTClient
import ujson as json
import network
import gc
import time
import sys


LED_R = 14
LED_G = 12
LED_B = 13
BTN_STATUS = 15
BTN_VOL_PLUS = 2
BTN_VOL_MINUS = 4
BTN_PLAY = 0


CONFIG = {
    'mqtt_server': '192.168.13.37',
    'status_topic': '/haspa/status',
    'music_topic': '/haspa/music/control'
}


class Rupprecht:
    def __init__(self, config):
        self.config = config
        self.mqtt = None

        self.pin_led_r = machine.PWM(Pin(LED_R, Pin.OUT))
        self.pin_led_g = machine.PWM(Pin(LED_G, Pin.OUT))
        self.pin_led_b = machine.PWM(Pin(LED_B, Pin.OUT))

        self.in_pins = [
            Pin(BTN_STATUS, Pin.IN, Pin.PULL_UP),
            Pin(BTN_PLAY, Pin.IN, Pin.PULL_UP),
            Pin(BTN_VOL_PLUS, Pin.IN, Pin.PULL_UP),
            Pin(BTN_VOL_MINUS, Pin.IN, Pin.PULL_UP)
        ]
        self.bounces = [0, 0, 0, 0]
        self.curr_pin_states = [pin.value() for pin in self.in_pins]

        self.pin_led_r.freq(1000)
        self.set_led(0, 0, 1023)

        print("GC After boot", gc.mem_free())

    def init(self):
        gc.collect()

        sta_if = network.WLAN(network.STA_IF)

        while not sta_if.isconnected():
            print('[?] Waiting for network connection...')
            time.sleep(0.2)

        # Network is available
        print("[*] IP address: ", sta_if.ifconfig()[0])

    def connect(self):
        self.mqtt = MQTTClient('rupprecht', self.config['mqtt_server'])
        self.mqtt.set_callback(self.on_message)
        self.mqtt.connect()

    def on_message(self, topic, msg):
        try:
            msg = msg.decode('utf-8')
            data = json.loads(msg)
        except:
            print("[!] Json error: ", msg)

    def run(self):
        gc.collect()
        self.running = True
        self.update_status()

        while self.running:
            gc.collect()
            for i in range(4):  # debounce input pins
                if self.in_pins[i].value() != self.curr_pin_states[i]:
                    if self.bounces[i] >= 20:  # steady for 20ms
                        self.curr_pin_states[i] = self.in_pins[i].value()
                        self.pin_changed(i)
                        self.bounces[i] = 0
                    else:
                        self.bounces[i] += 1
                else:
                    if self.bounces[i] > 0:
                        self.bounces[i] -= 1

            self.mqtt.check_msg()
            time.sleep(0.001)

    def set_led(self, r, g, b):
        self.pin_led_r.duty(r)
        self.pin_led_g.duty(g)
        self.pin_led_b.duty(b)

    def pin_changed(self, index):
        print('[*] Pin changed', index)
        if index == 0:
            self.update_status()
        elif index == 1 and self.curr_pin_states[index] == 0:
            payload = json.dumps({
                'play': True
            })
            #self.mqtt.publish(self.config['music_topic'], payload)
        elif index == 2 and self.curr_pin_states[index] == 0:
            payload = json.dumps({
                'volume': '+5'
            })
            #self.mqtt.publish(self.config['music_topic'], payload)
        elif index == 3 and self.curr_pin_states[index] == 0:
            payload = json.dumps({
                'volume': '-5'
            })
            #self.mqtt.publish(self.config['music_topic'], payload)

    def update_status(self):
        """change space status, 0 corresponds to open, 1 to closed"""
        payload = json.dumps({
            'haspa': 'open' if self.curr_pin_states[0] == 0 else 'closed'
        })
        if self.curr_pin_states[0] == 0:
            self.set_led(0, 1023, 0)
        else:
            self.set_led(1023, 0, 0)
        #self.mqtt.publish(self.config['status_topic'], payload)

    def main(self):
        self.init()

        while True:
            # network is available, dropping out of here recreates network context
            print("[?] Starting setup")
            try:
                self.connect()
                gc.collect()
                print("[*] Ready for messages")
                self.run()
                gc.collect()
                print("[!] connection loop terminated. reinitializing")
            except KeyboardInterrupt:
                # filter out and allow keyboard interrupts
                raise
            except Exception as exc:
                #raise e # For debug times
                sys.print_exception(exc)
                print("Sleeping for 10 seconds")
                time.sleep(10)
                machine.reset()


rupprecht = Rupprecht(CONFIG)


def main():
    rupprecht.main()


if __name__ == '__main__':
    main()
