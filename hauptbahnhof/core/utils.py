from collections import namedtuple

MQTTUpdate = namedtuple("MQTTUpdate", ("topic", "payload"))
StateUpdate = namedtuple("StateUpdate", ("topic", "value"))
