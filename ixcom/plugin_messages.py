from .protocol import plugin_message, DefaultPluginMessagePayload, Message, PayloadItem



class GenericPluginMessagePayload(DefaultPluginMessagePayload):
    plugin_message_payload = Message([
        PayloadItem(name = 'data', dimension = 4096-4, datatype = "B"),
    ])
