from app import app,login_manager
from flask import render_template,request,session,g,redirect,url_for,flash,abort
#from app.model import Item
from .forms import LoginForm,RegisterForm,ProfileForm,ChangePasswordForm,\
        PostForm
from app.models import User,Post,Category
import sqlite3
from werkzeug import secure_filename
from datetime import datetime
from flask.ext.login import login_user,logout_user,login_required,current_user
from app.utils import clean_html
import os
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def is_author(post):
    if post.author_id == current_user.id:
        return True
    return False



@app.route('/')
def index():
    if request.args.get('page'):
        try:
            page=int(request.args.get('page'))
        except ValueError:
            flash('输入了不允许的参数')
            abort(404)
    else:
        page=1
    categorys = Category.query.all()
    posts = Post.query.order_by(Post.id.desc()).paginate(page,per_page=15)
    return render_template('index.html',categorys=categorys,pagination=posts,count=20)

'''=======================================================================

        The Category View

========================================================================'''


@app.route('/category/<category_name>')
def category(category_name):
    categorys = Category.query.all()
    category = Category.query.filter_by(name=category_name).first()
    if category:
        posts = category.posts.all()
        return render_template('category.html',categorys=categorys,category=category,posts=posts)
    return redirect(url_for('index'))


'''========= End of the Cateogry View ==================================='''






"""=========================================================================

        The Post View

=========================================================================="""

@app.route('/post/<post_id>')
def view_post(post_id):
    post = Post.query.get(post_id)
    if post:
        author = post.author
        return render_template('view-post.html',post=post,author=author)
    abort(404)


@app.route('/post',methods=['GET','POST'])
@app.route('/post/<int:post_id>/edit',methods=['GET','POST'])
@login_required
def edit_post(post_id=None):
    if post_id:
        post = Post.query.get(post_id)
        if not is_author(post):
            abort(404)
    else:
        post = Post()
    form = PostForm(request.form,post)
    form.category_id.choices = [(g.id,g.name) for g in Category.query.order_by('id')]
    if form.validate_on_submit():
        form.content.data = clean_html(form.content.data)  #clean the html content
        category = Category.query.get(form.category_id.data)
        if category:
            form.populate_obj(post)
            post.save(author=current_user,category=category)
            return redirect(post.url)
    return render_template('edit-post.html',form=form)
    pass

@app.route('/post/<int:post_id>/delete')
@login_required
def delete_post(post_id):
    '''
    Delete a post by the author
    '''
# TODO: Check CRSF
    post = Post.query.get(post_id)
    if not is_author(post):
        flash('You do not have the permission to do this','danger')
        abort(403)
    post.delete()
    return redirect(request.args.get("next") or url_for("index"))




"""======== End of the Post View ======================================"""






"""===============================================================================

    user views

================================================================================"""

@login_manager.user_loader
def load_user(userid):
    """User username to callback
    param
    userid: in fact, it's username
    """
    return User.get(userid)



@app.route("/signup",methods=['GET','POST'])
def register():
    user = User()
    errors = list()
    form = RegisterForm(csrf_enabled=False)
    if form.validate_on_submit():
        form.populate_obj(user)
        user.save()
        login_user(user)
        return redirect(url_for('index'))
    if form.errors:
        for item in form.errors.values():
            errors.extend(item)
    return render_template("signin.html",form=form,errors=errors,act="signup")
    pass


@app.route("/signin",methods=['GET','POST'])
def login():
    if current_user.is_authenticated():
        return redirect(url_for('profile',username=current_user.username))
    error=None
    user=User()
    form = LoginForm(csrf_enabled=False)
    if form.validate_on_submit():
        user,status = User.authenticate(form['username'].data,form['password'].data)
        if user and status:
            login_user(user)
            flash("Logged in successfully.")
            return redirect(request.args.get("next") or url_for("index"))
        error="用户名或密码错误"
    return render_template("signin.html",form=form,act="signin",login_error=error)



@app.route('/logout')
@login_required
def logout():
    '''Logout the current user'''
    logout_user()
    return redirect(url_for('index'))



@app.route("/user")
def user():
    return redirect(url_for('login'))



@app.route("/user/<username>/")
def profile(username):
    user=User().query.filter_by(username=username).first()
    if user:
        return render_template("profile.html",user=user)
    flash("User not find")
    abort(404)

@app.route("/user/<username>/posts/")
def view_user_posts(username):
    page = request.args.get("page",1,type=int)
    user = User.query.filter_by(username=username).first_or_404()
    if user:
        posts = user.posts.order_by(Post.id.desc()).paginate(page)
        return render_template("user-posts.html",user=user,pagination=posts)
    flash("User not find")
    abort(404)





@app.route("/setting")
@app.route("/setting/profile",methods=['GET','POST'])
@login_required
def edit_profile():
    username=current_user.username
    user=User().query.filter_by(username=username).first()
    form = ProfileForm(request.form,user)
    print(form.data)
    print(form.errors)
    if form.validate_on_submit():
        form.populate_obj(user)
        user.save()
        return redirect(url_for('profile',username=username))
    return render_template('edit-profile.html',user=user,form=form)




@app.route('/setting/password',methods=['GET','POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    errors = None
    if form.validate_on_submit():
        current_user.password = form.new_password.data
        current_user.save()
        flash("Password updataed.","success")
        return "passwordchanged"
    errors = form.old_password.errors
    return render_template("change-password.html",user=current_user,errors=errors,form=form)


@app.route('/resetpassword',methods=['GET','POST'])
def forget_password():
#TODO forget_password
    pass

@app.route('/resetpassword/<token>',methods=['GET','POST'])
def reset_password():
#TODO reset_password
    pass



