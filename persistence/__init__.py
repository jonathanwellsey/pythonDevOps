import os

if os.environ.get("MYSQL_HOST"):
    from .mysql_db import *  # noqa: F401,F403
else:
    from .sqlite_db import *  # noqa: F401,F403
