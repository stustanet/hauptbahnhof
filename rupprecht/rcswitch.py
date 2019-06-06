#!/usr/bin/python3
"""
generate packets for quigg rc switches
"""
import argparse
import serial
import asyncio

class Quigg1000:
    def __init__(self, loop=None, serial=None, rupprecht=None, code=1337, subaddr=0):
        """
        Create a new switch representation
        The switch can either be connected to a raw-serial port (old arduino)
        or it can be connected via a rupprecht-interface, that will handle all interfacing
        """
        if loop == None:
            loop=asyncio.get_event_loop()
        self.loop = loop
        self.serial = serial
        self.rupprecht = rupprecht
        self.code = code
        self.subaddr = str(subaddr)

        if serial != None and rupprecht != None:
            raise ArgumentException("Only one of serial and rupprecht may be set")


    async def state(self, state, debug=False):
        """
        Set the switch to the value indicated by state (true or false)
        """
        msg = self.__build_msg(state, debug=debug)
        if debug:
            print(msg)
        await self.__send_msg(msg)

    async def on(self, debug=False):
        msg = self.__build_msg(True, debug=debug)
        if debug:
            print(msg)
        await self.__send_msg(msg)

    async def off(self, debug=False):
        msg = self.__build_msg(False, debug=debug)
        if debug:
            print(msg)
        await self.__send_msg(msg)

    def __build_msg(self, state, dimm=0, debug=False):
        """
        Build a quigg message.
        Read the inline docs for details

        state: 1 bit value: True: On, False: Off
        dimm: ??
        """
        # key on remote -> real addr mapping
        key_lookup = {'1': 0, '2': 1, '4': 2, '3': 3}
        # 12 bits set code addr
        set_code = '{0:0>12b}'.format(self.code)
        # 2 bit addr of rc switch
        addr = '{0:0>2b}'.format(key_lookup[self.subaddr])[::-1]
        # address all rf devices (not implemented)
        allflag = '0'
        # 1 bit state
        state = '1' if int(state) else '0'
        # 2 bit dimm information
        dimm = '{0:0>2}'.format(dimm)
        # repeat bit 13 / addr bit 0
        internal = addr[0]
        # build buffer with leading 1
        buffer_string = '1' + set_code + addr + allflag + state + dimm + internal
        # parity over last 7 bits
        parity_bit = '1' if buffer_string[13:20].count('1') % 2 else '0'
        # append parity bit
        buffer_string += parity_bit

        if debug:
            print('set code:\t{}'.format(set_code))
            print('addr:\t\t{}'.format(addr))
            print('state:\t\t{}'.format(state))
            print('dimm:\t\t{}'.format(dimm))
            print('internal:\t{}'.format(internal))
            print('parity range:\t{}'.format(buffer_string[13:20]))
            print('parity bit:\t{}'.format(parity_bit))
            print('\nbuffer string:\t{}'.format(buffer_string))

        if len(buffer_string) != 21:
            print('Bad packet length.')
            return None
        return buffer_string

    async def __send_msg(self, msg):
        if self.rupprecht:
            print("sending via rupprecht message", msg)
            await self.rupprecht.light(msg)
            await asyncio.sleep(1)
        if self.serial:
            print("sending via raw message", msg)
            try:
                self.serial.write(str.encode(msg))
                await asyncio.sleep(1)
            except serial.SerialException:
                print('Serial communication failed.')

def main():
    parser = argparse.ArgumentParser(description='Remote COntrol rc switches')
    parser.add_argument('addr', help='number of the switch')
    parser.add_argument('state', help='1 (on) or 0 (off)')
    parser.add_argument('--set-code', '-c', help='set-code-number',
                        default=2816, type=int)
    parser.add_argument('--dimm', help='dimm value', default=0)
    parser.add_argument('--device',
                        help='serial device path/name (e.g. COM11 or /dev/ttyUSB3)',
                        default='/dev/ttyUSB3')
    parser.add_argument('--debug', '-d', help='enable debug output',
                        default=False, action='store_true')

    args = parser.parse_args()
    loop=asyncio.get_event_loop()

    try:
        s = serial.Serial(args.device, 9600)
    except serial.SerialException:
        print('Serial communication failed.')
        exit()

    r = Quigg1000(serial=s, loop=loop, code=args.set_code, subaddr=args.addr)
    loop.run_until_complete(r.state(args.state, args.debug))

if __name__ == '__main__':
    main()
