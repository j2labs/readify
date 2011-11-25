from dictshield.base import ShieldException
from dictshield.document import Document, EmbeddedDocument
from dictshield.fields import (StringField,
                               BooleanField,
                               URLField,
                               EmailField,
                               LongField,
                               ListField)

from brubeck.timekeeping import MillisecondField
from brubeck.datamosh import OwnedModelMixin, StreamedModelMixin

from brubeck.models import User, UserProfile

# We're going to use ObjectIds for the id fields
from dictshield.fields.mongo import ObjectIdField
from dictshield.document import swap_field 

###
### Override the id fields to be ObjectIdFields
###

User = swap_field(User, ObjectIdField, ['id'])
UserProfile = swap_field(UserProfile, ObjectIdField, ['id', 'owner_id'])


###
### List Models
###
    
class ListItem(Document, OwnedModelMixin, StreamedModelMixin):
    """Bare minimum to have the concept of streamed item.
    """
    # status fields
    liked = BooleanField(default=False)
    deleted = BooleanField(default=False)
    archived = BooleanField(default=False)

    url = URLField(required=True)
    title = StringField(required=True)
    tags = ListField(StringField())

    _private_fields = [
        'owner_id',
    ]
   
    def __unicode__(self):
        return u'%s' % (self.url)

ListItem = swap_field(ListItem, ObjectIdField, ['id', 'owner_id'])
    
  
