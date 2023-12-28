from flask import Flask, render_template, request, session, redirect, jsonify
import json
from flask_sqlalchemy import SQLAlchemy
import pymysql
import os
from werkzeug.utils import secure_filename
import math
with open('config.json', 'r') as c:
    parameters = json.load(c)["parameters"]
local_server = True


app=Flask(__name__)
app.secret_key = 'super-secret-key'

if (local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = parameters["local_uri"]
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = parameters["prod_uri"]

db = SQLAlchemy(app)

class Cart(db.Model):
    __tablename__ = 'cart'
    product_name = db.Column(db.String, nullable=False, primary_key=True)
    product_price = db.Column(db.Integer, nullable=False)
    product_company = db.Column(db.String(100), nullable=False)
    product_slug = db.Column(db.String(50), nullable=False)

class Products(db.Model):
    name = db.Column(db.String, nullable=False,primary_key=True)
    price=db.Column(db.Integer, nullable=False,)
    slug = db.Column(db.String(50), nullable=False)
    company =db.Column(db.String(100), nullable=False)
    disc = db.Column(db.String(200), nullable=False)
    new=db.Column(db.String(5),nullable=True)
    popular = db.Column(db.String(5), nullable=True)
    img_file = db.Column(db.String(100), nullable=False)


@app.route('/')
def home():
    products=Products.query.filter_by().all()
    return render_template("index.html",products=products)

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/allproducts')
def allproducts():
    return render_template('allproducts.html')

@app.route('/newarrivals')
def newarrivals():
    # Filter products where the 'new' attribute is True
    new_arrivals = Products.query.filter_by(new='TRUE').all()
    return render_template('newarrivals.html', new_arrivals=new_arrivals)

@app.route('/popularitems')
def popularitems():
    # Filter products where the 'popular' attribute is True
    popular_products = Products.query.filter_by(popular='TRUE').all()
    return render_template('popularitems.html', popular_products=popular_products)

@app.route('/cart')
def cart():
    return  render_template('cart.html')

@app.route('/checkout')
def checkout():
    return  render_template('checkout.html')

@app.route('/product/<string:product_slug>', methods=['GET'])
def product_route(product_slug):
    product = Products.query.filter_by(slug=product_slug).first()
    products=Products.query.filter_by().all()

    return render_template("product.html", product=product,products=products)

@app.route('/dashboard', methods=["GET", "POST"])
def dashboard():
    if 'user' in session and session['user'] == parameters["admin_username"]:
        products = Products.query.filter_by().all()
        return render_template('dashboard.html', parameters=parameters, products=products)

    if request.method == "POST":
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == parameters["admin_username"] and userpass == parameters['admin_password']):
            session['user'] = username
            products = Products.query.filter_by().all()
            return render_template('dashboard.html', parameters=parameters, products=products)

    return render_template("login.html", parameters=parameters)


@app.route('/edit/<string:name>', methods=['GET', 'POST'])
def edit(name):

    if 'user' in session and session['user'] == parameters["admin_username"]:
        if request.method == "POST":
            box_name = request.form.get('name')
            company = request.form.get('company')
            slug = request.form.get('slug')
            disc = request.form.get('content')
            img_file = request.form.get('img_file')
            price = request.form.get('price')
            popular = request.form.get('popular')
            new = request.form.get('new')

            if name == '0':
                product = Products(name=box_name,
                             slug=slug,
                             company=company,
                             disc=disc,
                             img_file=img_file,
                             price=price,
                             popular=popular,
                             new=new)
                db.session.add(product)
                db.session.commit()
            else:
                product = Products.query.filter_by(name=name).first()
                product.title = box_name
                product.slug = slug
                product.disc = disc
                product.price = price
                product.img_file = img_file
                product.popular = popular
                product.new = new
                db.session.commit()
                return redirect('/edit/' + name)

    product = Products.query.filter_by(name=name).first()
    return render_template('edit.html', parameters=parameters, product=product, name=name)


@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == parameters["admin_username"]:
        if request.method == "POST":
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully"


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route('/delete/<string:name>')
def delete(name):
    if 'user' in session and session['user'] == parameters["admin_username"]:
        product = Products.query.filter_by(name=name).first()
        db.session.delete(product)
        db.session.commit()
    return redirect('/dashboard')


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_name = request.form.get('product_name')
    product_price = request.form.get('product_price')
    product_company = request.form.get('product_company')
    product_slug = request.form.get('product_slug')

    # Check if 'product_price' is not None
    if product_price is None:
        return jsonify({'status': 'error', 'message': 'Product price cannot be null'})

    # Check if 'product_price' is a valid integer
    try:
        product_price = int(product_price)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid product price'})

    item = Cart(product_name=product_name, product_price=product_price, product_company=product_company, product_slug=product_slug)

    db.session.add(item)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Product added to cart'})


app.run(debug=True)