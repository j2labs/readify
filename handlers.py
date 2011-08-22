import sys
import time
import datetime
import logging
import pymongo
import json
import copy
from hashlib import md5

from brubeck.models import User, UserProfile
from brubeck.auth import web_authenticated, UserHandlingMixin
from brubeck.request_handling import WebMessageHandler
from brubeck.templating import Jinja2Rendering
from brubeck.timekeeping import millis_to_datetime, prettydate

from models import ListItem
from queries import (load_user,
                     save_user,
                     load_listitems,
                     save_listitem,
                     update_listitem,
                     load_userprofile,
                     save_userprofile)
from forms import (user_form,
                   userprofile_form,
                   listitem_form)


###
### Handler Infrastructure
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

    def get_current_userprofile(self):
        """Attempts to load the userprofile associated with `self.current_user`.
        If no profile is found it prepares a blank one.
        """
        userprofile_dict = load_userprofile(self.db_conn,
                                            uid=self.current_user.id)

        if userprofile_dict:
            userprofile = UserProfile(**userprofile_dict)
        else:
            up_dict = {
                'owner': self.current_user.id,
                'username': self.current_user.username,
                'created_at': self.current_time,
                'updated_at': self.current_time,
            }
            userprofile = UserProfile(**up_dict)

        return userprofile


###
### Account Handlers
###

class AccountCreateHandler(BaseHandler, Jinja2Rendering):
    skip_fields = ['date_joined', 'last_login']
    
    def get(self):
        """Offers login form to user
        """
        form_fields = user_form(skip_fields=self.skip_fields)
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

        try:
            u = User.create_user(username, password)
            u.validate()
            save_user(self.db_conn, u)
        except Exception, e:
            logging.error('Credentials failed')
            logging.error(e)
            form_fields = user_form(skip_fields=self.skip_fields,
                                    values={'username': username})
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
        skip_fields=['date_joined', 'last_login']
        form_fields = user_form(skip_fields=skip_fields)
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
        return self.redirect(self.application.login_url)


###
### List Handlers
###

class ListHandlerBase(BaseHandler, Jinja2Rendering):
    """Base handler for list handlers that provides some commonly needed
    functions.
    """
    def handle_updates(self):
        """I'm not a huge fan of how this works yet. Got any ideas?
        """
        archive = self.get_argument('archive', None)
        unarchive = self.get_argument('unarchive', None)
        like = self.get_argument('like', None)
        unlike = self.get_argument('unlike', None)
        delete = self.get_argument('delete', None)
        undelete = self.get_argument('undelete', None)

        # Simple closure to simplify updating code
        def updater(item_id, **kw):
            update_listitem(self.db_conn, self.current_user.id, item_id, **kw)

        # This could def be cleaner
        if archive: updater(archive, archived=True)
        elif unarchive: updater(unarchive, archived=False)
        elif like: updater(like, liked=True)
        elif unlike: updater(unlike, liked=False)
        elif delete: updater(delete, deleted=True)
        elif undelete: updater(undelete, deleted=False)

    def get_tags(self):
        """
        """
        # There might be multiple tags, so use `get_arguments`
        tags = self.get_arguments('tag', None)
        return tags

    @classmethod
    def prepare_items(self, query_set, sort_field='updated_at'):
        query_set.sort(sort_field, direction=pymongo.DESCENDING)

        items = []
        for i in query_set:
            item_id = i['_id']
            item = ListItem.make_ownersafe(i)
            
            updated = millis_to_datetime(item['updated_at'])
            formatted_date = prettydate(updated)
            item['formatted_date'] = formatted_date

            item['id'] = item_id
            items.append(item)

        return items


class DashboardDisplayHandler(ListHandlerBase):
    @web_authenticated
    def get(self):
        """
        """
        self.handle_updates()
        tags = self.get_tags()
        
        items_qs = load_listitems(self.db_conn, owner=self.current_user.id,
                                  tags=tags)
        items = ListHandlerBase.prepare_items(items_qs)

        context = {
            'links': items,
        }
        return self.render_template('linklists/link_list.html', **context)


class ArchivedDisplayHandler(ListHandlerBase):
    @web_authenticated
    def get(self):
        """
        """
        self.handle_updates()
        tags = self.get_tags()
        
        items_qs = load_listitems(self.db_conn, owner=self.current_user.id,
                                  archived=True, tags=tags)
        items = ListHandlerBase.prepare_items(items_qs)
        
        context = {
            'links': items,
        }
        return self.render_template('linklists/link_list.html', **context)


