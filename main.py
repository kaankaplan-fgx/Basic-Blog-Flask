from flask import Flask,render_template,redirect,request,url_for,flash,session
from wtforms import Form, BooleanField, StringField, PasswordField, validators, TextAreaField
from flask_mysqldb import MySQL
from passlib.hash import pbkdf2_sha256
import time

app = Flask(__name__)
mysql = MySQL(app)
app.secret_key = "kaankaplan"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "users"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


class RegistrationForm(Form):
    name = StringField('İsim Soyisim', validators= [validators.Length(min=4, max=25,message="İsim 3 ila 25 karakter arasında olmalıdır"),
     validators.DataRequired(message="")])
    username = StringField("Kullanıcı Adı", validators=[validators.DataRequired(message=""), validators.length(min=6,max=12,
    message="Kullanıcı adı 6 ila 12 karakter arasında olmalıdır!")])
    email = StringField("E-Mail", validators=[validators.DataRequired(message=""),validators.Email(message="Lütfen Geçerli Bir E-Mail Adresi Giriniz")])
    password = PasswordField("Parola", validators=[validators.DataRequired(message=""),validators.length(min=6, max=28,
    message="Parola 6 ile 25 Karakter Arasında olması Gerekir!")])


class LoginForm(Form):
    username = StringField("Kullanıcı Adı ", validators=[validators.DataRequired(message="")])
    password = PasswordField(" Parola ", validators=[validators.DataRequired(message="")])


class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators=[validators.DataRequired(message=""), validators.length(min=2,max=100)])
    content = TextAreaField("Makale İçeriği", validators=[validators.DataRequired(message=""), validators.length(min=100,max=1000)])


@app.route("/addarticle", methods=['GET', 'POST'])
def addarticle():
    form = ArticleForm(request.form)
    form.validate()
    if request.method == 'POST' and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        add_article = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(add_article,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale Başarıyla Kaydedildi", "success")
        return redirect(url_for("dashboard"))
    else:
        

        return render_template("addarticle.html", form=form)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/anasayfa")
def anasayfa():
    on = 30
    liste = [10,11,12,13,14]
    return render_template("index.html", on = on, liste = liste)

@app.route("/hakkimizda")
def hakkımızda():
    return render_template("hakkimizda.html")

@app.route("/makaleler")
def makaleler():
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles"
    cursor.execute(sorgu)
    articles = cursor.fetchall()

    return render_template("makaleler.html",articles=articles)


@app.route("/makaleler/<string:id>")    
def articles_detail(id):
    cursor = mysql.connection.cursor()
    sorgu = "SELECT * FROM articles WHERE id=%s"
    result = cursor.execute(sorgu,(id,))
    if result >0:
        articles = cursor.fetchall()
        return render_template("article_detail.html",articles=articles)
    else:
        flash("Bu makale bulunamadı!","info")

        return render_template("article_detail.html")

@app.route("/dashboard")
def dashboard():
    if session:
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles WHERE author=%s"
        cursor.execute(sorgu,(session["username"],))

        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else:
        flash("Lütfen giriş yapınız.", "secondary")
        time.sleep(2)
        return redirect(url_for("login"))

    



@app.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla Çıkış Yapıldı", "success")
    return redirect(url_for("anasayfa"))


@app.route("/login", methods = ['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    form.validate()

    if request.method == "POST" and form.validate():
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users WHERE username = %s"
        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]

            if pbkdf2_sha256.verify(password_entered,real_password):
                session["logged_in"] = True
                session["username"] = username
                flash("Başarıyla giriş yapıldı.", "success")
                return redirect(url_for("anasayfa"))
            else:
                flash("Kullanıcı adı veya parola hatalı", "danger")
                return redirect(url_for("login"))

        else:
            flash("Kullanıcı adı veya parola hatalı.","danger")
            return redirect(url_for("login"))
    else:
        pass



    return render_template("login.html", form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    form.validate()



    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = pbkdf2_sha256.hash(form.password.data)

        cursor = mysql.connection.cursor()
        register = "INSERT INTO users(name,username,email,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(register,(name,username,email,password))
        mysql.connection.commit()
        cursor.close()
        flash("Kayıt İşleni Başarılı", "success")

        return redirect(url_for("anasayfa"))
    else:
        return render_template("register.html", form = form)



@app.route("/delete/<string:id>")   
def delete(id):
    if session:
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM articles WHERE author =%s and id=%s"
        result = cursor.execute(sorgu,(session["username"],id))
        
        if result>0:
            sorgu2="DELETE FROM articles WHERE id=%s"
            cursor.execute(sorgu2,(id,))
            mysql.connection.commit()
            cursor.close()
            flash("Silme İşlemi Başarıyla Tamamlandı","info")
            return redirect(url_for("dashboard"))
        else:
            flash("Yetkisiz İşlem!","danger")
            return redirect(url_for("anasayfa"))

    else:
        flash("Yetkisiz İşlem!","danger")
        return redirect(url_for("anasayfa"))


@app.route("/update/<string:id>",methods=["POST","GET"])
def update(id):
    if session:
        if request.method =="GET":
            cursor = mysql.connection.cursor()
            sorgu = "SELECT * FROM articles WHERE id=%s and author=%s"
            result = cursor.execute(sorgu,(id,session["username"]))

            if result>0:
                form = ArticleForm()
                article = cursor.fetchone()
                form.title.data = article["title"]
                form.content.data = article["content"]
                return render_template("update.html",form = form)
            else:
                flash("Yetkisiz İşlem!","danger")
                return redirect(url_for("anasayfa"))
           

            

        else:
            form = ArticleForm(request.form)
            new_title = form.title.data
            new_content = form.content.data
            cursor = mysql.connection.cursor()
            update = "UPDATE articles SET title=%s,content=%s WHERE id=%s"
            cursor.execute(update,(new_title,new_content,id))
            mysql.connection.commit()
            cursor.close()
            flash("Makale Başarıyla Güncellendi","info")
            return redirect(url_for("dashboard"))
    else:
        flash("Yetkisiz İşlem!","danger")
        return redirect(url_for("anasayfa"))




if __name__ == "__main__":
    app.run(debug=True)