
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
import flask
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.handlers.sha2_crypt import sha256_crypt
from functools import wraps
#Kullanıcı giriş decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu Sayfayı Görüntülemek İçin Giriş Yapınız!!","danger")
            return redirect(url_for("login"))

    return decorated_function

#Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators=[validators.Length(min = 4, max = 25)])
    username = StringField("Kullanıcı Adı", validators=[validators.Length(min = 5, max = 35)])
    email = StringField("Email Adresi", validators=[validators.Email(message="Lütfen Geçerli Bir Email Adresi Giriniz")])
    password = PasswordField("Parola:", validators=[validators.DataRequired(message="Lütfen Parola Belirleyin"),validators.EqualTo(fieldname = "confirm", message="Parolanız Uyuşmuyor..")])
    confirm = PasswordField("Parola Doğrula")

#Giriş Formu

class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")



app = Flask(__name__)
app.secret_key= "mnblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "mnblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql = MySQL(app)

#Ana Sayfa
@app.route("/")
def index():
    numbers = [1,2,3,4,5]

    return render_template("index.html",numbers = numbers)
#Hakkımda
@app.route("/about")
def about():
    return render_template("about.html")

#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))


    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2, (id,))

        mysql.connection.commit()

        
        return redirect(url_for("dashboard"))

    else:
        flash("Böyle bir makale yok ve ya bu işleme yetkiniz yok!!","danger")
        return redirect(url_for("index"))

#Makale Güncelle
@app.route("/edit/<string:id>",methods= ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":

        cursor = mysql.connection.cursor()
        sorgu = "Select * From articles where id = %s and  author = %s"

        result = cursor.execute(sorgu,(id,session["username"]))
        if result == 0:
            flash("Böyle bir makale yok ve ya işleme yetkiniz yok", "danger")
            return redirect(url_for("index"))

        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)

    else:
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update articles Set title = %s, content = %s where id = %s"
        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()
        flash("Makale Güncellendi!","success")

        return redirect(url_for("dashboard"))



#Makale Sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles"

    result = cursor.execute(sorgu)

    if result > 0:
        articles= cursor.fetchall()

        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")


#Kontrol Paneli Giriş
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()

        return render_template("dashboard.html", articles = articles)

    else:
        return render_template("dashboard.html")
#Kayıt Olma
@app.route("/register",methods = ["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email  = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        
        cursor.close()

        flash("Başarıyla Kayıt Oldunuz...","success")

        return redirect(url_for("login"))
        
    else:

        return render_template("register.html", form = form)

#Giriş Yapma

@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu,(username,))

        if result > 0:
            
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Giriş Yapıldı.","success")
                session["logged_in"] = True
                session["username"] = username



                return redirect(url_for("index"))
            else:
                flash("Parola Hatalı.","danger")

                return redirect(url_for("login"))
        else:
            flash("Kullanıcı Adı Bulunmuyor...","danger")
            
            return redirect(url_for("login"))



    return render_template("login.html",form = form)

#Detay Sayfası
@app.route("/article/<string:id>")
def detail(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles where id = %s"

    result = cursor.execute(sorgu, (id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article = article)
    else:
        return render_template("article.html")

#ÇıkısYapma
@app.route("/logout")
def logout():
    session.clear()
    flash("Çıkış Yapıldı","danger")
    return redirect(url_for("index"))


#Makale Ekleme

@app.route("/addarticle",methods= ["GET","POST"])
def addarticle():

    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))
        
        mysql.connection.commit()
        
        cursor.close()
        flash("Makale Başarıyla Oluşturuldu","success")
        return redirect(url_for("dashboard"))
    else:
        pass



    return render_template("addarticle.html",form = form)

#Makale Form
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min= 5, max= 100)])
    content = TextAreaField("Makale İçeriği", validators=[validators.Length(min=10)])


#Arama URL
@app.route("/search",methods = ["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()
        
        sorgu = "Select * from articles where title like '%" + keyword + "%' "
        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aranan Kelimeye uygun makale mevcut değil","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()

            return render_template("articles.html",articles = articles)

#Profil 
@app.route("/profile/<string:username>")

def profile(username):
    cursor = mysql.connection.cursor()

    sorgu = "Select * From users where username = %s "
    result = cursor.execute(sorgu,(username,))
    if result > 0:
        user = cursor.fetchone()
        return render_template("profile.html", user = user)
    else:
    
        return render_template("profile.html")

#Profiller
@app.route("/profile")
def profiles():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From users"

    result = cursor.execute(sorgu)

    if result > 0:

        users = cursor.fetchall()
        return render_template("profiles.html",users = users)
    else:
        return redirect(url_for("index"))
    


#Chat
@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html")

    
if __name__ == "__main__":
    app.run(debug=True)
    


