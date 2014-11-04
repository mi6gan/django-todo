#!/usr/bin/env python

from distutils.core import setup

setup(name='django-todo',
      version='0.1',
      description='Simple projects management application with tasks, comments and files attachment features.',
      author='Michael Boyarov',
      author_email='mi666gan@gmail.com',
      url='https://github.com/mi6gan/django-todo',
      packages=['todo'],
      package_data={'todo':[	"templates/*.html",
				"templates/registration/*.html",
				"templates/todo/*.html",
				"static/less/*.less",
				"static/less/mixins/*.less",
				"static/js/*.js",	
				"static/bootstrap-3.2.0/js/*.js",
				"static/bootstrap-3.2.0/less/*.less",
				"static/bootstrap-3.2.0/fonts/*"	]},
      requires=['django_filters','compressor','taggit_bootstrap']
     )
