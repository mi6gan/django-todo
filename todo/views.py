from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import ModelFormMixin
from django_filters.views import FilterView
from django.core.urlresolvers import reverse_lazy
from django.http import Http404
from django.contrib.auth.decorators import login_required,permission_required
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied

from .models import * 

from .forms import TaskModelForm, TaskStatusForm, ProjectModelForm, TaskFilter, TaskCommentForm

# Base views
class LoginRequiredMixin(ContextMixin):
	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)

class TasksProjectsFormMixin(ModelFormMixin):
	def form_valid(self,form):
		o=form.save(commit=False)
		o.author=self.request.user
		o.save()
		form.save_m2m()
		return super(TasksProjectsFormMixin,self).form_valid(form)

# Task views
class TasksMixin(ContextMixin):
	menu_active="tasks"
	model=Task

class TaskListView(TasksMixin,LoginRequiredMixin,FilterView):
	template_name_suffix = '_list'
	filterset_class = TaskFilter
	paginate_by = 20

	def get_filterset_kwargs(self, filterset_class):
		kwargs=super(TaskListView,self).get_filterset_kwargs(filterset_class)
		kwargs.update({'user':self.request.user})
		return kwargs

	def get_queryset(self):
		queryset=super(TaskListView,self).get_queryset()
		user=self.request.user
		if not user.is_superuser:
			queryset=queryset.filter(project__users=user)
		return queryset

class TaskCreateView(TasksMixin,TasksProjectsFormMixin,CreateView):
	form_class=TaskModelForm

	def get_form_kwargs(self):
		kwargs=super(TaskCreateView,self).get_form_kwargs()
		kwargs.update({'user':self.request.user})
		return kwargs

	@method_decorator(permission_required('todo.add_task',raise_exception=True))
	def dispatch(self, *args, **kwargs):
		response=super(TaskCreateView, self).dispatch(*args, **kwargs)
		task=self.__dict__.get('object')
		if task:
			action_info='Создана задача "%s"' % task.title
			Action(content_object=task,info=action_info,author=self.request.user).save()
		return response

class TaskEditView(TasksMixin,LoginRequiredMixin,TasksProjectsFormMixin,UpdateView):
	form_class=TaskModelForm

	def get_form_kwargs(self):
		kwargs=super(TaskEditView,self).get_form_kwargs()
		kwargs.update({'user':self.request.user})
		return kwargs

	def dispatch(self, *args, **kwargs):
		user=self.request.user
		if not user.is_superuser and not user==self.get_object().author:
			raise PermissionDenied
		return super(TaskEditView, self).dispatch(*args, **kwargs)
    	
class TaskDeleteView(TasksMixin,LoginRequiredMixin,DeleteView):
	success_url=reverse_lazy('task_list')

	def dispatch(self, *args, **kwargs):
		user=self.request.user
		if not user.is_superuser and not user==self.get_object().author:
			raise PermissionDenied
		return super(TaskDeleteView, self).dispatch(*args, **kwargs)

class TaskDetailView(TasksMixin,DetailView):

	def get_context_data(self, **kwargs):
		user=self.request.user
		task=self.get_object()
		if  user.is_superuser or user.has_perm("todo.add_taskcomment") and (user==task.author or user in task.assigned_to.all()):
			context={'comment_form':TaskCommentForm(initial={"task":self.object})}
		else: context={}
		context.update(kwargs)
		return super(TaskDetailView, self).get_context_data(**context)

	def dispatch(self, *args, **kwargs):
		user=self.request.user
		task=self.get_object()
		if not user.is_superuser and not (user==task.author or user in task.assigned_to.all()) and task.public==0:
			raise PermissionDenied
		return super(TaskDetailView, self).dispatch(*args, **kwargs)

class TaskStatusView(UpdateView,LoginRequiredMixin):
	model=Task
	form_class=TaskStatusForm

	def dispatch(self, *args, **kwargs):
		user=self.request.user
		status=int(self.request.POST.get('status') or 0)
		task=self.get_object()
		if not user.is_superuser: 
			if status in (1,4) and not user==task.author:
				raise PermissionDenied
			elif status in (2,3) and not user in task.assigned_to:
				raise PermissionDenied
		response = super(TaskStatusView, self).dispatch(*args, **kwargs)
		action_info= TASK_NOTIF_SUBJECTS[status] % task.title
		Action(content_object=task,info=action_info,author=self.request.user).save()
		return response
    	
class TaskAttachCreateView(CreateView,LoginRequiredMixin): 
	model=TaskAttach

	def dispatch(self, *args, **kwargs):
		user=self.request.user
		task=Task.objects.get(id=self.request.POST.get('task'))
		if not user.is_superuser and not (user==task.author or user in task.assigned_to.all()):
			raise PermissionDenied
		return super(TaskAttachCreateView, self).dispatch(*args, **kwargs)
    	
