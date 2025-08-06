from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from payments import process_evc, process_zaad, process_sahal, process_edahab

app = Flask(__name__)

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///takeapp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), default='pending')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)

app.secret_key = os.environ.get('SECRET_KEY', 'takeapp_secret')

# Helper: admin login required
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Bogga hore
@app.route('/')
def index():
    return render_template('index.html')

# CRUD API for Products
@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.price, 'image_url': p.image_url} for p in products])

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.json
    product = Product(name=data['name'], price=data['price'], image_url=data.get('image_url'))
    db.session.add(product)
    db.session.commit()
    return jsonify({'message': 'Alaab waa la abuuray', 'id': product.id}), 201

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({'id': product.id, 'name': product.name, 'price': product.price, 'image_url': product.image_url})

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.json
    product.name = data.get('name', product.name)
    product.price = data.get('price', product.price)
    product.image_url = data.get('image_url', product.image_url)
    db.session.commit()
    return jsonify({'message': 'Alaab waa la cusbooneysiiyay'})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Alaab waa la tirtiray'})

# CRUD API for Orders
@app.route('/api/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return jsonify([
        {'id': o.id, 'customer_name': o.customer_name, 'customer_phone': o.customer_phone, 'product_id': o.product_id, 'quantity': o.quantity, 'status': o.status}
        for o in orders
    ])

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    order = Order(
        customer_name=data['customer_name'],
        customer_phone=data['customer_phone'],
        product_id=data['product_id'],
        quantity=data.get('quantity', 1),
        status=data.get('status', 'pending')
    )
    db.session.add(order)
    db.session.commit()
    return jsonify({'message': 'Dalab waa la abuuray', 'id': order.id}), 201

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify({'id': order.id, 'customer_name': order.customer_name, 'customer_phone': order.customer_phone, 'product_id': order.product_id, 'quantity': order.quantity, 'status': order.status})

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.json
    order.customer_name = data.get('customer_name', order.customer_name)
    order.customer_phone = data.get('customer_phone', order.customer_phone)
    order.product_id = data.get('product_id', order.product_id)
    order.quantity = data.get('quantity', order.quantity)
    order.status = data.get('status', order.status)
    db.session.commit()
    return jsonify({'message': 'Dalab waa la cusbooneysiiyay'})

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({'message': 'Dalab waa la tirtiray'})

# CRUD API for Payments
@app.route('/api/payments', methods=['POST'])
def make_payment():
    data = request.json
    method = data.get('method')
    amount = data.get('amount')
    phone = data.get('phone')
    if not all([method, amount, phone]):
        return jsonify({'error': 'Xogta lacag-bixinta waa dhammaystirnaan la’'}, 400)
    if method == 'evc':
        result = process_evc(amount, phone)
    elif method == 'zaad':
        result = process_zaad(amount, phone)
    elif method == 'sahal':
        result = process_sahal(amount, phone)
    elif method == 'edahab':
        result = process_edahab(amount, phone)
    else:
        return jsonify({'error': 'Nooca lacag-bixinta lama aqoonsan'}), 400
    return jsonify(result)

# Admin panel
@app.route('/admin')
def admin():
    return render_template('admin.html')

# Admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password) and user.is_admin:
            session['admin_logged_in'] = True
            session['admin_username'] = user.username
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Magaca ama erayga sirta ah waa qalad!')
    return render_template('admin_login.html')

# Admin logout
@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

# Admin dashboard
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    products = Product.query.all()
    orders = Order.query.all()
    return render_template('admin_dashboard.html', products=products, orders=orders)

# Admin: add product
@app.route('/admin/products/add', methods=['POST'])
@admin_required
def admin_add_product():
    name = request.form['name']
    price = request.form['price']
    image_url = request.form.get('image_url')
    product = Product(name=name, price=price, image_url=image_url)
    db.session.add(product)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# Admin: delete product
@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# Admin: update product (simple)
@app.route('/admin/products/update/<int:product_id>', methods=['POST'])
@admin_required
def admin_update_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.name = request.form['name']
    product.price = request.form['price']
    product.image_url = request.form.get('image_url')
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# Admin: update order status
@app.route('/admin/orders/update/<int:order_id>', methods=['POST'])
@admin_required
def admin_update_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = request.form['status']
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)