from django import forms
from .models import Task,Project,TaskComment
from ckeditor.widgets import CKEditorWidget
import django.contrib.comments
import django_filters
import taggit
import taggit_bootstrap
from django.forms.models import model_to_dict
from copy import copy

user_label_from_instance = lambda obj: "%s" % obj.get_full_name() or obj.username

class TodoBaseForm(forms.Form):
	class Media:
        	css = { 'all': ('chosen/chosen.min.css','datepicker/css/datepicker3.css') }
	        js = ('chosen/chosen.jquery.min.js','datepicker/js/bootstrap-datepicker.js','datepicker/js/locales/bootstrap-datepicker.ru.js')
	def __init__(self, *args, **kwargs):
		super(TodoBaseForm, self).__init__(*args, **kwargs)
		for field in self.fields:
			self.fields[field].widget.attrs['class'] = 'form-control'

class TodoModelForm(TodoBaseForm,forms.ModelForm): pass

class TaskModelForm(TodoModelForm):
	title = forms.CharField(widget=forms.TextInput)
	info = forms.CharField(widget=CKEditorWidget())
	class Meta:
		model=Task
		exclude = ['author','status']
		widgets = {
			'tags': taggit_bootstrap.TagsInput() 
		}
	def __init__(self, user, *args, **kwargs):
		super(TaskModelForm, self).__init__(*args, **kwargs)
		assigned_to = self.fields['assigned_to']
		assigned_to.widget.attrs['data-placeholder']=' '
		assigned_to.label_from_instance = user_label_from_instance
		assigned_to.queryset = assigned_to.queryset.exclude(id=user.id) 
		self.fields['project'].queryset=Project.objects.available_for(user)

class TaskStatusForm(forms.ModelForm):
	class Meta:
		model=Task
		fields = ['status']

class ProjectModelForm(TodoModelForm):
	title = forms.CharField(widget=forms.TextInput)
	info = forms.CharField(widget=CKEditorWidget())
	class Meta:
		model=Project
		exclude = ('author',)
	def __init__(self, user, *args, **kwargs):
		super(ProjectModelForm, self).__init__(*args, **kwargs)
		users = self.fields['users']
		users.widget.attrs['data-placeholder']=' '
		#users.queryset = users.queryset.exclude(id=user.id) 
		users.label_from_instance = user_label_from_instance

class TaskFilter(django_filters.FilterSet):
	title = django_filters.CharFilter(lookup_type="icontains")
	tags = django_filters.CharFilter(widget=taggit_bootstrap.TagsInput(),
					 action=lambda q,v: q if not v else q.filter(tags__name__in=v.split(",")))
	class Meta:
		form = TodoBaseForm
		model = Task
		tags = django_filters.CharFilter()
		fields = ('author','assigned_to','status','priority','tags','title','project')
		order_by = ('author','assigned_to','status','priority','title','project','created_at','deadline',
			    '-author','-assigned_to','-status','-priority','-title','-project','-created_at','-deadline')
	def __init__(self, user, *args, **kwargs):
		super(TaskFilter, self).__init__(*args, **kwargs)
		assigned_to = self.form.fields['assigned_to']
		assigned_to.widget.attrs['data-placeholder'] = ' '
		assigned_to.label_from_instance = user_label_from_instance
		self.form.fields['project'].widget.attrs['form'] = 'filterForm'
		self.form.fields['project'].queryset=Project.objects.available_for(user)
		self.form.fields['author'].queryset=self.form.fields['author'].queryset.exclude(id=-1)
		self.form.fields['author'].label_from_instance = user_label_from_instance
		self.form.fields['o'].widget=forms.HiddenInput()

class TaskCommentForm(forms.ModelForm):
	class Meta:	
		model = TaskComment
		exclude = ('author',)
	def __init__(self, *args, **kwargs):
		super(TaskCommentForm,self).__init__(*args, **kwargs)
		self.fields['content'].widget=CKEditorWidget()
		self.fields['task'].widget=forms.HiddenInput()

