
from django import template


register = template.Library()


@register.simple_tag(takes_context=True)
def absolute_page_url(context, page):
    request = context['request']
    return request.build_absolute_uri(page.url)

@register.simple_tag(takes_context=True)
def absolute_url(context, path):
    request = context['request']
    return request.build_absolute_uri(path)
