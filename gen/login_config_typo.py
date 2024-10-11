Here's a concise Python script to dump login configuration for debugging:

```python
import os
import json
import getpass
import socket
import platform

def dump_login_config():
    config = {
        "user": os.getlogin(),
        "home": os.path.expanduser("~"),
        "current_dir": os.getcwd(),
        "env_vars": dict(os.environ),
        "effective_user": getpass.getuser(),
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "platform": platform.platform(),
        "python_version": platform.python_version()
    }

    print(json.dumps(config, indent=2))

if __name__ == "__main__":
    dump_login_config()
