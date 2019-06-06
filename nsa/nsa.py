import asyncio

from hauptbahnhof import Hauptbahnhof

class NSA:
    """
    Scan the local hackerspace network for new and unknown devices to send back a result
    """

    def __init__(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.hbf = Hauptbahnhof("nsa", loop)
        self.hbf.subscribe('/haspa/nsa/scan', self.command_scan)

    async def teardown(self):
        """
        Clean up your stuff...
        """
        await self.hbf.teardown()

    async def command_scan(self, client, message, _):
        """
        space.get_number_of_network_devices() -> int
        Return the number of non-stationary, connected network devices.
        """
        try:
            cfg = self.hbf.config("arplist")
        except FileNotFoundError as exc:
            self.hbf.log.warning("Coult not find config:%s", str(exc))
            cfg = {}

        known_devices = []
        try:
            known_devices = message['blacklist']
        except (KeyError, TypeError):
            known_devices = []

        try:
            known_devices += cfg['spacedevices']
        except KeyError:
            self.hbf.log.warning("You might want to configure space devices")

        # TODO use util/arp-scan
        proc = await asyncio.create_subprocess_exec(
            *['arp-scan', cfg['space_network']],
            stdout=asyncio.subprocess.PIPE,
            loop=self.loop)

        output, _ = await proc.communicate()
        for line in output.decode('utf8').split('\n'):
            self.hbf.log.debug(line)
        output = output.decode('utf8').split()

        dev_list = []

        for line in output:
            if line.find(':') != -1 and len(line) == 17:
                if line not in known_devices:
                    dev_list.append(line)

        await self.hbf.publish('/haspa/nsa/result', {'count': len(dev_list)})
