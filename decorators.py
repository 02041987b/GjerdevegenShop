from functools import wraps
from flask import session, flash, redirect, url_for, abort

def login_required(f):
    """
    Декоратор для проверки, вошел ли пользователь в систему.
    Если нет - перенаправляет на главную страницу с сообщением.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            #  Перенаправляем на главную страницу
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Декоратор для проверки прав администратора."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Декоратор login_required должен вызываться перед этим,
        # поэтому мы можем быть уверены, что session['role'] существует.
        if session.get('role') != 'admin':
            abort(403)  # Выдаем ошибку "Доступ запрещен"
        return f(*args, **kwargs)
    return decorated_function