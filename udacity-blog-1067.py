#!/usr/bin/env python

import webapp2, os, jinja2, re, hmac, random, string

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = 'supersecret'

def hash_str(str):
	return hmac.new(secret, str).hexdigest()

def hash_password(username, password):
	return "%s|%s" % (username, hash_str(password))

def verify_password(username, hashed_password):
	# get username's password hash from database
	users = db.GqlQuery('SELECT * from User WHERE username = :username', username = username)

	if users.get():
		stored_hashed_password = users.get().password;

		val = '%s|%s' % (username, hashed_password)
		print stored_hashed_password

		if val == stored_hashed_password:
			return username


class User(db.Model):
	username = db.StringProperty(required = True)
	password = db.StringProperty(required = True)
	email = db.StringProperty(required = False)

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
		user = self.get_user_logged_in()

		loggedIn = False
		if user:
			loggedIn = True

		self.render('index.html.jinja2', body = body + '.html.jinja2', loggedIn = loggedIn, user = user, **kw)

	def get_user_logged_in(self):
		userhash = self.request.cookies.get('user')

		if userhash:
			userhash = userhash.split('|')

			if len(userhash) > 1:
				username = userhash[0]
				hashed_password = userhash[1]

				return verify_password(username, hashed_password)

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
		username = self.request.get('username')
		password = self.request.get('password')

		if (self.valid_username and
		    self.valid_password):
			
			if verify_password(username, hash_str(password)):
				self.response.headers.add_header('Set-Cookie', 'user=%s; Path=/' % 
			                                 str(hash_password(username, password)))
				self.redirect('/')
			else:
				self.render_blog('/login',
				                 loginError = True,
				                 username = username)

		else:
			if not self.valid_username( username ):
				username_error = 'Invalid username!'
				username = ''
				

			if not self.valid_password( password ):
				password_error = 'Invalid password!'
				password = ''
				verify = ''

			self.render_blog('login', 
			                 username = username,
			                 password = password,
			                 username_error = username_error,
			                 password_error = password_error)


	def valid_username( self, un ):
		USER_RE = re.compile("^[a-zA-Z0-9_-]{3,20}$")
		return USER_RE.match(un)

	def valid_password( self, pw ):
		PASS_RE = re.compile("^.{3,20}$")
		return PASS_RE.match(pw)


class SignupHandler(Handler):

	def get(self):
		self.render_blog('signup')

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		verify = self.request.get('verify')
		email = self.request.get('email')

		if( self.valid_username( username ) and
			self.valid_password( password) and
			verify == password and
			(not email or self.valid_email( email))):

			# store user in database
			user = User(username = username, password = hash_password(username, password), 
			            email = email)
			db.put(user)

			# send cookie to user
			self.response.headers.add_header('Set-Cookie', 'user=%s; Path=/' % 
			                                 str(hash_password(username, password)))

			# redirect to welcome page
			self.redirect('/welcome')

		else:
			# set validation errors
			username_error = ''
			password_error = ''
			verify_error = ''
			email_error = ''

			if not self.valid_username( username ):
				username_error = 'Invalid username!'
				username = ''
				
			if not self.valid_password( password ):
				password_error = 'Invalid password!'
				password = ''
				verify = ''
				
			if not verify == password:
				verify_error = 'Passwords do not match!'
				password = ''
				verify = ''
				
			if email and not self.valid_email( email ):
				email_error = 'Invalid email address!'
				email = ''

			# render signup form with validation errors
			self.render_blog('signup', 
			                 username = username,
			                 password = password,
			                 verify = verify,
			                 email = email,
			                 username_error = username_error,
			                 password_error = password_error,
			                 verify_error = verify_error,
			                 email_error = email_error)

	# verification methods
	def valid_username( self, un ):
		USER_RE = re.compile("^[a-zA-Z0-9_-]{3,20}$")
		return USER_RE.match(un)

	def valid_password( self, pw ):
		PASS_RE = re.compile("^.{3,20}$")
		return PASS_RE.match(pw)

	def valid_email( self, em ):
		EMAIL_RE = re.compile("^[\S]+@[\S]+\.[\S]+$")
		return EMAIL_RE.match(em)

class WelcomeHandler(Handler):

	def get(self):
		user = self.request.cookies.get('user')
		self.render_blog('welcome')

class LogoutHandler(Handler):

	def get(self):
		self.response.headers.add_header('Set-Cookie', 'user=%s; Path=/' % 
			                             '')
		self.redirect('/signup')

class MainJSONHandler(Handler):

	def get(self):
		pass

class PostJSONHandler(Handler):

	def get(self):
		pass

# routes
app = webapp2.WSGIApplication([
    (r'/', MainHandler),
    (r'/signup', SignupHandler),
    (r'/login', LoginHandler),
    (r'/logout', LogoutHandler),
    (r'/welcome', WelcomeHandler),
    (r'/newpost', NewPostHandler),
    (r'/viewpost/(\d+)', ViewPostHandler),
    (r'/.json', MainJSONHandler),
    (r'/viewpost/(\d+).json', PostJSONHandler)
])