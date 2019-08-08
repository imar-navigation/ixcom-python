Basic communications
====================

.. code-block:: python

    import ixcom
    
    client = ixcom.Client('192.168.1.30')
    client.open_last_free_channel()
    client.realign()

Subscribing to logs
===================

.. code-block:: python

    import ixcom
    
    client = ixcom.Client('192.168.1.30')
    client.open_last_free_channel()
    
    def callback(msg, source_device):
        if isinstance(msg.payload, ixcom.messages.INSSOL_Payload):
            print(msg)

    client.add_callback(callback)

    client.add_log_with_rate(ixcom.messages.INSSOL_Payload.message_id, 10)
    