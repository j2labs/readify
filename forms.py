import copy
from dictshield.forms import Form

from models import User


###
### Form Structures
###

style_dict = {
    'div_class': 'forms_row',
    'label_class': 'forms_label',
    'input_class': 'forms_value',
}


### Make some adjustments to Brubeck `User` model
def gen_user_form(**kwargs):
    """A function that handles the details of generating a Form around `User`
    documents.
    """
    # Use `style_dict` as basis for new forms
    as_div_args = copy.copy(style_dict)

    # Add keywords and overwrite `style_dict` keys if necessary
    for kword,value in kwargs.items():
        as_div_args[kword] = value

    
    f = Form(User, blacklist=['is_active'])

    return f.as_div(**as_div_args)

