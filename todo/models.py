from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User

from django.core.urlresolvers import reverse

from taggit.managers import TaggableManager

# Для уведомлений по e-mail
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.contrib.sites.models import Site

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
#---------------------------------------------------
# Генерирует upload path для FileField
def make_upload_path(instance, filename):
	upload_path = "uploads"
	if isinstance(instance, ProjectAttach):
		project_id = instance.project.id
		return "%s/%s/%s" % (upload_path, project_id, filename)

	elif isinstance(instance, TaskAttach):
		project_id = instance.task.project.id
		return "%s/%s/tasks/%s" % (upload_path, project_id, filename)
	else:
		return "%s/attachs/%s" % (upload_path, filename)

# Пользователи в проектах
def users_in_projects(projects):
	users = User.objects.filter(
			Q(avail_projects__in=projects) | Q(is_superuser=True)).distinct().order_by('first_name', 'last_name')
	return users
#---------------------------------------------------
# Тема письма при изменении статуса задачи
TASK_NOTIF_SUBJECTS = {
	0: 'Новая задача "%s"',
	1: 'Задача "%s" открыта заново',
	2: 'Задача "%s" принята на выполнение',
	3: 'Задача "%s" выполнена',
	4: 'Результат выполнения задачи "%s" одобрен',
}

class Action(models.Model):

	class Meta:
		ordering = ['-created_at']

	author = models.ForeignKey(User, related_name="actions")
	content_type = models.ForeignKey(ContentType)
	object_id = models.PositiveIntegerField()
	content_object = GenericForeignKey('content_type', 'object_id')
	created_at = models.DateTimeField(auto_now_add=True)
	info = models.TextField()
	
	def __str__(self):
		return self.info
	

class ProjectManager(models.Manager):
	def available_for(self, user):
		if user.is_superuser:
			return self.all().order_by('title')
		else:
			return user.avail_projects.all().order_by('title')	 

class AbstractProject(models.Model):
	class Meta:
		abstract = True
	title = models.CharField("Название", max_length=255)
	info = models.TextField("Описание")
	created_at = models.DateTimeField("Дата добавления", auto_now_add=True)
	objects = ProjectManager()
	def __str__(self):
		return self.title
	def _get_tasks_count(self):
		return self.related_tasks.count()
	def _get_tasks_count_active(self):
		return self.related_tasks.exclude(status=3).exclude(status=4).count()
	tasks_count = property(_get_tasks_count)
	tasks_active_count = property(_get_tasks_count_active)

	def is_avail(self, user):
		if user.is_superuser:
			return True
		try:
			user.avail_projects.get(pk=self.pk)
			return True
		except Project.DoesNotExist:
			return False

	def allowed_users(self):
		pass

	def save(self, *args, **kwargs):
		super(AbstractProject, self).save()
		self.users.add(self.author)

class Project(AbstractProject):
	author = models.ForeignKey(User, db_column='author', related_name="projects", verbose_name="Автор")
	users = models.ManyToManyField(User, verbose_name="Участники", related_name="avail_projects")
	class Meta:
		verbose_name = "проект"
		verbose_name_plural = "проекты"

	def get_absolute_url(self):
		return reverse('project_detail', args=[str(self.id)])

class Task(models.Model):
	PRIORITY_CHOICES = (
		(None, '-'*9),
		(1, 'Низкий'),
		(50, 'Средний'),
		(100, 'Высокий'),
	)
	STATUS_CHOICES = (
		(None, '-'*9),
		(1, 'Новая'),
		(2, 'Принята'),
		(3, 'Завершена'),
		(4, 'Одобрена'),
	)
	project = models.ForeignKey(Project, verbose_name="Проект", related_name="related_tasks")
	author = models.ForeignKey(User, related_name="tasks", verbose_name="Автор")
	assigned_to = models.ManyToManyField(User, related_name="assigned_tasks", verbose_name="Ответственные")
	created_at = models.DateTimeField("Дата добавления", auto_now_add=True)
	title =  models.CharField("Название", max_length=255)
	info = models.TextField("Описание")  
	status = models.IntegerField("Статус",default=1,choices=STATUS_CHOICES)
	priority = models.IntegerField("Приоритет",choices=PRIORITY_CHOICES)
	deadline = models.DateField("Срок")
	public = models.IntegerField(default=0,choices=((0,"Закрытый"),(1,"Открытый (только чтение)")))
	tags = TaggableManager(blank=True)

	def __str__(self):
		return self.title

	def save(self, *args, **kwargs):
		is_new = self.pk is None
		if is_new:
			status=None
		else:
			try:
				old=Task.objects.get(pk=self.pk)
				status = old.status
			except Task.DoesNotExist:
				status=None
		super(Task, self).save()
		if status!=self.status:
			task_notif_subject=TASK_NOTIF_SUBJECTS[0 if is_new else self.status] % self.title
			host = Site.objects.get_current().domain
			action_info = "%s: %s" % (task_notif_subject, self.title)
			subject = "[%s] %s" % ( host, task_notif_subject )
			message = render_to_string('todo/mail/task.html',{'task':self, 'host': host })
			if self.status in (0,1,4):
				rcpnts = self.assigned_to.all()
			elif self.status in (2,3):
				rcpnts = [self.author]
			send_mail(subject.replace("\r\n"," "), 
				strip_tags(message), 
				settings.__dict__.get('TODO_FROM_EMAIL') or 'info', 
				[ u.email for u in set(rcpnts) ], html_message=message )

	def get_absolute_url(self):
		return reverse('task_detail', args=[str(self.id)])

class CommonAttach(models.Model):
	author = models.ForeignKey(User)
	created_at = models.DateTimeField(auto_now_add=True)
	attached_file = models.FileField(upload_to=make_upload_path,max_length=1024)
	class Meta:
		abstract=True

class ProjectAttach(CommonAttach):
	project = models.ForeignKey(Project, related_name="files")

	def get_absolute_url(self):
		return reverse('project_detail', args=[str(self.project.pk)])

class TaskAttach(CommonAttach):
	task = models.ForeignKey(Task, related_name="files")

	def get_absolute_url(self):
		return reverse('task_detail', args=[str(self.task.pk)])

class TaskComment(models.Model):
	author = models.ForeignKey(User, related_name="comments", verbose_name="Автор")
	task = models.ForeignKey(Task, related_name="comments")
	content = models.TextField("Комментарий")  
	created_at = models.DateTimeField(auto_now_add=True)
	
	def get_absolute_url(self):
		return reverse('task_detail', args=[str(self.task.pk)])

	def save(self, *args, **kwargs):
		super(TaskComment, self).save()
		host = Site.objects.get_current().domain
		subject = "[%s] %s" % ( host, "Комментарий к задаче" )
		message = render_to_string('todo/mail/comment.html',{'comment':self, 'host': host })
		rcpnts = [ u for u in self.task.assigned_to.all() ]
		send_mail(subject.replace("\r\n"," "), 
			strip_tags(message), 
			settings.__dict__.get('TODO_FROM_EMAIL') or 'info', 
			[ u.email for u in set(rcpnts) ], html_message=message )

