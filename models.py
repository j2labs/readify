from dictshield.base import BaseField, DictPunch
from dictshield.document import Document
from dictshield.fields import (StringField,
                               BooleanField,
                               URLField,
                               EmailField,
                               LongField,
                               ListField)
# this might get moved
from dictshield.fields import ObjectIdField

from timekeeping import MillisecondField


###
### Social Models
###

from brubeck.models import User
from brubeck.models import UserProfile



class UserProfile(Document):
    """A UserProfile is essentially any publicly available info about the user.
    Stored in a document separate from the User itself for security.
    """
    # ownable
    owner = ObjectIdField(required=True)
    username = StringField(max_length=30, required=True)

    # streamable
    created_at = MillisecondField()
    updated_at = MillisecondField()

    # unique fields
    name = StringField(max_length=100)
    location = StringField(max_length=100)
    website = URLField()

    _private_fields = [
        'owner',
    ]

    def __unicode__(self):
        return u'%s' % (self.username)


###
### List Models
###
    
class ListItem(Document):
    """Bare minimum to have the concept of streamed item.
    """
    # ownable
    owner = ObjectIdField(required=True)
    username = StringField(max_length=30, required=True)

    # streamable
    created_at = MillisecondField()
    updated_at = MillisecondField()

    # status fields
    deleted = BooleanField()
    archived = BooleanField()

    url = URLField(required=True)
    title = StringField(required=True)
    tags = ListField(StringField())

    _private_fields = [
        'owner',
    ]
   
    def __unicode__(self):
        return u'%s' % (self.url)
