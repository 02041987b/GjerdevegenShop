
import os
import uuid
from datetime import datetime
from flask import (Flask, render_template, request, redirect, url_for, session, jsonify, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, func
from models import Order, OrderItem
from flask import current_app



# 1. Инициализация и Конфигурация
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-and-complex-key-for-dev'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'images')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_FILE_SIZE'] = 2 * 1024 * 1024  # 2MB



# 2. Подключение компонентов
try:
    from models import db, User, Product, CartItem, ContactMessage
    from decorators import login_required, admin_required
    from api_routes import api as api_blueprint

    db.init_app(app)
    app.register_blueprint(api_blueprint)
except ImportError:
    pass # Позволяем приложению работать, даже если какие-то файлы еще не созданы

# 3. Контекстные процессоры и обработчики ошибок
@app.context_processor
def inject_globals():
    cart_count = 0
    if 'user_id' in session:
        try:
            count = db.session.query(func.sum(CartItem.quantity)).filter_by(user_id=session['user_id']).scalar() or 0
            cart_count = int(count)
        except Exception:
            cart_count = 0
    return {'cart_items_count': cart_count, 'current_year': datetime.now().year}

@app.errorhandler(403)
def forbidden(e): return render_template('errors/403.html'), 403
@app.errorhandler(404)
def page_not_found(e): return render_template('errors/404.html'), 404
@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# 4. Основные маршруты
@app.route('/')
def index():
    FEATURED_PRODUCTS_COUNT = 6
    products = Product.query.order_by(func.random()).limit(FEATURED_PRODUCTS_COUNT).all()
    return render_template('index.html', products=products)

@app.route('/admin/orders')
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('admin_dashboard.html', orders=orders)

@app.route('/admin/orders/<int:order_id>')
@admin_required
def admin_order_details(order_id):
    order = Order.query.options(
        joinedload(Order.items)
    ).options(
        joinedload(Order.user)
    ).get_or_404(order_id)
    return render_template('admin_order_details.html', order=order)

