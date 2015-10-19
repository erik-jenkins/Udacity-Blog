#!/usr/bin/env python

import webapp2, os, jinja2, re

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

class Post(db.Model):
	subject = db.StringProperty(required = True)
	content = db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)

class Handler(webapp2.RequestHandler):
	
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **kw):
		t = jinja_env.get_template(template)
		return t.render(**kw)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def render_blog(self, body='blog', **kw):
		self.render('index.html.jinja2', body=body, **kw)

class MainHandler(Handler):

	def get(self):
		posts = db.GqlQuery('SELECT * from Post ORDER BY created DESC')

		self.render_blog(posts = posts)
		
class NewPostHandler(Handler):

	def get(self):
		self.render_blog('newpost')

	def post(self):
		subject = self.request.get('subject')
		content = self.request.get('content')

		if subject and content:
			post = Post(subject = subject, content = content)
			post.put()

			self.redirect('/viewpost/%s' % str(post.key().id()))
		else:
			post_error = "Subject AND content, please!"

			self.render_blog('newpost',
			                 subject = subject,
			                 content = content,
			                 post_error = post_error)

class ViewPostHandler(Handler):

	def get(self, post_id):
		post = Post.get_by_id(int(post_id))
		self.render_blog('viewpost', post=post)

class LoginHandler(Handler):

	def get(self):
		self.render_blog('login')

app = webapp2.WSGIApplication([
    (r'/', MainHandler),
    (r'/login', LoginHandler),
    (r'/newpost', NewPostHandler),
    (r'/viewpost/(\d+)', ViewPostHandler)
])