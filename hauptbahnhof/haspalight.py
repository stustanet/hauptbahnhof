import rcswitch
import requests
import time

class HaspaLight:
    def __init__(self, rupprecht, loop=None, soundboard='http://bot.stusta.de'):
        if loop == None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.rupprecht = rupprecht
        self.soundboard = soundboard

        self.light = rcswitch.Quigg1000(code=1337, subaddr=1, loop=loop, rupprecht=rupprecht)
        self.alarm = rcswitch.Quigg1000(code=1337, subaddr=2, loop=loop, rupprecht=rupprecht)
        self.fan = rcswitch.Quigg1000(code=1337, subaddr=3, loop=loop, rupprecht=rupprecht)

        self.state = 'closed'
        self.last_party = 0

    async def open(self):
        self.state = 'open'
        # TODO: Check temperature
        await self.light.on()
        await self.alarm.off()

    async def close(self):
        self.state = 'closed'
        await self.light.off();
        await self.alarm.off();
        await self.fan.off();

    async def party(self):
        if self.last_party > time.time() - 60:
            self.last_party = time.time()
            print("rate limiting the party")
            return
        self.last_party = time.time()
        try:
            #if random.randint(0, 3) != 1:
            #    print("Skipping sound")
            #    return
            print("starting party")
            await self.light.off()
            await asyncio.sleep(1)
            await self.alarm.on()
            #requests.get('{}/set/56'.format(self.soundboard), timeout=0.1)
            requests.get('{}/set/110'.format(self.soundboard), timeout=0.1)
            await asyncio.sleep(4)
        except requests.exceptions.Timeout:
            print("connection timed out")
        finally:
            if self.state == 'open':
                await self.alarm.off()
                self.light.on()
