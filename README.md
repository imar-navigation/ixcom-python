This library can be used to communicate with iMAR devices speaking the iXCOM protocol.

Example usage:
```python
import ixcom

client = ixcom.Client('192.168.1.30')
client.open_last_free_channel()
client.realign()
```

Alongside this package, some command line tools will be installed in the user's path:
* configdump2txt: Converts a config.dump into a text form
* monitor2xcom: Converts iXCOM frames in a monitor.log into human readable format
* xcom_lookup: Looks for iXCOM devives on the local network
* split_config: Filters certain parameter IDs from a config.dump