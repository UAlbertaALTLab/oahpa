from django.urls import re_path

urlpatterns = [
    re_path(r"^lookup/$", "views.error_feedback_view"),
    re_path(r"^test_page/$", "views.test_page"),
]

# vim: set ts=4 sw=4 tw=72 syntax=python :
