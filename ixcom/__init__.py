try:
    from ixcom_internal.parser import Client
except ImportError as e:
    from .parser import Client