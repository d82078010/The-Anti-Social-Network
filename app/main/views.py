"""
    In the MVC paradigm, here we have the main views to the user.
"""

from flask import render_template, redirect, url_for, abort, flash, \
request, current_app, make_response, send_from_directory
from flask.ext.login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm, CreateGroupForm
from .. import db
from ..models import Permission, Role, User, Post, Comment, Group
from ..decorators import admin_required, permission_required
import os



# main page
@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.body.data,
                    like_count=0,  # todo: isso aqui deveria ser setado como default!
                    author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    show_followed = False
    # show only post by followers
    if current_user.is_authenticated():
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['ANTISOCIAL_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           show_followed=show_followed, pagination=pagination)


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


# profile page route
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
            abort(404)
    # display blogs for the user
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)



# editing profile
@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)



# profile edit for administrators
@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)

# add a permanent link to posts
# the urls that will be assigned to blog posts are constructed
# with the unique id field assigned when the post is inserted in
# the database
@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)

    # Allowing comments
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('Comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) / \
            current_app.config['ANTISOCIAL_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['ANTISOCIAL_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items


    # we send a list so that _post.html template can be used
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)


# like post
@main.route('/like/<id>')
@login_required
def like(id):
    post = Post.query.filter_by(id=id).first()
    if post is None:
        flash('Invalid post.')
        return redirect(url_for('.index'))
    post.like_set(current_user)
    flash('You liked this post.')
    return redirect(url_for('.post', id=id))


@main.route('/dislike/<id>')
@login_required
def dislike(id):
    post = Post.query.filter_by(id=id).first()
    if post is None:
        flash('Invalid post.')
        return redirect(url_for('.index'))
    post.like_remove(current_user)
    flash('You disliked this post.')
    return redirect(url_for('.post', id=id))


# edit posts
@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)

# delete post
@main.route('/postdelete/<int:id>')
@login_required
def postdelete(id):
    post = Post.query.filter_by(id=id)

    if post.first().group is None:
        go_to = redirect(url_for('.index'))
    else:
        go_to = redirect(url_for('.group', id=post.first().group_id))

    post.delete()

    return go_to

# following stuff

@main.route('/follow/<username>')
@login_required
#@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))

@main.route('/unfollow/<username>')
@login_required
#@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['ANTISOCIAL_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['ANTISOCIAL_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


# To show followed posts
@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


# Moderating comments

@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['ANTISOCIAL_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))

@main.route('/creategroup', methods=['GET', 'POST'])
@login_required
def creategroup():
    form = CreateGroupForm()
    if form.validate_on_submit():
        group = Group(name=form.name.data,
                      description=form.description.data,
                      public=form.public.data,
                      admin_id=current_user.id)

        db.session.add(group)
        db.session.flush()

        # todo: nao pode-se usar caminho absoluto!
        path = os.path.join('/Users/brunomacabeusaquino/ApenasMeu/Dropbox (BEPiD)/CEFET/EngenhariaSoftware/The-Anti-Social-Network/app/static/uploads/group_photo/', str(group.id) + '.png')
        form.photo.data.save(path)

        flash('Your group was created.')
        return redirect(url_for('.group', id=group.id))

    return render_template('create_group.html', form=form)


@main.route('/group/<int:id>', methods=['GET', 'POST'])
@login_required
def group(id):
    group = Group.query.filter_by(id=id).first()
    if group is None:
            abort(404)

    form = PostForm()
    if form.validate_on_submit():
        if group.has_already_join(current_user):
            post = Post(body=form.body.data,
                        author=current_user._get_current_object(),
                        like_count=0, # todo: isso aqui deveria ser setado como default!
                        group_id=id)
            db.session.add(post)
        else:
            flash("You can't write post.")
        return redirect(url_for('.group', id=id))

    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(group_id=id).order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['ANTISOCIAL_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items

    return render_template('group.html', group=group, posts=posts, pagination=pagination, form=form)


@main.route('/listgroups/<filter>')
@login_required
def listgroups(filter):
    page = request.args.get('page', 1, type=int)

    pagination = Group.query.paginate(
        page, per_page=current_app.config['ANTISOCIAL_POSTS_PER_PAGE'],
        error_out=False)
    groups = pagination.items

    return render_template('listgroups.html', groups=groups,
                           pagination=pagination)

@main.route('/groupdelete/<int:id>')
@login_required
def groupdelete(id):
    group = Group.query.filter_by(id=id)
    group.delete()

    return redirect(url_for('.index'))

# like post
@main.route('/groupjoin/<id>')
@login_required
def groupjoin(id):
    group = Group.query.filter_by(id=id).first()
    if group is None:
        flash('Invalid group.')
        return redirect(url_for('.index'))
    group.user_join(current_user)
    flash('You join in this group.')
    return redirect(url_for('.group', id=id))


@main.route('/groupleave/<id>')
@login_required
def groupleave(id):
    group = Group.query.filter_by(id=id).first()
    if group is None:
        flash('Invalid group.')
        return redirect(url_for('.index'))
    group.user_leave(current_user)
    flash('You leaved from this group.')
    return redirect(url_for('.group', id=id))
