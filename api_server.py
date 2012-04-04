#!/usr/bin/env python


from brubeck.request_handling import Brubeck

from readify.handlers import APIListDisplayHandler
from readify.queries import init_db_conn

import logging


###
### Configuration
###

# Instantiate database connection
db_conn = init_db_conn()

# Routing config
handler_tuples = [
    (r'^/', APIListDisplayHandler),
]

# Application config
config = {
    'mongrel2_pair': ('ipc://api_send', 'ipc://api_recv'),
    'handler_tuples': handler_tuples,
    'db_conn': db_conn,
    'cookie_secret': 'OMGSOOOOOSECRET',
    'log_level': logging.DEBUG,
}


# Instantiate app instance
app = Brubeck(**config)
app.run()
