try:
    from ixcom_internal.parser import Client
except ImportError as e:
    print(e)
    from .parser import Client
