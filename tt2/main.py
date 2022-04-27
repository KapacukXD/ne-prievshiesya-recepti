import shutil

from flask import Flask, render_template, redirect, request, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.exceptions import abort
from os import mkdir, path, rmdir
from PIL import Image

from forms.LoginForm import LoginForm
from forms.news import NewsForm
from data import db_session, news_api
from data.users import User
from data.news import News
from forms.user import RegisterForm

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data.strip()).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        if db_sess.query(User).filter(User.name == form.name.data.strip()).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Имя занято")
        user = User(
            name=form.name.data.strip(),
            email=form.email.data,
            about=form.about.data
        )
        f = request.files['file']
        if f.filename == '':
            print('Net faila')
            user.logo = 'https://avatars.mds.yandex.net/i?id=b75e339273d90bbabfa25f6bc6a4430c-5866055-images-thumbs&n=13&exp=1'
        else:
            i = form.name.data.strip()
            if not path.exists(f'static/images/{i}'):
                mkdir(f'static/images/{i}')
                mkdir(f'static/images/{i}/log')
            im = Image.open(f)
            im.save(f'static/images/{i}/log/log.png')
            user.logo = f'static/images/{i}/log/log.png'
        print(user.id)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/about', methods=['GET', 'POST'])
@login_required
def about():
    return render_template('about.html', title='О нас')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        try:
            cur_id = db_sess.query(News).order_by(News.id.desc()).first().id + 1
        except:
            cur_id = 1
        print(cur_id)
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        if not path.exists(f'static/images/posts/{cur_id}'):
            mkdir(f'static/images/posts/{cur_id}')
        else:
            shutil.rmtree(f'static/images/posts/{cur_id}')
            mkdir(f'static/images/posts/{cur_id}')
        log = request.files['log']
        imgs = request.files['imgs']
        if imgs:
            names = []
            imgs = request.files.getlist("imgs")
            for i, f in enumerate(imgs):
                im = Image.open(f)
                im.save(f'static/images/posts/{cur_id}/{i}.png')
                names += [f'static/images/posts/{cur_id}/{i}.png']
            news.imgs = ' '.join(names)
        else:
            news.imgs = ''
        if log.filename:
            im = Image.open(log)
            im.save(f'static/images/posts/{cur_id}/log.png')
            news.log = f'static/images/posts/{cur_id}/log.png'
        else:
            news.log = 'https://avatars.mds.yandex.net/i?id=b75e339273d90bbabfa25f6bc6a4430c-5866055-images-thumbs&n=13&exp=1'
        news.content = form.content.data
        if len(news.title) <= 33:
            news.show_cont = form.title.data + ' ' * (33 - len(news.title))
        else:
            news.show_cont = form.title.data[:30] + '...'
        news.is_private = form.is_private.data
        news.ingr = form.ingr.data
        current_user.recipes.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление рецепта',
                           form=form)


@app.route('/recipe/<int:id>', methods=['GET', 'POST'])
@login_required
def show_rec(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id).first()
    a = bool(news.imgs)
    return render_template('recipe.html',
                           title='#',
                           content=news.content, tite=news.title, imgs=news.imgs.split(), ch=a,
                           ings=news.ingr, rec=news.content)


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
            form.ingr.data = news.ingr
        else:
            abort(404)

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            news.ingr = form.ingr.data
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            cur_id = news.id

            log = request.files['log']
            imgs = request.files['imgs']
            if imgs:
                names = []
                imgs = request.files.getlist("imgs")
                for i, f in enumerate(imgs):
                    im = Image.open(f)
                    im.save(f'static/images/posts/{cur_id}/{i}.png')
                    names += [f'static/images/posts/{cur_id}/{i}.png']
                news.imgs = ' '.join(names)
            if log.filename:
                im = Image.open(log)
                im.save(f'static/images/posts/{cur_id}/log.png')
                news.log = f'static/images/posts/{cur_id}/log.png'
            news.content = form.content.data
            news.ingr = form.ingr.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/profile/<int:id>', methods=['GET', 'POST'])
@login_required
def profile(id):
    db_sess = db_session.create_session()
    profile = db_sess.query(Profile).filter(Profile.id == id.first())
    return render_template("profile.html", profile=profile)


@app.route("/", methods=['GET', 'POST'])
def index():
    searchword = request.args.get('search')
    print(searchword)
    db_sess = db_session.create_session()
    # news = db_sess.query(News).filter(News.is_private != True)
    if current_user.is_authenticated:
        if searchword:
            print(1)
            news = db_sess.query(News).filter(
                (News.user == current_user) | (News.is_private != True), News.title.like(f'%{searchword}%'))
        else:
            news = db_sess.query(News).filter(
                (News.user == current_user) | (News.is_private != True))
    else:
        if searchword:
            news = db_sess.query(News).filter((News.is_private != True), News.title.like(f'%{searchword}%'))
        else:
            news = db_sess.query(News).filter(News.is_private != True)

    return render_template("index.html", news=news)


from flask import make_response


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def main():
    db_session.global_init("db/blogs.db")
    app.register_blueprint(news_api.blueprint)
    app.run()


if __name__ == '__main__':
    main()