class LikedDisplayHandler(ListHandlerBase):
    @web_authenticated
    def get(self):
        """
        """
        self.handle_updates()
        tags = self.get_tags()
        
        items_qs = load_listitems(self.db_conn, owner=self.current_user.id,
                                  liked=True, archived=None, tags=tags)
        items = ListHandlerBase.prepare_items(items_qs)
        
        context = {
            'links': items,
        }
        return self.render_template('linklists/link_list.html', **context)


###
### Item Handlers
###

class ItemAddHandler(BaseHandler, Jinja2Rendering):
    """
    """
    @web_authenticated
    def get(self):
        """Renders a template with our links listed
        """
        # Check for data to autopopulate fields with
        values = {}
        url = self.get_argument('url')
        title = self.get_argument('title')
        
        if url is not None:
            values['url'] = url
        if title is not None:
            values['title'] = title

        skip_fields = ['deleted', 'archived', 'created_at', 'updated_at',
                       'liked', 'username']
        form_fields = listitem_form(skip_fields=skip_fields, values=values)
        return self.render_template('linklists/item_add.html',
                                    form_fields=form_fields)

    @web_authenticated
    def post(self):
        """Accepts a URL argument and saves it to the database
        """
        title = self.get_argument('title')
        url = self.get_argument('url')
        tags = self.get_argument('tags')

        # TODO The URLField should probably handle this somehow
        if not url.startswith('http'):
            url = 'http://%s' % (url)

        tag_list = tags.split(',')

        link_item = {
            'owner': self.current_user.id,
            'username': self.current_user.username,
            'created_at': self.current_time,
            'updated_at': self.current_time,

            'title': title,
            'url': url,
            'tags': tag_list,
        }

        item = ListItem(**link_item)
        try:
            item.validate()
        except Exception, e:
            logging.error('Item validatiom failed')
            logging.error(e)
            return self.render_error(500)
        
        save_listitem(self.db_conn, item)
        return self.redirect('/')


###
### Settings Handlers
###

class SettingsHandler(BaseHandler, Jinja2Rendering):
    """
    """
    @web_authenticated
    def get(self):
        """
        """
        # Load user's profile, if available.
        up_dict = self.current_userprofile.to_python()

        # Generate profile form elements
        hidden_fields = ['username', 'created_at', 'updated_at']
        form_fields =  userprofile_form(skip_fields=hidden_fields,
                                        values=up_dict)

        context = {
            'form_fields': form_fields,
        }
        return self.render_template('settings/edit.html', **context)

    @web_authenticated
    def post(self):
        """
        """
        new_profile = self.current_userprofile.to_python()

        # Apply each argument we accept to the new structure
        new_profile['name'] = self.get_argument('name', None)
        new_profile['bio'] = self.get_argument('bio', None)
        new_profile['location_text'] = self.get_argument('location_text', None)
        new_profile['avatar_url'] = self.get_argument('avatar_url', None)
        new_profile['email'] = self.get_argument('email', None)

        # Help a user out if they didn't put the "http" in front
        website = self.get_argument('website', None)
        if not website.startswith('http'):
            website = 'http://%s' % (website)
        new_profile['website'] = website

        # Save values if they pass validation
        try:
            new_up = UserProfile(**new_profile)
            new_up.validate()
            save_userprofile(self.db_conn, new_up)
            self._current_userprofile = new_up
        except Exception, e:
            # TODO handle errors nicely
            print e
            return self.get()

        return self.redirect("/" + self.current_user.username)


###
### Profile Handlers
###

class ProfilesHandler(BaseHandler, Jinja2Rendering):
    """
    """
    def get(self, username):
        """
        """
        if username == 'profile':
            up_dict = self.current_userprofile.to_python()
            username = self.current_user.username
        else:
            # Load user's profile, if available.
            up_dict = load_userprofile(self.db_conn, username=username)

        if up_dict and 'email' in up_dict and 'avatar_url' not in up_dict:
            # ad-hoc gravatar support!
            email = up_dict['email']
            email_hash = md5(email).hexdigest()
            avatar_url = 'http://www.gravatar.com/avatar/%s?s=100' % email_hash
            up_dict['avatar_url'] = avatar_url

        user_links = load_listitems(self.db_conn, username=username, archived=None)
        user_links = ListHandlerBase.prepare_items(user_links)

        context = {
            'userprofile': up_dict,
            'links': user_links,
        }

        return self.render_template('profiles/view.html', **context)


###
### List API
###

class APIListDisplayHandler(BaseHandler):
    """
    """
    @web_authenticated
    def get(self):
        """Renders a JSON list of link data
        """
        items_qs = load_listitems(self.db_conn, self.current_user.id)
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
        """Same as `get()`
        """
        return self.get()
