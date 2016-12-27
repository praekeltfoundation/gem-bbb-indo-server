
from django import template
from django.shortcuts import reverse


register = template.Library()


@register.simple_tag(takes_context=True)
def absolute_page_url(context, page):
    request = context['request']
    return request.build_absolute_uri(page.url)


@register.simple_tag(takes_context=True)
def absolute_path(context, path):
    request = context['request']
    return request.build_absolute_uri(path)


@register.simple_tag(takes_context=True)
def absolute_url(context, name, *args, **kwargs):
    request = context['request']
    return request.build_absolute_uri(reverse(name, args=args, kwargs=kwargs))
