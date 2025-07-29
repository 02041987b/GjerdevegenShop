GjerdevegenShop - E-commerce Platform
📌 Table of Contents
Project Description

Features

Technologies Used

Installation

Configuration

API Endpoints

Database Models

Error Handling

Project Structure

License

📝 Project Description
GjerdevegenShop is a comprehensive e-commerce platform developed as part of the CS50 final project. The application provides a complete online shopping experience with user authentication, product catalog, shopping cart functionality, order processing, and an administrative dashboard.

Key aspects:

Modern responsive design with mobile-first approach

Role-based access control (User/Admin)

RESTful API for frontend-backend communication

Secure payment processing (simulated)

Comprehensive error handling

✨ Features
User Features
✅ User registration and authentication

✅ Product browsing with categories

✅ Advanced product search

✅ Shopping cart management

✅ Checkout process with order confirmation

✅ Order history tracking

✅ User profile management

Admin Features
🔒 Admin dashboard with analytics

🔒 Product management (CRUD)

🔒 User management

🔒 Order processing and status updates

🔒 Contact message handling

Technical Features
🛡️ CSRF protection

🔐 Password hashing

📦 Session management

📊 Database migrations

📱 Responsive design

🎨 Custom error pages (403, 404, 500)

💻 Technologies Used
Backend
Python 3 - Primary programming language

Flask - Web framework

SQLAlchemy - ORM for database interactions

Jinja2 - Templating engine

Werkzeug - Security and utility functions

Frontend
HTML5 - Markup

CSS3 - Styling

JavaScript - Client-side functionality

Bootstrap 5 - Responsive framework

jQuery - DOM manipulation

Font Awesome - Icons

Database
SQLite (Development)

PostgreSQL (Production-ready)

🚀 Installation
Prerequisites
Python 3.8+

pip package manager

Virtual environment (recommended)

Setup Instructions
Clone the repository:

bash
git clone https://github.com/yourusername/gjerdevegenshop.git
cd gjerdevegenshop
Create and activate virtual environment:

bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
Install dependencies:

bash
pip install -r requirements.txt
Initialize the database:

bash
flask init-db
Run the development server:

bash
flask run
Access the application at http://localhost:5000

⚙️ Configuration
The application can be configured via environment variables or directly in app.py:

python
# Basic configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/site.db'
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'images')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_FILE_SIZE'] = 2 * 1024 * 1024  # 2MB
For production, consider:

Using environment variables

Setting up a proper database (PostgreSQL/MySQL)

Configuring proper secret keys

Enabling HTTPS

🔌 API Endpoints
The application provides a RESTful API under /api prefix:

Products
GET /api/products - List all products

POST /api/products - Create new product

PUT /api/products/<id> - Update product

DELETE /api/products/<id> - Delete product

Users
GET /api/users - List all users (admin only)

DELETE /api/users/<id> - Delete user (admin only)

Orders
GET /api/orders - List all orders (admin only)

PUT /api/orders/<id> - Update order status (admin only)

Cart
PUT /api/cart/item/<item_id> - Update cart item quantity

DELETE /api/cart/item/<item_id> - Remove item from cart

🗃️ Database Models
Key models and their relationships:

Diagram
Code
erDiagram
    User ||--o{ CartItem : has
    User ||--o{ Order : places
    Product ||--o{ CartItem : in
    Product ||--o{ OrderItem : in
    Order ||--o{ OrderItem : contains
Detailed model specifications:

User
id: Primary key

username: Unique identifier

email: Unique contact

password_hash: Securely stored password

role: User/Admin permissions

Relationships: CartItems, Orders

Product
id: Primary key

name: Product title

price: Product cost

stock_quantity: Available inventory

category: Product classification

description: Detailed information

image_file: Product image reference

Order
id: Primary key

order_number: Unique identifier

user_id: Customer reference

total_price: Order amount

status: Processing/Paid/Shipped/etc.

Relationships: User, OrderItems

🚨 Error Handling
Custom error pages for:

403 Forbidden - Spooky animated page for unauthorized access

404 Not Found - Friendly page for missing resources

500 Server Error - Technical error page with gears animation

Error handling includes:

Database transaction rollback

User-friendly error messages

Logging for technical errors

Graceful degradation

📂 Project Structure
text
gjerdevegenshop/
├── static/               # Static files
│   ├── css/              # Stylesheets
│   ├── images/           # Product images and assets
│   └── js/               # JavaScript files
├── templates/            # HTML templates
│   ├── admin/            # Admin interface
│   ├── errors/           # Error pages
│   └── *.html            # Main templates
├── app.py                # Main application file
├── api_routes.py         # API endpoints
├── models.py             # Database models
├── decorators.py         # Authentication decorators
├── utils.py              # Utility functions
├── requirements.txt      # Dependencies
└── README.md             # This file
📜 License
This project is licensed under the MIT License - see the LICENSE file for details.
