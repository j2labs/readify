from dictshield.base import BaseField, DictPunch
from dictshield.document import Document, EmbeddedDocument
from dictshield.fields import (StringField,
                               BooleanField,
                               URLField,
                               EmailField,
                               LongField,
                               ListField,
                               ObjectIdField)

from brubeck.timekeeping import MillisecondField
from brubeck.datamosh import OwnedModelMixin, StreamedModelMixin


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
