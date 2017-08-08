import os, sys, json, time, requests, uuid, re, datetime

from flask import *
from array import *
from flaskext.markdown import Markdown
from flask_sqlalchemy import SQLAlchemy
from flask_openid import OpenID
from os.path import dirname, join
from urllib.request import urlopen
from urllib.parse import urlencode
from flask_socketio import *
from werkzeug import generate_password_hash, check_password_hash
import logging

# Setting up variables

app = Flask(__name__)

from settings import config, github #custom module for security reasons

CONFIG = config.get_config(app)
github.setup(CONFIG)

LOCATION = CONFIG['app']['location']
SECRETS = CONFIG['web']
STATIC = LOCATION + 'static/'
BLOGS = LOCATION + 'blog.json'
VERSION = CONFIG['app']['version']
HOST = CONFIG['app']['host']
DEBUG = CONFIG['app']['debug']
PORT = CONFIG['app']['port']

STEAM_API_KEY = CONFIG['steam']['api_key']

handler = logging.FileHandler(LOCATION + '/logs/error.log')
handler.setLevel(logging.ERROR)

app.logger.addHandler(handler)

app.config.update(
    SQLALCHEMY_DATABASE_URI = CONFIG['mysql']['full_uri'],
    SQLALCHEMY_TRACK_MODIFICATIONS = False
)

Markdown(app)
oid = OpenID(app)
oid2 = OpenID(app)
db = SQLAlchemy(app)
socketio = SocketIO(app)

## Set up session variables

def init():
    if 'log' not in session:
        session['log'] = {'fail': False, 'show': 0}
    if 'logged_in' not in session:
        session['logged_in'] = False

@app.route('/')
def index():
    init()
    if session['log']['show'] > 0:
        session['log']['show'] = session['log']['show'] - 1
    msg = open(STATIC + 'messages/main.txt', 'r').read()
    ft = open(STATIC + 'messages/footer.txt', 'r').read()
    nav = open(STATIC + 'messages/nav.txt', 'r').read()
    return render_template('index.html', message=msg, footer=ft, nav=nav, version=VERSION)
    
@app.route('/ethernet')
def ethernet():
    return redirect('/products/ethernet')

@app.route('/blog/')
@app.route('/blog')
def blog():
    ft = open(STATIC + 'messages/footer.txt', 'r').read()
    nav = open(STATIC + 'messages/nav.txt', 'r').read()
    return render_template('blog.html', footer=ft, nav=nav, blogs=getBlogs(), version=VERSION)

def getBlogs():
    html = ''
    temp = ''
    blgs = open(BLOGS)
    blogs = json.loads(blgs.read())
    blgs.close()
    if len(blogs['blog']) > 0:
        for blog in blogs['blog']:
            temp = '<a href="/blog/'+str(blog['id'])+'" style="text-decoration: none;"><post><title>'+blog['title']+'</title><author>'+blog['author']+' | '+blog['date']+'</author><summary>'+blog['body']+'</summary></post></a>' + html
            html = temp
        return html
    else:
        return '<br><br><p>It looks like there are no blogs!</p>'

@app.route('/admin')
@app.route('/admin/')
def admin():
    if session.get('logged_in') == True:
        ft = open(STATIC + 'messages/footer.txt', 'r').read()
        nav = open(STATIC + 'messages/nav.txt', 'r').read()
        return render_template('admin.html', footer=ft, nav=nav, version=VERSION)
    else: 
        return redirect(url_for('login'))

@app.route('/blog/new/', methods=['GET', 'POST'])
@app.route('/blog/new', methods=['GET', 'POST'])
def newblog():
    if request.method == 'GET':
        if session.get('logged_in') == True:
            ft = open(STATIC + 'messages/footer.txt', 'r').read()
            nav = open(STATIC + 'messages/nav.txt', 'r').read()
            date = time.strftime(" %b %d, %Y")
            return render_template('blog-new.html', footer=ft, nav=nav, date=date, version=VERSION)
        else:
            abort(401)
    else:
        if session['logged_in'] == False:
            abort(401)
        else:
            # loading json data base, making it python readable, and closing
            db = open(BLOGS, 'r')
            jsondb = json.loads(db.read())
            db.close()
            # grabbing data
            title = request.form['title']
            body = request.form['body']
            date = time.strftime("%b %d, %Y")
            name = session['name']
            # modifying to JSON object
            jsondb["blog"].append({'id': jsondb["blogs"],'title':title,'date':date,'author':session['name'],'body':body})
            jsondb["blogs"] += 1
            # writing to data base
            db = open(BLOGS, 'w')
            db.write(json.dumps(jsondb))
            db.close()
            return redirect(url_for('blog'))