@app.route('/admin/orders/update-status/<int:order_id>', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status:
        order.status = new_status
        db.session.commit()
        flash('Order status updated successfully!', 'success')
    return redirect(url_for('admin_order_details', order_id=order_id))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not all([first_name, last_name, email, message]):
            flash('Please fill out all required fields.', 'danger')
            return redirect(url_for('contact'))

        new_message = ContactMessage(
            first_name=first_name,
            last_name=last_name,
            email=email,
            subject=subject,
            message=message
        )
        db.session.add(new_message)
        db.session.commit()

        flash('Thank you for your message!', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')


@app.route('/admin/add_product', methods=['POST'])
@admin_required
def add_product():
    data = request.get_json()

    # Генерация имени файла на основе названия товара
    image_name = f"{data['name'].lower().replace(' ', '_')}.png"

    product = Product(
        name=data['name'],
        price=data['price'],
        category=data.get('category'),
        description=data.get('description'),
        stock_quantity=data.get('stock_quantity', 0),
        image_file=image_name  # Автоматическое назначение
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({
        'success': True,
        'product_id': product.id,
        'image_name': image_name  # Возвращаем имя для ручной загрузки
    })


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.options(joinedload(CartItem.product)).filter_by(user_id=session['user_id']).all()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('index'))

    # Проверка наличия товаров
    for item in cart_items:
        if not item.product or item.product.stock_quantity < item.quantity:
            flash(f'Product {item.product.name if item.product else "Unknown"} is out of stock or quantity unavailable', 'danger')
            return redirect(url_for('view_cart'))

    total_price = sum(item.product.price * item.quantity for item in cart_items if item.product)

    if request.method == 'POST':
        try:
            # 1. Получаем данные из формы
            required_fields = ['first_name', 'last_name', 'address', 'city', 'postal_code', 'country', 'phone', 'email']
            form_data = {field: request.form.get(field) for field in required_fields}

            # Проверка обязательных полей
            if not all(form_data.values()):
                flash('Please fill all required fields.', 'danger')
                return redirect(url_for('checkout'))

            # 2. Создаем новый заказ
            new_order = Order(
                order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
                user_id=session['user_id'],
                total_price=total_price,
                status='Processing',
                payment_method=request.form.get('payment_method', 'Credit Card'),
                customer_name=f"{form_data['first_name']} {form_data['last_name']}",
                customer_email=form_data['email'],
                customer_phone=form_data['phone'],
                shipping_address=f"{form_data['address']}, {form_data['city']}, {form_data['postal_code']}, {form_data['country']}",
                order_date=datetime.utcnow()
            )

            db.session.add(new_order)
            db.session.flush()  # Получаем ID заказа

            # 3. Переносим товары из корзины в заказ
            for item in cart_items:
                if item.product.stock_quantity < item.quantity:
                    raise ValueError(f'Not enough stock for {item.product.name}')

                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price_per_item=item.product.price,
                    product_name=item.product.name,
                    product_image=item.product.image_file
                )

                # 4. Уменьшаем количество товара на складе
                item.product.stock_quantity -= item.quantity

                db.session.add(order_item)

            # 5. Очищаем корзину
            CartItem.query.filter_by(user_id=session['user_id']).delete()

            db.session.commit()

            # Отправка email (заглушка для реализации)
            # send_order_confirmation_email(new_order)

            flash('Your order has been placed successfully!', 'success')
            return redirect(url_for('order_details', order_id=new_order.id))

        except ValueError as e:
            db.session.rollback()
            flash(str(e), 'danger')
            return redirect(url_for('view_cart'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while processing your order.', 'danger')
            current_app.logger.error(f"Order processing error: {str(e)}")
            return redirect(url_for('checkout'))

    return render_template('checkout.html',
                         cart_items=cart_items,
                         total_price=total_price,
                         user=User.query.get(session['user_id']))

@app.route('/orders')
@login_required
def order_history():
    orders = Order.query.filter_by(user_id=session['user_id'])\
                       .order_by(Order.order_date.desc())\
                       .all()
    return render_template('order_history.html', orders=orders)

@app.route('/orders/<int:order_id>')
@login_required
def order_details(order_id):
    order = Order.query.filter_by(id=order_id, user_id=session['user_id']).first_or_404()
    return render_template('order_details.html', order=order)



@app.route('/catalog')
def catalog_index():

    categories = db.session.query(Product.category).distinct().all()
    category_names = [category[0] for category in categories]
    return render_template('catalog.html', categories=category_names)

@app.route('/catalog/<string:category_name>')
def category_view(category_name):

    products_in_category = Product.query.filter_by(category=category_name).all()
    return render_template('category_products.html', products=products_in_category, category_name=category_name)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if not all([username, email, password]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/cart')
@login_required
def view_cart():
    cart_items = CartItem.query.options(joinedload(CartItem.product)).filter_by(user_id=session['user_id']).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items if item.product)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart_item = CartItem.query.filter_by(user_id=session['user_id'], product_id=product.id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(user_id=session['user_id'], product_id=product.id, quantity=1)
        db.session.add(cart_item)
    db.session.commit()
    new_count = db.session.query(func.sum(CartItem.quantity)).filter_by(user_id=session['user_id']).scalar() or 0
    return jsonify({'success': True, 'message': f'Added {product.name} to cart!', 'cart_items_count': int(new_count)})

@app.route('/product/<int:product_id>')
def product(product_id):
    product_item = Product.query.get_or_404(product_id)
    return render_template('product_page.html', product=product_item)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    products = []
    if query:
        search_term = f"%{query}%"
        products = Product.query.filter(or_(Product.name.ilike(search_term))).all()
    return render_template('search_results.html', products=products, query=query)

@app.route('/profile')
@login_required
def user_profile():
    user = User.query.get_or_404(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/admin')
@admin_required
def admin_dashboard():
    # Получаем все заказы с информацией о пользователе
    orders = db.session.query(
        Order,
        User.username
    ).join(
        User, Order.user_id == User.id
    ).order_by(
        Order.order_date.desc()
    ).all()

    products = Product.query.all()
    users = User.query.all()
    messages = ContactMessage.query.order_by(ContactMessage.timestamp.desc()).all()

    return render_template(
        'admin_dashboard.html',
        orders=orders,
        products=products,
        users=users,
        messages=messages
    )


@app.cli.command("init-db")
def init_db_command():
    with app.app_context():
        db.create_all()
    print("Database tables created.")

@app.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    try:
        # Получаем данные из формы
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        address = request.form.get('address')
        city = request.form.get('city')
        country = request.form.get('country')
        postal_code = request.form.get('postal_code')
        phone_number = request.form.get('phone_number')

        # Проверяем обязательные поля
        if not all([first_name, last_name, address, city, country, postal_code, phone_number]):
            flash('Please fill all required fields', 'danger')
            return redirect(url_for('checkout'))

        # Получаем товары из корзины
        cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
        if not cart_items:
            flash('Your cart is empty', 'warning')
            return redirect(url_for('checkout'))

        # Создаем заказ (убедитесь, что все поля модели Order заполнены)
        order = Order(
            order_number=f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            user_id=session['user_id'],
            total_price=sum(item.product.price * item.quantity for item in cart_items),
            status='Paid',
            customer_name=first_name,
            customer_lastname=last_name,  # Это обязательное поле
            shipping_address=address,
            postal_code=postal_code,
            city=city,
            country=country,
            phone_number=phone_number
        )

        db.session.add(order)
        db.session.flush()  # Получаем ID заказа

        # Добавляем товары в заказ
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_per_item=item.product.price
            )
            db.session.add(order_item)
            # Уменьшаем количество на складе
            item.product.stock_quantity -= item.quantity

        # Очищаем корзину
        CartItem.query.filter_by(user_id=session['user_id']).delete()

        db.session.commit()

        return redirect(url_for('order_details', order_id=order.id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Order processing error: {str(e)}")
        flash('Error processing your order. Please try again.', 'danger')
        return redirect(url_for('checkout'))



if __name__ == '__main__':
    app.run(debug=True)