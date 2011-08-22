#!/usr/bin/env python


from brubeck.request_handling import Brubeck
from brubeck.templating import load_jinja2_env

from handlers import (AccountLoginHandler,
                      AccountCreateHandler,
                      AccountLogoutHandler,
                      DashboardDisplayHandler,
                      LikedDisplayHandler,
                      ArchivedDisplayHandler,
                      ListAddHandler,
                      APIListDisplayHandler,
                      SettingsHandler,
                      ProfilesHandler)

from queries import init_db_conn

import logging


###
### Configuration
###

# Instantiate database connection
db_conn = init_db_conn()

# Routing config
handler_tuples = [
    (r'^/login', AccountLoginHandler),
    (r'^/create', AccountCreateHandler),
    (r'^/logout', AccountLogoutHandler),
    (r'^/add_item', ItemAddHandler),
    (r'^/edit_item', ItemEditHandler),
    (r'^/api', APIListDisplayHandler),
    (r'^/settings', SettingsHandler),
    (r'^/archived', ArchivedDisplayHandler),
    (r'^/liked', LikedDisplayHandler),
    (r'^/(?P<username>\w+)', ProfilesHandler),
    (r'^/$', DashboardDisplayHandler),
]

# Application config
config = {
    'mongrel2_pair': ('ipc://127.0.0.1:9999', 'ipc://127.0.0.1:9998'),
    'handler_tuples': handler_tuples,
    'template_loader': load_jinja2_env('./templates'),
    'db_conn': db_conn,
    'login_url': '/login',
    'cookie_secret': 'OMGSOOOOOSECRET',
    'log_level': logging.DEBUG,
}


# Instantiate app instance
app = Brubeck(**config)
app.run()
