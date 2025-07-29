#!/usr/bin/env python3
from app import app
from models import db
from datetime import datetime
import inspect

def print_full_data(model):
    """Выводит полную информацию о всех записях модели"""
    with app.app_context():
        items = model.query.order_by(model.id).all()
        print(f"\n{'='*50}")
        print(f"=== FULL DATA FOR {model.__name__.upper()} ===")
        print(f"Total records: {len(items)}")
        print(f"Displaying ALL records with COMPLETE details")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}\n")

        # Получаем все поля модели
        columns = [column.key for column in model.__table__.columns]

        for item in items:
            print(f"\n■ {model.__name__} ID: {item.id} {'■'*30}")

            # Выводим все основные поля
            for column in columns:
                value = getattr(item, column)

                # Форматирование специальных типов
                if isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif column == 'price':
                    value = f"${value:.2f}"

                print(f"  {column:20}: {value}")

            # Выводим отношения (если есть)
            print("\n  Relationships:")
            relationships = inspect.getmembers(model, lambda x: isinstance(x, db.RelationshipProperty))
            for rel_name, _ in relationships:
                try:
                    related = getattr(item, rel_name)
                    if related is None:
                        print(f"  {rel_name:20}: None")
                    elif isinstance(related, list):
                        print(f"  {rel_name:20}: [{len(related)} items]")
                        for i, rel_item in enumerate(related[:3], 1):
                            print(f"    {i}. {rel_item}")
                        if len(related) > 3:
                            print(f"    ... and {len(related)-3} more")
                    else:
                        print(f"  {rel_name:20}: {related}")
                except Exception as e:
                    print(f"  {rel_name:20}: [Error loading: {str(e)}]")

            print("-"*50)

def get_available_models():
    """Возвращает список доступных моделей с проверкой"""
    available_models = []
    possible_models = ['Product', 'User', 'Order', 'CartItem', 'ContactMessage']

    for model_name in possible_models:
        try:
            model = getattr(__import__('models', fromlist=[model_name]), model_name)
            if hasattr(model, '__table__'):  # Проверяем, что это настоящая модель SQLAlchemy
                available_models.append((model_name, model))
        except AttributeError:
            continue

    return available_models

def show_menu(available_models):
    """Интерактивное меню с нумерацией"""
    print("\n" + "="*50)
    print("=== DATABASE INSPECTOR ===")
    print("="*50)
    print("\nAvailable Tables (Full Details):")

    for idx, (name, _) in enumerate(available_models, 1):
        print(f"{idx}. {name}")

    print("\n0. Exit")
    print("="*50)

    while True:
        try:
            choice = input("\nSelect table (number) >> ")
            if choice == '0':
                return None
            choice = int(choice)
            if 1 <= choice <= len(available_models):
                return available_models[choice-1][1]
            print("Invalid number! Please try again.")
        except ValueError:
            print("Please enter a valid number!")

def main():
    available_models = get_available_models()

    if not available_models:
        print("No database models found!")
        return

    while True:
        selected_model = show_menu(available_models)
        if not selected_model:
            print("\nExiting...")
            break

        print_full_data(selected_model)
        input("\nPress Enter to return to menu...")

if __name__ == '__main__':
    main()