class TaskAttachDeleteView(DeleteView,LoginRequiredMixin):
	model=TaskAttach
	success_url="/tasks/%(task_id)s"

	def dispatch(self, *args, **kwargs):
		user=self.request.user
		task=self.get_object().task
		if not user.is_superuser and not (user==task.author or user in task.assigned_to.all()):
			raise PermissionDenied
		return super(TaskAttachDeleteView, self).dispatch(*args, **kwargs)

# Project views
class ProjectsMixin(ContextMixin):
	model=Project
	menu_active="projects"

class ProjectListView(ProjectsMixin,LoginRequiredMixin,ListView):

	def get_queryset(self):
		queryset=super(ProjectListView,self).get_queryset()
		user=self.request.user
		if not user.is_superuser:
			queryset=queryset.filter(author=user)|queryset.filter(users=user)
		return queryset

class ProjectCreateView(ProjectsMixin,TasksProjectsFormMixin,CreateView):
	form_class=ProjectModelForm

	def get_form_kwargs(self):
		kwargs=super(ProjectCreateView,self).get_form_kwargs()
		kwargs.update({'user':self.request.user})
		return kwargs

	@method_decorator(permission_required('todo.add_project',raise_exception=True))
	def dispatch(self, *args, **kwargs):
        	return super(ProjectCreateView, self).dispatch(*args, **kwargs)

class ProjectEditView(ProjectsMixin,TasksProjectsFormMixin,UpdateView):
	form_class=ProjectModelForm

	def get_form_kwargs(self):
		kwargs=super(ProjectEditView,self).get_form_kwargs()
		kwargs.update({'user':self.request.user})
		return kwargs

	def dispatch(self, *args, **kwargs):
		user=self.request.user
		if not user.is_superuser and not user==self.get_object().author:
			raise PermissionDenied
		return super(ProjectEditView, self).dispatch(*args, **kwargs)

class ProjectDeleteView(ProjectsMixin,DeleteView):
	success_url=reverse_lazy('project_list')

	def dispatch(self, *args, **kwargs):
		user=self.request.user
		if not user.is_superuser and not user==self.get_object().author:
			raise PermissionDenied
		return super(ProjectDeleteView, self).dispatch(*args, **kwargs)
		
class ProjectDetailView(ProjectsMixin,LoginRequiredMixin,DetailView):
	def dispatch(self, *args, **kwargs):
		user=self.request.user
		project=self.get_object()
		if not user.is_superuser and not (user==project.author or user in project.users.all()):
			raise PermissionDenied
		return super(ProjectDetailView, self).dispatch(*args, **kwargs)

class ProjectAttachCreateView(CreateView): 
	model=ProjectAttach

	def dispatch(self, *args, **kwargs):
		user=self.request.user
		project=Project.objects.get(id=self.request.POST.get('project'))
		if not user.is_superuser and not (user==project.author or user in project.users.all()):
			raise PermissionDenied
		return super(ProjectAttachCreateView, self).dispatch(*args, **kwargs)

class ProjectAttachDeleteView(DeleteView):
	model=ProjectAttach
	success_url="/projects/%(project_id)s"

	def dispatch(self, *args, **kwargs):
		user=self.request.user
		project=self.get_object().project
		if not user.is_superuser and not (user==project.author or user in project.assigned_to.all()):
			raise PermissionDenied
		return super(ProjectAttachDeleteView, self).dispatch(*args, **kwargs)

# Comments views
class TaskCommentCreateView(TasksMixin,TasksProjectsFormMixin,LoginRequiredMixin,CreateView):
	model=TaskComment
	form_class=TaskCommentForm

	@method_decorator(permission_required('todo.add_taskcomment',raise_exception=True))
	def dispatch(self, *args, **kwargs):
		task=Task.objects.get(id=self.request.POST.get('task'))
		user=self.request.user
		if not user.is_superuser and not (user==task.author or user in task.assigned_to.all()):
			raise PermissionDenied
		response = super(TaskCommentCreateView, self).dispatch(*args, **kwargs)
		comment=self.__dict__.get('object')
		if comment:
			action_info='Создан комментарий к задаче "%s"' % task.title
			Action(content_object=self.object,info=action_info,author=self.request.user).save()
		return response

class TaskCommentDeleteView(TasksMixin,LoginRequiredMixin,DeleteView):
	model=TaskComment
	success_url="/tasks/%(task_id)s"

	def dispatch(self, *args, **kwargs):
		user=self.request.user
		if not user.is_superuser and not user==self.get_object().author:
			raise PermissionDenied
		return super(TaskCommentDeleteView, self).dispatch(*args, **kwargs)

class ActionListView(LoginRequiredMixin, ListView):
	menu_active = 'actions'
	model = Action
	def dispatch(self, *args, **kwargs):
		if not self.request.user.is_superuser: PermissionDenied
		return super(ActionListView, self).dispatch(*args, **kwargs)

