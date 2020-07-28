import json
from typing import Optional, Dict

from hauptbahnhof import Hauptbahnhof

# maximum recursion depth in translation
MAX_TTL = 15


class Babel(Hauptbahnhof):
    def __init__(self):
        super().__init__("babel")
        self._load_config("babel")
        self.dfnode_state = {}

    def on_connect(self, client, userdata, flags, rc):
        super().on_connect(client, userdata, flags, rc)
        self.subscribe_to_config()

    def parse_config(self):
        # now process every path in the final translation result if it is parsable
        success = True
        for source, targets in self.config["translation"].items():
            if source in ["documentation"]:
                # skip documentation paragraphs, because they are actually needed
                continue
            for target in targets:
                if target not in self.config["translation"]:
                    # sanity check the node configuration
                    cfg = self.topicconfig(target)
                    if not cfg:
                        success = False
                        self.log.error(
                            "Cannot translate output path: "
                            "%s for translating from %s",
                            target,
                            source,
                        )
                        continue

                    if cfg["type"] == "dfnode":
                        if "topic" not in cfg or "espid" not in cfg:
                            self.log.error(
                                "missing 'topic' or 'espid' in config %s", cfg
                            )
                            success = False
                            continue

                        index: str = cfg["index"]  # 0 <= index < 8

                        if not index.isnumeric():
                            self.log.error("cannot convert index to int: %s", index)
                            success = False
                            continue

                        if int(index) < 0 or int(index) >= 8:
                            self.log.error(
                                "index must be between (including) 0 "
                                "and (excluding) 8"
                            )
                            success = False
                            continue
                    elif cfg["type"] == "delock":
                        if "topic" not in cfg:
                            self.log.error("missing 'topic' in config %s", cfg)
                            success = False
                            continue

        return success

    def make_baseconfig_tree(self, subtree, path):
        data = []
        for key, value in subtree.items():
            if isinstance(value, dict):
                data += self.make_baseconfig_tree(value, path + "/" + key)
            else:
                return [path]
        return data

    def subscribe_to_config(self):
        base_config = self.make_baseconfig_tree(self.config["basechannels"], "")

        # subscribe to all translated topics
        base_config += self.config["translation"].keys()
        self.log.info("Subcribing to topics: %s", ", ".join(base_config))
        self._mqtt.subscribe([(topic, 0) for topic in base_config])

    def on_message(self, msg):
        self.log.debug(f"msg {msg.topic}: {msg.payload}")
        try:
            # TODO sanitize Payload:
            # has to be 0 - 100 integer or string
            payload = int(msg.payload)
            self.handle_message(msg.topic, payload, MAX_TTL)
        except Exception as e:
            self.log.warning(
                "Received invalid payload in topic %s. Got error %s.", msg.topic, e
            )

    def handle_message(self, topic, payload, ttl):
        # Handle /haspa/licht = 0 messages seperately, and turn _everything_ off
        if topic == "/haspa/licht" and payload == 0:
            # send a 0 message to every configured base channel
            baseconfig = self.make_baseconfig_tree(self.config["basechannels"], "")
            for channel in baseconfig:
                self.send_message(channel, payload)
            return

        if ttl <= 0:
            raise RuntimeError("ttl exceeded")
        if topic in self.config["translation"]:
            for subtopic in self.config["translation"][topic]:
                self.handle_message(subtopic, payload, ttl - 1)
        else:
            self.send_message(topic, payload)

    def send_message(self, topic: str, payload: str):
        cfg = self.topicconfig(topic)

        if cfg["type"] == "dfnode":
            self.send_dfnode(cfg, topic, payload)
        elif cfg["type"] == "delock":
            self.send_delock(cfg, topic, payload)
        else:
            self.log.warning("Config had unknown type %s", cfg["type"])

    def topicconfig(self, topic: str) -> Optional[Dict]:
        cfg = self.config["basechannels"]
        for layer in topic.split("/"):
            if not layer:
                continue

            if layer not in cfg:
                self.log.error("Cannot find base channel %s", topic)
                return None

            cfg = cfg[layer]
        return cfg

    def send_dfnode(self, cfg: Dict, topic: str, payload):
        if cfg["topic"] not in self.dfnode_state:
            self.dfnode_state[cfg["topic"]] = [0] * 8

        self.dfnode_state[cfg["topic"]][int(cfg["index"])] = payload

        # print("Sending ", self.dfnode_state[cfg['topic']], "to", cfg['topic'])

        payload = {cfg["espid"]: self.dfnode_state[cfg["topic"]]}
        self.publish(cfg["topic"], json.dumps(payload))

    def send_delock(self, cfg: Dict, topic: str, payload):
        msg = "OFF" if payload == 0 else "ON"
        self.publish(cfg["topic"], msg)
