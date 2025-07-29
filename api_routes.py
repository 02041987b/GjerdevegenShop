import os
import uuid
from flask import Blueprint, jsonify, request, session, current_app, url_for
from werkzeug.utils import secure_filename
from models import db, Product, User, ContactMessage, Order, OrderItem, CartItem
from decorators import admin_required, login_required
from utils import validate_image

# --- КОНФИГУРАЦИЯ ---
api = Blueprint('api', __name__, url_prefix='/api')

def allowed_file(filename):
    """Проверяет, что расширение файла разрешено"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


# === API для ЗАГРУЗКИ ИЗОБРАЖЕНИЙ ===

@api.route('/admin/upload_image', methods=['POST'])
@admin_required
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400

    file = request.files['file']
    product_id = request.form.get('product_id')

    if not product_id or not product_id.isdigit():
        return jsonify({'error': 'Invalid Product ID'}), 400

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Генерируем уникальное имя: {product_id}_original_{filename}
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{product_id}_original.{ext}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Создаем папку если не существует
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)

        # Сохраняем файл
        file.save(filepath)

        # Обновляем запись в базе данных
        product = Product.query.get(product_id)
        if product:
            product.image_file = filename
            db.session.commit()
            return jsonify({
                'success': True,
                'filename': filename,
                'image_url': url_for('static', filename=f'images/{filename}')
            })

    return jsonify({'error': 'File type not allowed or upload failed'}), 400

# === API для Товаров (Products) ===

@api.route('/products', methods=['GET'])
@admin_required
def get_products():
    products = Product.query.order_by(Product.id).all()
    return jsonify([{'id': p.id, 'name': p.name, 'price': p.price, 'stock_quantity': p.stock_quantity, 'category': p.category, 'description': p.description, 'image_file': p.image_file} for p in products])

@api.route('/products', methods=['POST'])
@admin_required
def create_product():
    data = request.get_json()

    # Валидация обязательных полей
    if not all([data.get('name'), data.get('price')]):
        return jsonify({'error': 'Name and price are required'}), 400

    # Генерация имени изображения
    base_name = data['name'].lower().replace(' ', '_').replace("'", "")
    image_name = f"{base_name}.png"

    product = Product(
        name=data['name'],
        price=float(data['price']),
        category=data.get('category'),
        description=data.get('description'),
        stock_quantity=int(data.get('stock_quantity', 0)),
        image_file=image_name
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({
        'success': True,
        'product_id': product.id,
        'image_filename': image_name,
        'message': 'Upload image manually via FTP/SFTP'
    })

@api.route('/products/<int:id>', methods=['PUT'])
@admin_required
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.get_json()
    product.name = data.get('name', product.name)
    product.price = float(data.get('price', product.price))
    product.stock_quantity = int(data.get('stock_quantity', product.stock_quantity))
    product.category = data.get('category', product.category)
    product.description = data.get('description', product.description)
    product.image_file = data.get('image_file', product.image_file) or 'product_placeholder.png'
    db.session.commit()
    return jsonify({'message': 'Product updated successfully'})

@api.route('/products/<int:id>', methods=['DELETE'])
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})


# === API для Пользователей (Users) ===

@api.route('/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.order_by(User.id).all()
    return jsonify([{'id': u.id, 'username': u.username, 'email': u.email, 'role': u.role} for u in users])

@api.route('/users/<int:id>', methods=['DELETE'])
@admin_required
def delete_user(id):
    user_to_delete = User.query.get_or_404(id)
    if user_to_delete.id == session.get('user_id'):
        return jsonify({'message': 'Action not allowed: You cannot delete your own account.'}), 403
    db.session.delete(user_to_delete)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})

# === API для Сообщений (Messages) ===

@api.route('/messages', methods=['GET'])
@admin_required
def get_messages():
    messages = ContactMessage.query.order_by(ContactMessage.timestamp.desc()).all()
    return jsonify([{'id': msg.id, 'from': f"{msg.first_name} {msg.last_name}", 'email': msg.email, 'subject': msg.subject, 'message': msg.message, 'received_at': msg.timestamp.strftime('%Y-%m-%d %H:%M')} for msg in messages])

@api.route('/messages/<int:id>', methods=['DELETE'])
@admin_required
def delete_message(id):
    message = ContactMessage.query.get_or_404(id)
    db.session.delete(message)
    db.session.commit()
    return jsonify({'message': 'Message deleted successfully'})

# === API для Заказов (Orders) ===

@api.route('/orders', methods=['GET'])
@admin_required
def get_orders():
    orders = Order.query.order_by(Order.order_date.desc()).all()
    return jsonify([{'id': o.id, 'order_number': o.order_number, 'customer': f"{o.customer_name} {o.customer_lastname}", 'total': o.total_price, 'status': o.status, 'address': o.shipping_address, 'city': o.city, 'country': o.country, 'postal_code': o.postal_code} for o in orders])

@api.route('/orders/<int:id>', methods=['PUT'])
@admin_required
def update_order_address(id):
    order = Order.query.get_or_404(id)
    data = request.get_json()
    if 'shipping_address' in data:
        order.shipping_address = data['shipping_address']
        db.session.commit()
        return jsonify({'message': 'Shipping address updated successfully'})
    return jsonify({'error': 'No shipping_address provided'}), 400

@api.route('/orders/<int:id>', methods=['DELETE'])
@admin_required
def delete_order(id):
    order = Order.query.get_or_404(id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({'message': 'Order deleted successfully'})

# === API для Корзины (Cart) ===

@api.route('/cart/item/<int:item_id>', methods=['PUT'])
@login_required
def update_cart_item(item_id):
    """Обновляет количество товара в корзине."""
    item = CartItem.query.filter_by(id=item_id, user_id=session['user_id']).first_or_404()
    data = request.get_json()

    if 'quantity' in data:
        new_quantity = int(data['quantity'])
        if new_quantity > 0:
            item.quantity = new_quantity
        else:
            db.session.delete(item)

    db.session.commit()
    return jsonify({'success': True, 'message': 'Cart updated.'})

@api.route('/cart/item/<int:item_id>', methods=['DELETE'])
@login_required
def delete_cart_item(item_id):
    """Удаляет товар из корзины."""
    item = CartItem.query.filter_by(id=item_id, user_id=session['user_id']).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Item removed from cart.'})