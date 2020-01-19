import paho.mqtt.client as mqtt
import json

# maximum recursion depth in translation
MAX_TTL=5

class Babel:
    def __init__(self, config="/etc/hauptbahnhof/realms.json"):
        with open(config) as cfgfile:
            if not self.parse_config(cfgfile):
                raise RuntimeError("Error in config.")
        self.dfnode_state = {}

        self.mqtt = mqtt.Client()
        self.mqtt.on_message = self.on_message
        self.mqtt.on_connect = lambda mqtt, obj, flags, rc: \
            self.subscribe_to_config(self.config)
        self.mqtt.on_message = self.on_message
        #self.mqtt.on_log = self.on_log

        self.connect()

    def connect(self):
        self.mqtt.connect("knecht.stusta.de", 1883)

    def on_log(self, mqttc, obj, level, string):
        print("mqtt: ", string)

    def run(self):
        self.mqtt.loop_forever()

    def parse_config(self, config):
        self.config = json.load(config)

        # now process every path in the final translation result if it is parsable
        success = True
        for source, targets in self.config['translation'].items():
            if source in ['documentation']:
                # skip documentation paragraphs, because they are actually needed
                continue
            for target in targets:
                if target not in self.config['translation']:
                    # sanity check the node configuration
                    try:
                        cfg = self.topicconfig(target)
                    except KeyError:
                        success = False
                        print("Cannot translate output path: ", target, "for translating from ", source)
                        continue
                    try:
                        if cfg['type'] == "dfnode":
                            _ = cfg['topic'] # require topic
                            _ = cfg['espid'] # require espid
                            index = cfg['index'] # 0 <= index < 8
                            if int(index) < 0 or int(index) >= 8:
                                print("index must be between (including) 0 and (excluding) 8")
                                success = False
                        elif cfg['type'] == "delock":
                            _ = cfg['topic'] # require topic

                    except KeyError as e:
                        print("could not find expected element", e, "in path ", target)
                        success = False
                    except ValueError as e:
                        print("could not convert to int", e)
                        success = False

        return success

    def make_baseconfig_tree(self, subtree, path):
        data = []
        for key, value in subtree.items():
            if isinstance(value, dict):
                data += self.make_baseconfig_tree(value, path + "/" + key)
            else:
                return [path]
        return data

    def subscribe_to_config(self, config):
        try:
            print("Connected")
            # subscribe to all basechannels
            baseconfig = self.make_baseconfig_tree(config['basechannels'], "")

            # subscribe to all translated topics
            baseconfig += config['translation'].keys()
            print("Subcribing to topics:\n\t", "\n\t".join(baseconfig))
            self.mqtt.subscribe([
                (topic, 0) for topic in baseconfig])
        except Exception as e:
            print('subscribe', e)

    def on_message(self, mqtt, userdata, msg):
        print("msg", msg.topic, ":", msg.payload)
        try:
            # TODO sanitize Payload:
            # has to be 0 - 100 integer or string
            payload = int(msg.payload)
            self.handle_message(msg.topic, payload, MAX_TTL)
        except Exception as e:
            print('on_message', e)

    def handle_message(self, topic, payload, ttl):
        if ttl <= 0:
            raise RuntimeError("ttl exceeded")
        if topic in self.config['translation']:
            for subtopic in self.config['translation'][topic]:
                self.handle_message(subtopic, payload, ttl-1)
        else:
            self.send_message(topic, payload)

    def send_message(self, topic, payload):
        cfg = self.topicconfig(topic)

        if cfg['type'] == "dfnode":
            self.send_dfnode(cfg, topic, payload)
        elif cfg['type'] == "delock":
            self.send_delock(cfg, topic, payload)
        else:
            print("Config had unknown type", cfg['type'])

    def topicconfig(self, topic):
        try:
            cfg = self.config['basechannels']
            for layer in topic.split("/"):
                if not layer:
                    continue
                cfg = cfg[layer]
            return cfg
        except KeyError:
            raise KeyError("Cannot find basechannel " + topic)

    def send_dfnode(self, cfg, topic, payload):
        if cfg['topic'] not in self.dfnode_state:
            self.dfnode_state[cfg['topic']] = [0] * 8

        self.dfnode_state[cfg['topic']][int(cfg['index'])] = payload

        #print("Sending ", self.dfnode_state[cfg['topic']], "to", cfg['topic'])

        payload = {cfg['espid']: self.dfnode_state[cfg['topic']]}
        self.mqtt.publish(cfg['topic'], json.dumps(payload))


    def send_delock(self, cfg, topic, payload):
        msg = "OFF" if payload == 0 else "ON"
        self.mqtt.publish(cfg['topic'], msg)


def test():
    babel = Babel(config="./config.json")
    babel.run()

if __name__ == "__main__":
    test()
