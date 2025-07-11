from django.urls import re_path

from .views import cookie_login, cookie_logout
from django.views.generic import TemplateView

# Have to rename login/ to standard_login/ so that the cookie login falls back
# to standard login without unlimited redirects.  users who go to login/ and do
# not have the cookie, will be redirected here, users with the cookie will end
# up being logged in.


urlpatterns = [
	re_path(r'^standard_login/$', TemplateView.as_view(template_name="auth/login.html")),
	re_path(r'^logout/$', TemplateView.as_view(template_name="auth/logout.html")),
    re_path(r'^login/$', cookie_login),
	re_path(r'^cookie_logout/$', cookie_logout),
]

from .views import courses_main, instructor_student_detail

urlpatterns += [
    re_path(r'^(?P<cid>\d+)/(?P<uid>\d+)/$', instructor_student_detail),
    re_path(r'^$', courses_main, name="courses_index"),
]