@app.route('/blog/<id>/', methods=['GET', 'POST'])
@app.route('/blog/<id>', methods=['GET', 'POST'])
def blogDisplay(id):
    if request.method == 'GET':
        ft = open(STATIC + 'messages/footer.txt', 'r').read()
        nav = open(STATIC + 'messages/nav.txt', 'r').read()
        # grabbing blog data
        blgs = open(BLOGS)
        blogs = json.loads(blgs.read())
        blgs.close()
        for blog in blogs['blog']:
            if str(blog['id']) == str(id):
                mkd = '# '+blog['title']+'\n##### '+blog['author']+' | '+blog['date']+'\n___\n'+blog['body']
                return render_template('blog-post.html', footer=ft, nav=nav, mkd=mkd, version=VERSION)
        abort(404)
    else:
        btn = request.form['option']
        print(btn)
        if btn == 'trash':
            blgs = open(BLOGS)
            blogs = json.loads(blgs.read())
            blgs.close()
            
            keep = []
            
            for blog in blogs['blog']:
                if str(blog['id']) != str(id):
                    keep.append(blog)
                    
            blogs['blog'] = keep
            
            blgs = open(BLOGS, 'w')
            blgs.write(json.dumps(blogs))
            blgs.close()
            return redirect(url_for('blog'))
            
        elif btn == 'edit':
            return redirect('/blog/'+id+'/edit')
        else:
            return redirect(url_for('blog'))
            

@app.route('/blog/<id>/edit/', methods=['GET', 'POST'])
@app.route('/blog/<id>/edit', methods=['GET', 'POST'])
def editBlog(id):
    ft = open(STATIC + 'messages/footer.txt', 'r').read()
    nav = open(STATIC + 'messages/nav.txt', 'r').read()
    if request.method == 'GET':
        if session.get('logged_in') == True:
            ft = open(STATIC + 'messages/footer.txt', 'r').read()
            nav = open(STATIC + 'messages/nav.txt', 'r').read()
            # grabbing blog data
            blgs = open(BLOGS, 'r')
            blogs = json.loads(blgs.read())
            blgs.close()
            for blog in blogs['blog']:
                if str(blog['id']) == str(id):
                    title = blog['title']
                    date = blog['date']
                    body = blog['body']
                    author = blog['author']
                    return render_template('blog-edit.html', footer=ft, nav=nav, title=title, date=date, body=body, author=author, version=VERSION)
            abort(404)
        else: 
            abort(401)
    else:
        if session.get('logged_in') == True:
            # loading json data base, making it python readable, and closing
            db = open(BLOGS, 'r')
            jsondb = json.loads(db.read())
            db.close()
            # grabbing data
            title = request.form['title']
            body = request.form['body']
            date = time.strftime("%b %d, %Y")
            name = '' # to be found
            # modifying to JSON object
            
            for blog in jsondb['blog']:
                if str(blog['id']) == str(id):
                    blog['title'] = title
                    blog['body'] = body
            
            # writing to data base
            db = open(BLOGS, 'w')
            db.write(json.dumps(jsondb))
            db.close()
            return redirect(url_for('blog') + "/"+str(id))
        else: 
            abort(401)
        

@app.route('/products/')
@app.route('/products')
def products():
    ft = open(STATIC + 'messages/footer.txt', 'r').read()
    nav = open(STATIC + 'messages/nav.txt', 'r').read()
    return render_template('products.html', footer=ft, nav=nav, version=VERSION)
    
@app.route('/services/')
@app.route('/services')
def services():
    ft = open(STATIC + 'messages/footer.txt', 'r').read()
    nav = open(STATIC + 'messages/nav.txt', 'r').read()
    return render_template('services.html', footer=ft, nav=nav, version=VERSION)

@app.route('/services/web/calc/')
@app.route('/services/web/calc')
def webcalc():
    ft = open(STATIC + 'messages/footer.txt', 'r').read()
    nav = open(STATIC + 'messages/nav.txt', 'r').read()
    return render_template('webcalc.html', footer=ft, nav=nav, version=VERSION)

