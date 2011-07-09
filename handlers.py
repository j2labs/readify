import sys
import time
import datetime
import logging
import pymongo
import json

from brubeck.models import User
from brubeck.auth import web_authenticated, UserHandlingMixin
from brubeck.request_handling import WebMessageHandler
from brubeck.templating import Jinja2Rendering

from models import ListItem
from queries import (load_user,
                     save_user,
                     load_listitems,
                     save_listitem)
from timekeeping import millis_to_datetime, prettydate
from forms import gen_user_form

import copy


###
### Authentication
###

class BaseHandler(WebMessageHandler, UserHandlingMixin):
    """This Mixin provides a `get_current_user` implementation that
    validates auth against documents in mongodb.
    """
    def prepare(self):
        self.current_time = int(time.time() * 1000)

    def get_current_user(self):
        """Attempts to load user information from cookie. If that
        fails, it looks for credentials as arguments.

        It then attempts auth with the found credentials by checking for that in
        the database.
        """
        user = None
        
        # Try loading credentials from secure cookie
        user_id = self.get_cookie('user_id',
                                  secret=self.application.cookie_secret)

        # If secure cookies yields username, load it
        if user_id:
            user = load_user(self.db_conn, username=user_id)
            return user
        
        # If not, check POST args and attempt load
        else:
            username = self.get_argument('username')
            password = self.get_argument('password')
            if username:
                user = load_user(self.db_conn, username=username)

        if not user or (user and user.username != username):
            logging.error('Auth fail: bad username')
            return
            
        if not user.check_password(password):
            logging.error('Auth fail: bad password')
            return
        
        logging.debug('Access granted for user: %s' % user.username)

        return user


###
### Account Handlers
###

class AccountCreateHandler(BaseHandler, Jinja2Rendering):
    skip_fields = ['date_joined', 'last_login']
    
    def get(self):
        """Offers login form to user
        """
        form_fields = gen_user_form(skip_fields=self.skip_fields)
        return self.render_template('accounts/create.html',
                                    form_fields=form_fields)
    
    def post(self):
        """Attempts to create an account with the credentials provided in the
        post arguments.

        Successful creation logs the user in and sends them to '/'.

        Failure returns the user to the account create screen and tells them
        what went wrong.
        """
        username = self.get_argument('username')
        password = self.get_argument('password')
        email = self.get_argument('email')

        try:
            u = User.create_user(username, password, email)
            u.validate()
            save_user(self.db_conn, u)
        except Exception, e:
            logging.error('Credentials failed')
            logging.error(e)
            form_fields = gen_user_form(skip_fields=self.skip_fields,
                                        values={'username': username,
                                                'email': email})
            return self.render_template('accounts/create.html',
                                        form_fields=form_fields)

        logging.debug('User <%s> created' % (username))
        self.set_cookie('user_id', username,
                        secret=self.application.cookie_secret)

        return self.redirect('/')

    
class AccountLoginHandler(BaseHandler, Jinja2Rendering):
    def get(self):
        """Offers login form to user
        """
        skip_fields=['email', 'date_joined', 'last_login']
        form_fields = gen_user_form(skip_fields=skip_fields)
        return self.render_template('accounts/login.html',
                                    form_fields=form_fields)
    
    @web_authenticated
    def post(self):
        """Checks credentials with decorator and sends user authenticated
        users to the landing page.
        """
        # Set the cookie to expire in five years
        five_years = datetime.timedelta(days=(5 * 365.25))
        expiration = datetime.datetime.utcnow() + five_years
        expires = expiration.strftime("%a, %d-%b-%Y %H:%M:%S UTC")
        
        self.set_cookie('user_id', self.current_user.username,
                        secret=self.application.cookie_secret,
                        expires=expires)
        
        return self.redirect('/')


class AccountLogoutHandler(BaseHandler, Jinja2Rendering):
    def get(self):
        """Clears cookie and sends user to login page
        """
        self.delete_cookies()
        return self.redirect('/login')


###
### Application Handlers
###

### Web Handlers

class ListDisplayHandler(BaseHandler, Jinja2Rendering):
    """A link listserv (what?!)
    """
    @web_authenticated
    def get(self):
        """Renders a template with our links listed
        """
        items_qs = load_listitems(self.db_conn, self.current_user._id)
        items_qs.sort('updated_at', direction=pymongo.DESCENDING)

        items = []
        for i in items_qs:
            updated = millis_to_datetime(i['updated_at'])
            formatted_date = prettydate(updated)
            item = {
                'formatted_date': formatted_date,
                'url': i.get('url', None),
                'title': i.get('title', None),
                'tags': i.get('tags', None),
            }
            items.append(item)

        context = {
            'links': items,
        }
        return self.render_template('linklists/link_list.html', **context)


class ListAddHandler(BaseHandler, Jinja2Rendering):
    """A link listserv (what?!)
    """
    @web_authenticated
    def get(self):
        """Renders a template with our links listed
        """
        url = self.get_argument('url')
        title = self.get_argument('title')
        context = {}
        if url is not None:
            context['url'] = url
        if title is not None:
            context['title'] = title
        return self.render_template('linklists/item_add.html', **context)

    @web_authenticated
    def post(self):
        """Accepts a URL argument and saves it to the database
        """
        title = self.get_argument('title')
        url = self.get_argument('url')
        tags = self.get_argument('tags')

        if not url.startswith('http'):
            url = 'http://%s' % (url)

        link_item = {
            'owner': self.current_user._id,
            'username': self.current_user.username,
            'created_at': self.current_time,
            'updated_at': self.current_time,

            'title': title,
            'url': url,
        }

        if tags:
            tag_list = tags.split(',')
            link_item['tags'] = tag_list
            
        item = ListItem(**link_item)
        try:
            item.validate()
        except Exception, e:
            logging.error('Item validatiom failed')
            logging.error(e)
            return self.render_error(500)
        
        save_listitem(self.db_conn, item)
        return self.redirect('/')


### API Handler

class APIListDisplayHandler(BaseHandler):
    """A link listserv (what?!)
    """
    @web_authenticated
    def get(self):
        """Renders a template with our links listed
        """
        items_qs = load_listitems(self.db_conn, self.current_user._id)
        items_qs.sort('updated_at', direction=pymongo.DESCENDING)
        num_items = items_qs.count()
        
        items = [ListItem.make_ownersafe(i) for i in items_qs]

        data = {
            'num_items': num_items,
            'items': items,
        }

        self.set_body(json.dumps(data))
        return self.render(status_code=200)
    
    @web_authenticated
    def post(self):
        """Renders a template with our links listed
        """
        return self.get()

