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
		self.render('index.html.jinja2', body = body + '.html.jinja2', **kw)

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

	def post(self):
		pass


class SignupHandler(Handler):

	def get(self):
		self.render_blog('signup')

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		verify = self.request.get('verify')
		email = self.request.get('email')

		if( self.verify_username( username ) and
			self.verify_password( password) and
			verify == password and
			(not email or self.verify_email( email))):
			self.redirect('/');

		else:
			username_error = ''
			password_error = ''
			verify_error = ''
			email_error = ''

			if not self.verify_username( username ):
				username_error = 'Invalid username!'
				username = ''
				

			if not self.verify_password( password ):
				password_error = 'Invalid password!'
				password = ''
				verify = ''
				

			if not verify == password:
				verify_error = 'Passwords do not match!'
				password = ''
				verify = ''
				
			if email and not self.verify_email( email ):
				email_error = 'Invalid email address!'
				email = ''

			self.render_blog('signup', 
			                 username = username,
			                 password = password,
			                 verify = verify,
			                 email = email,
			                 username_error = username_error,
			                 password_error = password_error,
			                 verify_error = verify_error,
			                 email_error = email_error)

	def verify_username( self, un ):
		USER_RE = re.compile("^[a-zA-Z0-9_-]{3,20}$")
		return USER_RE.match(un)

	def verify_password( self, pw ):
		PASS_RE = re.compile("^.{3,20}$")
		return PASS_RE.match(pw)

	def verify_email( self, em ):
		EMAIL_RE = re.compile("^[\S]+@[\S]+\.[\S]+$")
		return EMAIL_RE.match(em)

app = webapp2.WSGIApplication([
    (r'/', MainHandler),
    (r'/signup', SignupHandler),
    (r'/login', LoginHandler),
    (r'/newpost', NewPostHandler),
    (r'/viewpost/(\d+)', ViewPostHandler)
])