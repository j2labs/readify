from dictshield.base import BaseField, DictPunch
from dictshield.document import Document
from dictshield.fields import (StringField,
                               BooleanField,
                               URLField,
                               EmailField,
                               LongField,
                               ListField,
                               ObjectIdField)

from brubeck.timekeeping import MillisecondField
from brubeck.models import User
from brubeck.models import UserProfile


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
    liked = BooleanField(default=False)
    deleted = BooleanField(default=False)
    archived = BooleanField(default=False)

    url = URLField(required=True)
    title = StringField(required=True)
    tags = ListField(StringField())

    _private_fields = [
        'owner',
    ]
   
    def __unicode__(self):
        return u'%s' % (self.url)
