import asyncio
from hauptbahnhof import Hauptbahnhof

class Babel:
    """
    Translate the messages that arrived into new messages and accumulate their results
    """

    def __init__(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.hbf = Hauptbahnhof("babel", loop)
        self.hbf.subscribe('/haspa/power', self.command_translate)
        self.hbf.subscribe('/haspa/power/requestinfo', self.command_requestinfo)
        self.hbf.subscribe('/haspa/power/status', self.command_requeststatus)

        self.ledstrip_states = [[0] * 8, [0] * 8]
        #self.espids = ['a9495a00', 'c14e5a00']
        # new 4 channel ESPs
        self.espids = ['f97c7300', 'dfd80b00']

        # mapps from (color, id) ==> (self.ledstrip indexes)
        self.idxpair = {
            ('c', 2):(0, 0),
            ('w', 2):(0, 1),
            ('c', 1):(0, 6),
            ('w', 1):(0, 7),
            ('c', 3):(1, 0),
            ('w', 3):(1, 1),
            ('c', 4):(1, 2),
            ('w', 4):(1, 3),
            }

        self.rupprecht_map = {
            'table': ('rupprecht-table', 0),
            'alarm': ('rupprecht-alarm', 0),
            'fan': ('rupprecht-fan', 0),
        }

    async def teardown(self):
        """ clean up after yourself """
        await self.hbf.teardown()

    async def command_translate(self, client, message, _):
        """
        space.get_number_of_network_devices() -> int
        Return the number of non-stationary, connected network devices.
        """
        del client
        group_changed = False
        msg = {}
        for lamp, value in sorted(message.items()):
            ## The lamp is managed by rupprecht
            if lamp in self.rupprecht_map:
                msg[self.rupprecht_map[lamp][0]] = int(value)
                self.rupprecht_map[lamp] = (self.rupprecht_map[lamp][0], int(value))

            ## The lamp is a led strip and needs to be aggregated
            if lamp.startswith('ledstrip'):
                tmp = lamp.split('-')
                if len(tmp) == 1:
                    for a, b in self.idxpair.values():
                        group_changed |= self.ledstrip_states[a][b] != int(value)
                        self.ledstrip_states[a][b] = int(value)

                elif len(tmp) == 2 and tmp[1] in ('c', 'w'):
                    for color, position in self.idxpair:
                        if color == tmp[1]:
                            idx = self.idxpair[(color, position)]
                            group_changed |= self.ledstrip_states[idx[0]][idx[1]] != int(value)
                            self.ledstrip_states[idx[0]][idx[1]] = int(value)

                elif len(tmp) == 3 and tmp[1] in ('c', 'w') and abs(int(tmp[2])) <= 4:
                    idx = self.idxpair[(tmp[1], abs(int(tmp[2])))]
                    group_changed |= self.ledstrip_states[idx[0]][idx[1]] != int(value)
                    self.ledstrip_states[idx[0]][idx[1]] = int(value)

        self.hbf.log.info(self.ledstrip_states)
        if group_changed:
            for idx, ledidx in enumerate(self.espids):
                msg[ledidx] = self.ledstrip_states[idx]
        await self.hbf.publish('/haspa/led', msg)
        print("Mapped Reduced Message: ", msg)

    async def command_requestinfo(self, client, msg, _):
        """
        Request details about configured led mappings
        """
        del client, msg
        await self.hbf.publish('/haspa/power/info', {
            'documentation':'too lazy to implement'
        })

    async def command_requeststatus(self, client, msg, _):
        msg = {}
        for idx, espid in enumerate(self.espids):
            msg[espid] = self.ledstrip_states[idx]

        for rupid, value in self.rupprecht_map.values():
            msg[rupid] = value

        print("Full message: ", msg)
        await self.hbf.publish('/haspa/led', msg)