@app.route('/products/<subpage>/')
@app.route('/products/<subpage>')
@app.route('/services/<subpage>/')
@app.route('/services/<subpage>')
def serviceAndProjectPage(subpage):
    ft = open(STATIC + 'messages/footer.txt', 'r').read()
    nav = open(STATIC + 'messages/nav.txt', 'r').read()
    
    if subpage == 'ethernet':
        return render_template('ethernet.html', footer=ft, nav=nav, version=VERSION)
    elif os.path.isfile(STATIC + 'messages/' + subpage + '.txt'):
        msg = open(STATIC + 'messages/' + subpage + '.txt', 'r').read()
    else:
        return abort(404)
        
    return render_template('service.html', footer=ft, nav=nav, service=subpage, innerText=msg, version=VERSION)

@app.errorhandler(400)
def error400(error):
    ft = open(STATIC + 'messages/footer.txt', 'r').read()
    nav = open(STATIC + 'messages/nav.txt', 'r').read()
    msg = open(STATIC + 'messages/error/400', 'r').read()
    return render_template('error.html', footer=ft, nav=nav, code='400', innerText=msg, version=VERSION)

@app.errorhandler(404)
def error404(error):
    ft = open(STATIC + 'messages/footer.txt', 'r').read()
    nav = open(STATIC + 'messages/nav.txt', 'r').read()
    msg = open(STATIC + 'messages/error/404', 'r').read()
    return render_template('error.html', footer=ft, nav=nav, code='404', innerText=msg, version=VERSION)

@app.errorhandler(401)
def error401(error):
    ft = open(STATIC + 'messages/footer.txt', 'r').read()
    nav = open(STATIC + 'messages/nav.txt', 'r').read()
    msg = open(STATIC + 'messages/error/401', 'r').read()
    return render_template('error.html', footer=ft, nav=nav, code='401', innerText=msg, version=VERSION)

@app.errorhandler(500)
def error500(error):
    ft = open(STATIC + 'messages/footer.txt', 'r').read()
    nav = open(STATIC + 'messages/nav.txt', 'r').read()
    msg = open(STATIC + 'messages/error/500', 'r').read()
    return render_template('error.html', footer=ft, nav=nav, code='500', innerText=msg, version=VERSION)

@app.route('/login/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        result = findUser(request.form['username'], request.form['password'])
        
        if result == True:
            session['logged_in'] = True
            return redirect(url_for('blog'))
        else:
            return render_template('login.html', error='Invalid username or password<br>', version=VERSION)
    else:
        if session.get('logged_in') == True:
            return redirect("/blog")
        else:
            return render_template('login.html', error='', version=VERSION)
    
def findUser(usr, psw):
    username = 'invalid'
    password = 'invalid'
    name = None
    
    db = open(LOCATION + 'users.json', 'r')
    jsondb = json.loads(db.read())
    db.close()
    for user in jsondb['user']:
        if usr == user['username']:
            name = user['name']
            username = True
        elif usr == user['email']:
            name = user['name']
            username = True
        if psw == user['password']:
            password = True
    
    if username == True and password == True:
        session['name'] = name
        return True
    else:
        return False

@app.route('/login/google')
def google_callback():
    if 'logged_in' in session and session['logged_in'] == False:
        if 'code' not in request.args:
            redirect_url = 'https://accounts.google.com/o/oauth2/auth'
            query_params = {
                'response_type': 'code',
                'client_id': SECRETS['client_id'],
                'redirect_uri': url_for('google_callback', _external=True),
                'scope': 'email profile',
                'access_type': 'offline'
            }
            final_url = requests.Request(url=redirect_url, params=query_params).prepare().url
            return redirect(final_url)
        else:
            if 'error' in request.args:
                return Response(request.args.get('message'))

            auth_code = request.args['code']

            oauth_link = 'https://accounts.google.com/o/oauth2/token'
            post_params = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'client_id': SECRETS['client_id'],
                'client_secret': SECRETS['client_secret'],
                'redirect_uri': url_for('google_callback', _external=True),
            }

            result = requests.post(oauth_link, data=post_params).json()
            access_token = result['access_token']

            # Get Info
            google_plus_user_info_api = 'https://www.googleapis.com/userinfo/v2/me'
            headers = {'Authorization': 'Bearer {}'.format(access_token)}
            user_info = requests.get(google_plus_user_info_api, headers=headers).json()
            print(user_info)
            loggedin = google_login(user_info)
            if loggedin == True:
                session['userinfo'] = user_info
                session['logged_in'] = True
                session["log"] = {'fail': False, 'show': 2}
                return redirect(url_for('index'))
            else:
                session["log"] = {'fail': True, 'show': 2}
                return redirect(url_for('index'))
    elif 'logged_in' not in session:
        session['logged_in'] = False;
        return google_callback()
    else:
        return redirect(url_for('index'))

