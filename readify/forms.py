import copy
from dictshield.forms import Form

from models import (User,
                    UserProfile,
                    ListItem)


###
### HTML Mappings
###

style_dict = {
    'div_class': 'forms_row',
    'label_class': 'forms_label',
    'input_class': 'forms_value',
}


def gen_doc_as_div(model, private_fields=None, **kwargs):
    """A function that handles the details of generating a Form around some
    document model.
    """
    # Use `style_dict` as basis for new forms
    as_div_args = copy.copy(style_dict)

    # Add keywords and overwrite `style_dict` keys if necessary
    for kword,value in kwargs.items():
        as_div_args[kword] = value

    f = Form(model, private_fields=private_fields)

    return f.as_div(**as_div_args)


###
### User Forms
###

def user_form(**kwargs):
    """A function that handles the details of generating a Form around `User`
    documents.
    """
    return gen_doc_as_div(User, private_fields=['is_active'], **kwargs)


def userprofile_form(**kwargs):
    """A function that handles the details of generating a Form around `User`
    documents.
    """
    return gen_doc_as_div(UserProfile, **kwargs)

###
### ListItem Forms
###

def listitem_form(**kwargs):
    """Listitem forms! Party time! Excellent!
    """
    # Tags must be joined back into a comma-delimited string
    if 'values' in kwargs and kwargs['values'] and 'tags' in kwargs['values']:
        kwargs['values']['tags'] = ','.join(kwargs['values']['tags'])

    return gen_doc_as_div(ListItem, **kwargs)

