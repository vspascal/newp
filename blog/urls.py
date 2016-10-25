from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views
from .views import IndexView, UserControlView, WriteBlogView, UserView, BlogView, DeleteCommentView, NewsView, \
    DetailNewsView

app_name = 'blog'
urlpatterns = [

    url(r'index', IndexView.as_view(), name='index'),

    url(r'^auth/login/$', auth_views.login, {'template_name': 'blog/login.html'}),

    url(r'^user/(?P<slug>\w+)$', UserControlView.as_view(), name='usercontrol'),

    url(r'^news$', NewsView.as_view(), name='news'),

    url(r'^news/(?P<slug>\w+)$', DetailNewsView.as_view(), name='detailnews'),

    url(r'^(?P<u_id>[0-9]+)/(?P<slug>\w+)$', UserView.as_view(), name='user'),

    url(r'^blog/write', WriteBlogView.as_view(), name='writeblog'),

    url(r'^blog/(?P<b_id>[0-9]+)/(?P<slug>\w+)$', BlogView.as_view(), name='blog'),

    url(r'^comment/(?P<c_id>[0-9]+)/delete', DeleteCommentView.as_view(), name='comment'),
]