def google_login(data):
    email = 'invalid'
    gid = 'invalid'
    name = None
    
    db = open(LOCATION + 'users.json', 'r')
    jsondb = json.loads(db.read())
    db.close()
    for user in jsondb['user']:
        if data['email'] == user['email']:
            email = True
        if data['id'] == user['gid']:
            name = user['name']
            gid = True
    
    if email == True and gid == True:
        session['name'] = name
        return True
    else:
        return False

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session['logged_in'] = False
    session.pop('name', None)
    session.pop('userinfo', None)
    return redirect(url_for('blog'))
    
####      Piggah Bro Studios Community Forum Layout      ####

class members(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    steam_id = db.Column(db.String(50))
    nickname = db.Column(db.String(32))
    avatar = db.Column(db.String(200))
    realname = db.Column(db.String(100))
    username = db.Column(db.String(18))
    password = db.Column(db.String(255))
    posts = db.Column(db.String(10))
    email = db.Column(db.String(100))
    joined = db.Column(db.String(20))
    error = None
    steamerror = None

    @staticmethod
    def get_or_create(steam_id):
        rv = members.query.filter_by(steam_id=steam_id).first()
        if rv is None:
            if g.user:
                g.user.steam_id = steam_id
                db.session.commit()
            else:
                rv = members()
                rv.steam_id = steam_id
                db.session.add(rv)
        return rv
        
    def check_for_steam(steam_id):
        rv = members.query.filter_by(steam_id=steam_id).first()
        if rv is None:
            if g.user:
                g.user.steam_id = steam_id
                db.session.commit()
                return True
        return False

    @staticmethod
    def create_user(username, email):
        test = members()
        test1 = members.query.filter_by(username=username).first()
        test2 = members.query.filter_by(email=email).first()
        if test1 is not None:
          test.error = "Username has been taken!"
        elif test2 is not None:
          test.error = "Email has been taken!"
        if test.error == None:
            test = members()
            test.username = username
            test.posts = 0
            test.email = email
            db.session.add(test)
        return test

    @staticmethod
    def check_for_user(username, email):
        test = members()
        test1 = members.query.filter_by(username=username).first()
        test2 = members.query.filter_by(email=email).first()
        if test1 is not None:
          test.error = "Username has been taken!"
        elif test2 is not None:
          test.error = "Email has been taken!"
        return test.error

    @staticmethod
    def get_user(username, password):
        test = members.query.filter_by(username=username).first()
        if test is not None:
          if check_password_hash(test.password, password):
            return test
          else:
            test.error = 'Incorrect username or password!'
            return test
        else:
          test.error = 'User was not found!'
          return test

class forum_threads(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    topic = db.Column(db.String(50))
    created = db.Column(db.String(20))
    subtopic = db.Column(db.String(50))
    author_id = db.Column(db.String(10))
    privilege = db.Column(db.String(10))
    error = None

    @staticmethod
    def get_threads(topic):
        results = forum_threads.query.filter_by(topic=topic).all()
        if results is not None:
          data = []
          for result in results:
            author = members.query.filter_by(id=result.author_id).first()
            _format = "%b %d, %Y %-I:%M %p"
            _created = result.created.strftime(_format)
            _author = "%s" % Markup.escape(author.nickname)
            _topic_test = False
            for t in data:
              if t['topic'] == result.topic:
                _topic_test = True
            if _topic_test == False:
              data.append({
                'topic': result.topic,
                'subtopics': [{
                  'subtopic': result.subtopic,
                  'thread': {
                    'title': result.title,
                    'created': _created,
                    'author': {
                      'id': result.author_id,
                      'name': _author
                    },
                    'privilege': result.privilege,
                  }
                }]
              })
            else:
              for x in data:
                if x['topic'] == result.topic:
                  x['subtopics'].append({
                    'subtopic': result.subtopic,
                    'thread': {
                      'title': result.title,
                      'created': _created,
                      'author': {
                        'id': result.author_id,
                        'name': _author
                      },
                      'privilege': result.privilege,
                    }
                  })
          return data
        else:
          result.error = 'Threads were not found!'
          return result

_steam_id_re = re.compile('steamcommunity.com/openid/id/(.*?)$')

def get_steam_userinfo(steam_id):
    options = {
        'key': STEAM_API_KEY,
        'steamids': steam_id
    }
    url = 'http://api.steampowered.com/ISteamUser/' \
          'GetPlayerSummaries/v0001/?%s' % urlencode(options)
    rv = json.load(urlopen(url))
    return rv['response']['players']['player'][0] or {}

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = members.query.filter_by(id=session['user_id']).first()

@app.route("/gaming/login", methods=['GET', 'POST'])
@app.route("/gaming/login/", methods=['GET', 'POST'])
def gaming_login():
  if request.method == 'POST':
    if request.form['type'] == "login":
      # Basic testing for username/password combo
      _password = request.form['password']
      _username = request.form['username']
      g.user = members.get_user(_username,_password)
      if g.user.error:
        return render_template('gaming/login.html', error=g.user.error, version=VERSION)
      else:
        session['user_id'] = g.user.id
        return redirect(url_for('gaming_forums'))
    elif request.form['type'] == "signup":
      # set variables
      _pass1 = request.form['password']
      _pass2 = request.form['password2']
      _username = request.form['username']
      _email = request.form['email']
      _name = request.form['realname']
      # Test if passwords match
      if _pass1 != _pass2:
        return render_template('gaming/login.html', error='Passwords do not match', version=VERSION)
      else:
        _password = generate_password_hash(_pass1)
        g.user = members.create_user(_username,_email)
        if g.user.error is not None:
          return render_template('gaming/login.html', error=g.user.error, version=VERSION)
        else:
          g.user.nickname = _username
          g.user.password = _password
          g.user.realname = _name
          db.session.commit()
          session['user_id'] = g.user.id
          return redirect(url_for('gaming_forums'))
    else:
      return render_template('gaming/login.html', error='Unexpected Error', version=VERSION)
  else:
    if g.user is not None:
        return redirect(url_for('gaming_forums'))
    else:
        return render_template('gaming/login.html', error='', version=VERSION)

@app.route("/gaming/login/steam")
@app.route("/gaming/login/steam/")
@oid.loginhandler
def gaming_login_steam():
    if g.user is not None:
        return redirect(oid.get_next_url())
    else:
        return oid.try_login("http://steamcommunity.com/openid")
@oid.after_login
def update_forum_user(resp):
    match = _steam_id_re.search(resp.identity_url)
    g.user = members.get_or_create(match.group(1))
    steamdata = get_steam_userinfo(g.user.steam_id)
    if g.user.nickname == None:
      g.user.nickname = steamdata['personaname']
      g.user.avatar = steamdata['avatarfull']
      if 'realname' in steamdata:
        g.user.realname = steamdata['realname']
    elif g.user.avatar == None:
      g.user.avatar = steamdata['avatarfull']
    db.session.commit()
    session['user_id'] = g.user.id
    return redirect(oid.get_next_url())

@app.route("/gaming/account/steam")
@app.route("/gaming/account/steam/")
@oid2.loginhandler
def gaming_add_steam():
    return oid.try_login("http://steamcommunity.com/openid")

@oid2.after_login
def update_user(resp):
    match = _steam_id_re.search(resp.identity_url)
    check = members.check_for_steam(match.group(1))
    if check == True:
      steamdata = get_steam_userinfo(g.user.steam_id)
      if g.user.nickname == None:
        g.user.nickname = steamdata['personaname']
      if g.user.avatar == None:
        g.user.avatar = steamdata['avatarfull']
      db.session.commit()
      return redirect(oid.get_next_url())
    else:
      session['steamerror'] = "Steam ID already in use!"
      return redirect(url_for('gaming_account')+'#create-steam-login')

@app.route('/gaming/logout')
@app.route('/gaming/logout/')
def gaming_logout():
    session.pop('user_id', None)
    return redirect(oid.get_next_url())

@app.route('/gaming')
@app.route('/gaming/')
def gaming():
    return render_template('gaming/index.html', version=VERSION)

@app.route('/gaming/account', methods=['GET', 'POST'])
@app.route('/gaming/account/', methods=['GET', 'POST'])
def gaming_account():
  if g.user:
    _name = Markup.escape(g.user.nickname)
    _format_before = "%Y-%m-%d %H:%M:%S"
    _format_after = "%b %d, %Y %-I:%M %p"
    _avatar = g.user.avatar
    _joined = datetime.datetime.strptime(str(g.user.joined), _format_before).strftime(_format_after)
    if request.method == "GET":
      if 'steamerror' in session:
        _error = Markup.escape(session['steamerror'])
        print(_error)
        session.pop('steamerror')
        return render_template('gaming/account.html',\
                name=_name,joined=_joined,img=_avatar,\
                serr=_error, version=VERSION)
      else:
        return render_template('gaming/account.html',\
                name=_name,joined=_joined,img=_avatar, version=VERSION)
    else:
      if request.form['form'] == "create_login":
        _pass1 = request.form['password']
        _pass2 = request.form['password2']
        _username = request.form['username']
        _email = request.form['email']
        if _pass1 != _pass2:
          return render_template('gaming/account.html',name=_name,\
                  joined=_joined,img=_avatar,error="Passwords do not match!",\
                  version=VERSION)
        _check = members.check_for_user(_username, _email)
        if _check == None:
          _password = generate_password_hash(_pass1)
          g.user.password = _password
          g.user.username = _username
          g.user.email = _email
          db.session.commit()
          return render_template('gaming/account.html',\
                  name=_name,joined=_joined,img=_avatar,version=VERSION)
        else:
          return render_template('gaming/account.html',name=_name,\
                  joined=_joined,img=_avatar,error=_check,version=VERSION)
      elif request.form['form'] == "manage_login":
        _old_pass = request.form['password_old']
        _pass1 = request.form['password']
        _pass2 = request.form['password2']
        if _pass1 != _pass2:
          return render_template('gaming/account.html',name=_name,\
                  joined=_joined,img=_avatar,error="Passwords do not match!",\
                  version=VERSION)
        if check_password_hash(g.user.password, _old_pass):
          _password = generate_password_hash(_pass1)
          g.user.password = _password
          db.session.commit()
          return render_template('gaming/account.html',\
                  name=_name,joined=_joined,img=_avatar,version=VERSION)
        else:
          return render_template('gaming/account.html',name=_name,\
                  joined=_joined,img=_avatar,version=VERSION,\
                  perr="Old password does not match database")
      elif request.form['form'] == "remove_steam":
        if g.user.username != None and g.user.password != None:
          g.user.steam_id = None
          db.session.commit()
          return render_template('gaming/account.html',\
                  name=_name,joined=_joined,img=_avatar,version=VERSION)
        else:
          return render_template('gaming/account.html',name=_name,\
                  joined=_joined,img=_avatar,version=VERSION,\
                  derr="Please create a login before deactivating Steam login!")
      else:
        return render_template('gaming/account.html',\
                name=_name,joined=_joined,img=_avatar,\
                error="This form is not developed on the server side yet",\
                version=VERSION)
  else:
    return redirect(url_for("gaming_login"))

@app.route('/gaming/forums')
@app.route('/gaming/forums/')
def gaming_forums():
  fupdates = forum_threads.get_threads('Development')
  if g.user:
    _name = Markup.escape(g.user.nickname)
    _posts = Markup.escape(g.user.posts)
    _format_before = "%Y-%m-%d %H:%M:%S"
    _format_after = "%b %d, %Y %-I:%M %p"
    _joined = datetime.datetime.strptime(str(g.user.joined), _format_before).strftime(_format_after)
    return render_template('gaming/forums.html',\
            name=_name,posts=_posts,joined=_joined,\
            version=VERSION,forum=fupdates)
  else:
    return render_template('gaming/forums.html',forum=fupdates,version=VERSION)
    
## Github Payload Management

@app.route('/push', methods=['POST'])
def github_payload():
  data = request.get_json()
  if "head_commit" in data:
    with open(LOCATION + "logs/github/"+data['head_commit']['timestamp']+".log", 'w') as log:
      log.write("Received JSON: "+json.dumps(data))
      log.close()
    github.log("Received package created at "+data['head_commit']['timestamp'])
    pull = github.pull()
    if pull == True:
      return "Received package created at "+data['head_commit']['timestamp']
    else: 
      return "Failed to pull package!" 
  else:
    return "Package Aborted: Received data was not a commit"
  
#### ONLY COPY AND PASTE STUFF ABOVE THIS LINE TO SERVER ####

if __name__ == "__main__":
    socketio.run(app, debug=DEBUG, host=HOST, port=PORT)
