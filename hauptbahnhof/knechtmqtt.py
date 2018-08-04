import logging
from paho.mqtt.client import Client as PahoMqttClient

class MQTTBahnhofClient:
    """
    A simplified hauptbahnhof client that is able to connect to a remote mqtt
    with username password and certificates
    """
    def __init__(self, config, subscriptions):
        logformat = '%(asctime)s | %(name)s | %(levelname)5s | %(message)s'
        logging.basicConfig(format=logformat)
        self.log = logging.getLogger(__name__)
        if config['hauptbahnhof']['debug']:
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.INFO)

        self.host = config['hauptbahnhof']['host']
        self.subscriptions = subscriptions

        self.mqtt = PahoMqttClient()
        self.mqtt.enable_logger(self.log)
        self.mqtt.on_message = self.on_message
        self.mqtt.on_connect = self.on_connect

        ssl = {"ca_certs": config['hauptbahnhof']['ca_crt'],
               "certfile": config['hauptbahnhof']['certfile'],
               "keyfile":  config['hauptbahnhof']['keyfile']}
        self.mqtt.tls_set(**ssl)

        auth = {"username": config['hauptbahnhof']['username'],
                "password": config['hauptbahnhof']['password']}
        self.mqtt.username_pw_set(**auth)

    def on_message(self, client, userdata, msg):
        """
        A message was received. push it back towards the async context
        """
        self.log("Unhandled message has arrived: %s %s %s", client, userdata, msg)

    def on_connect(self, client, userdata, flags, returncode):
        """ After a successfull connection the topics are set and subscribed """
        del client, userdata
        if returncode == 0:
            print("Flags: ", flags)
            self.mqtt.subscribe([(topic, 0) for topic in self.subscriptions])

            if not 'session present' in flags or flags['session present'] == 0:
                # If we have a new session
                for topic, callback in self.subscriptions.items():
                    if callback:
                        self.mqtt.message_callback_add(topic, callback)

        else:
            try:
                msg = {
                    0: "Connection successful",
                    1: "Incorrect Protocol Version",
                    2: "Invalid client identifier",
                    3: "Server unavailable",
                    4: "Bad username or password",
                    5: "Not authorized",
                }[returncode]
            except KeyError:
                msg = "Unknown error occured: " + returncode
            print("Connection refused: ", msg)


    def publish(self, topic, data):
        """ Publish a message """
        self.mqtt.publish(topic, data)

    def start(self, spinoff=True):
        """ Connect and start the mqtt machine """
        self.mqtt.connect(self.host, port=8883)
        self.log.info("Successfully connected to %s", self.host)

        # Spinning of a thread for the magic
        if spinoff:
            self.mqtt.loop_start()
        else:
            self.mqtt.loop_forever()
