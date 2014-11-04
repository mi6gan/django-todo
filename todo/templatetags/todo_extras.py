# -*- coding: utf-8 -*-
from datetime import datetime, date,timedelta
import re

from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django import template

from todo.models import Task

from django.template.defaultfilters import stringfilter
import os

register = template.Library()

@register.filter(name='basename')
@stringfilter
def basename(value):
    return os.path.basename(value)

@register.filter
def size_kb(attached_file):
    try:
        size = attached_file.size
        import math
        return "%s Кб" % (int(math.ceil(float(size)/1024)))
    except:
        return 'размер неизвестен'

