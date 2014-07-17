from django import template
import time
import os

register = template.Library()

@register.simple_tag
def version_date():
    try:
        timestamp = "Updated: " + time.strftime('%m/%d/%Y', time.gmtime(os.path.getmtime('.git')))
    except:
        timestamp = ""
    return timestamp
