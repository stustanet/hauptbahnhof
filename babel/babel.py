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
        self.hbf = Hauptbahnhof(loop)
        self.hbf.subscribe('/haspa/power', self.command_translate)
        self.hbf.subscribe('/haspa/power/requestinfo', self.command_requestinfo)

        self.ledstrip_states = [[0,0,0,0], [0,0,0,0]]
        self.espids = ['a9495a00','024c5a00']

        # TODO create this mapping:
        # mapps from (color, id) ==> (self.ledstrip indexes)
        self.idxpair = {
            ('c',1):(0,0),
            ('w',1):(0,1),
            ('c',2):(0,2),
            ('w',2):(0,3),
            ('c',3):(1,0),
            ('w',3):(1,1),
            ('c',4):(1,2),
            ('w',4):(1,3),
            }

        self.rupprecht_map = {
            'table': 'rupprecht-table',
            'alarm': 'rupprecht-alarm',
            'fan': 'rupprecht-fan',
        }

    async def teardown(self):
        await self.hbf.teardown()

    async def command_translate(self, client, message, _):
        """
        space.get_number_of_network_devices() -> int
        Return the number of non-stationary, connected network devices.
        """
        group_changed = False
        msg = {}
        for lamp, value in message.items():
            ## The lamp is managed by rupprecht
            if lamp in self.rupprecht_map:
                msg[self.rupprecht_map[lamp]] = int(value)

            ## The lamp is a led strip and needs to be aggregated
            if lamp.startswith('ledstrip'):
                tmp = lamp.split('-')
                if len(tmp) == 1:
                    for a, b in self.idxpair.values():
                        group_changed |= self.ledstrip_states[a][b] != int(value)
                        self.ledstrip_states[a][b] = int(value)

                elif len(tmp) == 2 and tmp[1] in ('c','w'):
                    for color, position in self.idxpair:
                        if color == tmp[1]:
                            idx = self.idxpair[(color, position)]
                            group_changed |= self.ledstrip_states[idx[0]][idx[1]] != int(value)
                            self.ledstrip_states[idx[0]][idx[1]] = int(value)

                elif len(tmp) == 3 and tmp[1] in ('c', 'w') and abs(int(tmp[2])) <= 4:
                    idx = self.idxpair[(tmp[1],abs(int(tmp[2])))]
                    group_changed |= self.ledstrip_states[idx[0]][idx[1]] != int(value)
                    self.ledstrip_states[idx[0]][idx[1]] = int(value)

        self.hbf.log.info("Done mapping: ")
        self.hbf.log.info(self.ledstrip_states)
        if group_changed:
            for idx, e in enumerate(self.espids):
                msg[e] = self.ledstrip_states[idx]
        await self.hbf.publish('/haspa/led', msg)

    async def command_requestinfo(self, client, msg, _):
        await self.hbf.publish('/haspa/power/info', {
            'documentation':'too lazy to implement'
        })
