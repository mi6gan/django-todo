from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse_lazy

from django.views.generic.base import RedirectView

from .views import *

from django.contrib import admin



urlpatterns = patterns('',
	url(r'^$',RedirectView.as_view(url='/tasks/')),
	url(r'^admin/', include(admin.site.urls)),
    	url(r'^login/$', 'django.contrib.auth.views.login'),
    	url(r'^logout/$', 'django.contrib.auth.views.logout_then_login'),
    	url(r'^tasks/$', TaskListView.as_view(), name='task_list'),
    	url(r'^tasks/new$', TaskCreateView.as_view(), name='task_create'),
    	url(r'^tasks/edit/(?P<pk>\d+)$', TaskEditView.as_view(), name='task_edit'),
    	url(r'^tasks/status/(?P<pk>\d+)$', TaskStatusView.as_view(), name='task_status'),
    	url(r'^tasks/delete/(?P<pk>\d+)$', TaskDeleteView.as_view(), name='task_delete'),
    	url(r'^tasks/(?P<pk>\d+)$', TaskDetailView.as_view(), name='task_detail'),
    	url(r'^tasks/attach/new$', TaskAttachCreateView.as_view(), name='task_attach_create'),
    	url(r'^tasks/attach/delete/(?P<pk>\d+)$', TaskAttachDeleteView.as_view(), name='task_attach_delete'),
	url(r'^tasks/comments/new$', TaskCommentCreateView.as_view(), name='task_comment_create'),
    	url(r'^tasks/comments/delete/(?P<pk>\d+)/$',TaskCommentDeleteView.as_view(),name='task_comment_delete'),
    	url(r'^projects/$', ProjectListView.as_view(), name='project_list'),
    	url(r'^projects/new$', ProjectCreateView.as_view(), name='project_create'),
    	url(r'^projects/edit/(?P<pk>\d+)$', ProjectEditView.as_view(), name='project_edit'),
    	url(r'^projects/delete/(?P<pk>\d+)$', ProjectDeleteView.as_view(), name='project_delete'),
    	url(r'^projects/(?P<pk>\d+)$', ProjectDetailView.as_view(),name='project_detail'),
    	url(r'^projects/attach/new$', ProjectAttachCreateView.as_view(), name='project_attach_create'),
    	url(r'^projects/attach/delete/(?P<pk>\d+)$', ProjectAttachDeleteView.as_view(), name='project_attach_delete'),
    	url(r'^actions/$', ActionListView.as_view(), name='action_list'),
    	url(r'^ckeditor/', include('ckeditor.urls')),
    	url(r'^taggit/', include('taggit_bootstrap.urls')),
)

