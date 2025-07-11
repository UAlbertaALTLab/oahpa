"""
crk_oahpa URL Configuration
"""
from django.conf.urls import include
from django.urls import re_path
from django.contrib import admin
from django.views.static import serve

from .settings import LLL1
import importlib
oahpa_module = importlib.import_module(LLL1+'_oahpa')
sdv = importlib.import_module(LLL1+'_oahpa.drill.views')
scv = importlib.import_module(LLL1+'_oahpa.conf.views')

prefix = oahpa_module.settings.URL_PREFIX
MEDIA_ROOT = oahpa_module.settings.MEDIA_ROOT

admin_url = r'^%s/admin/' % prefix


urlpatterns = [
    re_path(r'^%s/$' % prefix, sdv.index),
    re_path(r'^%s/i18n/' % prefix, include('django.conf.urls.i18n')),
    re_path(r'^%s/' % prefix, include(LLL1+'_oahpa.drill.urls')),
    re_path(r'^%s/courses/' % prefix, include(LLL1+'_oahpa.courses.urls')),
    re_path(r'^%s/dialect/$' % prefix, scv.dialect),
    re_path(r'^%s/media/(?P<path>.*)$' % prefix, serve, {'document_root': MEDIA_ROOT}),
    re_path(r'^admin/', admin.site.urls),
]
