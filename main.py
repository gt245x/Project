import os
import jinja2
import webapp2
import re
from string import letters
from google.appengine.ext import db
from handler import *

template_dir = os.path.join(os.path.dirname(__file__),'templates').replace("\\","/")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)




class MainPage(BlogHandler):
    def get(self):
        self.write("Welcome to Project multi user blog")

class Signup(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify_password')
        self.email = self.request.get('email')

        params = dict(username = self.username, email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True

        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.redirect('/welcome?username=' + self.username)

class Welcome(BlogHandler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            self.render('welcome.html', username = username)
        else:
            self.redirect('/signup')


class Register(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify_password')
        self.email = self.request.get('email')

        params = dict(username = self.username, email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True

        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            u = User.by_name(self.username) #
            if u:
                msg = 'That user already exists.'
                self.render('signup-form.html', username = self.username, error_username = msg)
            else:
                u = User.register(self.username, self.password, self.email)
                u.put()

                self.login_set_cookie(u)
                self.redirect('/blog')


class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    blog_author = db.StringProperty(required = True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

class BlogFront(BlogHandler):
    def get(self):
        posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC LIMIT 10")
        if self.user:
            self.render('front.html', posts = posts)
        else:
            self.redirect('/login')

# def blog_key(name = 'default'):
#     return db.Key.from_path('blogs', name)

class PostPage(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent = blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return
        self.render("permalink.html", post = post)




class NewPost(BlogHandler):
    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect('/login')

    def post(self):
        if not self.user:
            self.redirect('/blog')

        subject = self.request.get("subject")
        content = self.request.get("content")
        blog_author = self.request.get("blog_author")

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content, blog_author = blog_author)
            p.put()
            self.redirect('/blog/%s' % str(p.key().id()))
        else:
            error = "subject and content, please!!!!!"
            self.render("newpost.html", subject = subject, content = content, error = error)

class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        self.username = self.request.get('username')
        self.password = self.request.get('password')

        u = User.login(self.username, self.password)
        if u:
            self.login_set_cookie(u)
            self.redirect('/blog')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', username = self.username, error = msg)

class Logout(BlogHandler):
    def get(self):
        self.logout_cookie()
        self.redirect('/blog')


class EditPost(BlogHandler):
    def post(self, post_id):
        if self.user:
            key = db.Key.from_path('Post', int(post_id), parent = blog_key())
            post = db.get(key)

            if self.user.name == post.blog_author::
                self.render('newpost.html',
                            subject = post.subject,
                            content = post.content,
                            )
            else:
                message = ("You can only edit a post created by you")
                self.render



class DeletePost(BlogHandler):
    def get(self, post_id):
        if self.user:
            key = db.Key.from_path('Post', int(post_id), parent = blog_key())
            post = db.get(key)
            if self.user.name == post.blog_author:
                #if self.user.name.key().id() == post.blog_author.key().id(): does not work
                post.delete()
                message = "The selected post was successfully deleted"
                self.render('confirm.html', message = message)
            else:
                message = "You don't have permission to delete this post."
                self.render('confirm.html', message = message)
        else:
            self.redirect('/login')







app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/signup', Signup),
    ('/welcome', Welcome),
    ('/register', Register),
    ('/blog/?', BlogFront),
    ('/blog/([0-9]+)', PostPage),
    ('/blog/newpost', NewPost),
    ('/login', Login),
    ('/logout', Logout),
    ('/blog/delete/([0-9]+)', DeletePost)
], debug=True)


