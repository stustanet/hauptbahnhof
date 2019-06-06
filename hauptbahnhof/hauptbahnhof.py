import json
import asyncio
import traceback
import io
import sys
import logging

import libconf
import aiomqtt

class Hauptbahnhof:
    """
    Hauptbahnhof manager with a lot of convenience methods
    """

    def __init__(self, name, loop=None):
        try:
            idx = sys.argv.index('--confdir')
            self._configbase = sys.argv[idx + 1]
        except (ValueError, KeyError):
            self._configbase = '/etc/hauptbahnhof'

        if not loop:
            loop = asyncio.get_event_loop()

        self.loop = loop
        # find master config
        self._config = self.config("hauptbahnhof")

        self._host = self._config['host']

        self._subscriptions = {}
        self._mqtt = None
        self._mqtt_queue = []

        self._mqtt_start_task = self.loop.create_task(self.start())
        self._queue = asyncio.Queue()
        self._message_process_task = self.loop.create_task(self.message_processing())
        self.connected = asyncio.Event(loop=self.loop)

        logformat = '%(name)s | %(levelname)5s | %(message)s'
        logging.basicConfig(format=logformat)
        self.log = logging.getLogger(name)
        self.log.setLevel(logging.INFO)

    async def teardown(self):
        """
        The last one switches off the light
        """
        self._mqtt_start_task.cancel()
        self._message_process_task.cancel()

        results = await asyncio.gather(self._mqtt_start_task,
                                        self._message_process_task,
                                        return_exceptions=True)
        for r in results:
            if isinstance (r, Exception):
                if not isinstance(r, asyncio.CancelledError):
                    traceback.print_exception(type(r), r, r.__traceback__)

    async def start(self):
        """
        Start the mqtt locally, and when it is connected send it back
        """

        mqtt = aiomqtt.Client(self.loop)
        mqtt.loop_start()

        mqtt.on_message = self.on_message
        mqtt.on_connect = lambda client, userdata, flags, rc: self.connected.set()
        try:
            await mqtt.connect(self._host)
        except:
            self.log.error("Could not connect to %s", self._host)
            self.loop.cancel()
            raise
        await self.connected.wait()

        self.log.info("Successfully connected to %s", self._config['host'])
        for topic in self._subscriptions:
            mqtt.subscribe(topic)

        self._mqtt = mqtt
        while self._mqtt_queue:
            topic, msg = self._mqtt_queue.pop(0)
            self.log.debug("Topic: %s", topic)
            self._mqtt.publish(topic, msg)

        # Now we have mqtt available!
        self._mqtt = mqtt

    async def message_processing(self):
        while True:
            try:
                (client, userdata, msg) = await self._queue.get()
                # is called when a message is received
                try:
                    payload = msg.payload.decode('utf-8')
                except UnicodeDecodeError:
                    continue

                try:
                    futures = self._subscriptions[msg.topic]
                except KeyError:
                    # Received unknown message - this is strange, log and ignore
                    self.log.info("Received unsubscribed message on %s with content: %s"%(
                        msg.topic, msg.payload))

                try:
                    payloadobj = json.loads(payload)
                except json.JSONDecodeError:
                    self.log.info("Invalid json received: %s"%payload)
                    continue
                except:
                    continue

                try:
                    await asyncio.gather(*[fut(client, payloadobj, msg) for fut in futures])
                except Exception:
                    traceback.print_exc()
                    continue
            except asyncio.CancelledError:
                break

            except Exception:
                traceback.print_exc()
                continue

    def on_message(self, client, userdata, msg):
        self._queue.put_nowait((client, userdata, msg))


    def config(self, module):
        """
        Load a config from the pile of configs ( usually in /etc/hauptbahnhof/*.conf )
        """
        with io.open('%s/%s.conf'%(self._configbase, module), 'r') as f:
            return libconf.load(f)

    def subscribe(self, topic, coroutine):
        """
        Subscribe to topic
        """
        try:
            self._subscriptions[topic].append(coroutine)
        except KeyError:
            self._subscriptions[topic] = [coroutine]

        if self._mqtt:
            self._mqtt.subscribe(topic)

    async def publish(self, topic, message):
        """
        Publish a message on the given topic
        """
        jsonmsg = json.dumps(message)

        # Maybe the system is not already online?
        if self._mqtt:
            await self._mqtt.publish(topic, jsonmsg).wait_for_publish()
        else:
            self._mqtt_queue.append((topic, jsonmsg))

    def mqtt(self):
        """
        Get the underlying mqtt object. For debug use only!
        """
        return self._mqtt
