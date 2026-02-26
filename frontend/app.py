from flask import Flask, render_template, abort, session, redirect, url_for, flash, request
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24) # Required for sessions

# URL of the Django backend API
API_BASE_URL = 'http://127.0.0.1:8000/api'

@app.route('/')
def index():
    try:
        # Fetch products from Django API
        response = requests.get(f'{API_BASE_URL}/products/')
        response.raise_for_status()
        products = response.json()
    except requests.RequestException as e:
        print(f"Error fetching products: {e}")
        products = []  # Fallback to empty list if API is down
        
    return render_template('index.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    try:
        response = requests.get(f'{API_BASE_URL}/products/{product_id}/')
        if response.status_code == 404:
            abort(404)
        response.raise_for_status()
        product = response.json()
    except requests.RequestException as e:
        print(f"Error fetching product details: {e}")
        abort(500)
        
    return render_template('product_detail.html', product=product)

@app.context_processor
def inject_global_data():
    cart = session.get('cart', {})
    cart_count = sum(cart.values())
    
    # Fetch categories for the navbar dropdown
    try:
        response = requests.get(f'{API_BASE_URL}/categories/')
        categories = response.json() if response.status_code == 200 else []
    except requests.RequestException:
        categories = []
        
    user = session.get('user', None)

    return dict(cart_count=cart_count, categories=categories, current_user=user)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product_id_str = str(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    if 'cart' not in session:
        session['cart'] = {}
        
    cart = session['cart']
    cart[product_id_str] = cart.get(product_id_str, 0) + quantity
    session.modified = True
    
    flash('Added to cart!', 'success')
    return redirect(request.referrer or url_for('index'))

@app.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    product_id_str = str(product_id)
    if 'cart' in session and product_id_str in session['cart']:
        del session['cart'][product_id_str]
        session.modified = True
        flash('Item removed from cart.', 'info')
        
    return redirect(url_for('view_cart'))

@app.route('/cart/update/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    product_id_str = str(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    if 'cart' in session and product_id_str in session['cart']:
        if quantity > 0:
            session['cart'][product_id_str] = quantity
        else:
            del session['cart'][product_id_str]
        session.modified = True
        flash('Cart updated.', 'success')
        
    return redirect(url_for('view_cart'))

@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    cart_items = []
    cart_total = 0
    
    # Fetch details for each product in cart from API
    for product_id, quantity in cart.items():
        try:
            response = requests.get(f'{API_BASE_URL}/products/{product_id}/')
            if response.status_code == 200:
                product = response.json()
                subtotal = float(product['price']) * quantity
                cart_total += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
            else:
                # Remove if product no longer exists
                del session['cart'][product_id]
                session.modified = True
        except requests.RequestException:
            pass # Keep it simple, ignore fetch errors for individual items here

    return render_template('cart.html', cart_items=cart_items, cart_total=cart_total)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty!', 'error')
        return redirect(url_for('view_cart'))

    if request.method == 'POST':
        # 1. Collect Form Data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        address = request.form.get('address')
        city = request.form.get('city')
        postal_code = request.form.get('postal_code')

        # 2. Build the payload for Django API
        items_payload = []
        for product_id, quantity in cart.items():
            items_payload.append({
                "product_id": int(product_id),
                "quantity": int(quantity),
                "price": "0.00" # Let backend or frontend calculate this appropriately, backend relies on this right now
            })

        # We actually need prices for the payload. Let's fetch the cart again to get current prices.
        # In a real app, the backend might just take product_id and calculate the price itself to prevent tampering.
        cart_total = 0
        valid_items_payload = []
        for item in items_payload:
            try:
                response = requests.get(f'{API_BASE_URL}/products/{item["product_id"]}/')
                if response.status_code == 200:
                    product = response.json()
                    item['price'] = product['price']
                    cart_total += float(product['price']) * item['quantity']
                    valid_items_payload.append(item)
            except requests.RequestException:
                pass
        
        order_payload = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "address": address,
            "city": city,
            "postal_code": postal_code,
            "items": valid_items_payload,
            "total_amount": str(cart_total)
        }

        # 3. Send to Django
        try:
            response = requests.post(f'{API_BASE_URL}/orders/checkout/', json=order_payload)
            if response.status_code == 201:
                # Success! Clear cart and redirect
                session.pop('cart', None)
                session.modified = True
                order_data = response.json()
                return redirect(url_for('order_success', order_id=order_data['id']))
            else:
                flash(f'Error processing order: {response.text}', 'error')
        except requests.RequestException as e:
            flash('Could not connect to the payment server. Please try again later.', 'error')

    # GET Request: calculate total for display
    cart_total = 0
    for product_id, quantity in cart.items():
        try:
            res = requests.get(f'{API_BASE_URL}/products/{product_id}/')
            if res.status_code == 200:
                cart_total += float(res.json()['price']) * quantity
        except requests.RequestException:
            pass

    return render_template('checkout.html', cart_total=cart_total)

@app.route('/shop')
def shop():
    category_id = request.args.get('category')
    search_query = request.args.get('search')
    
    params = {}
    if category_id:
        params['category'] = category_id
    if search_query:
        params['search'] = search_query
        
    try:
        response = requests.get(f'{API_BASE_URL}/products/', params=params)
        response.raise_for_status()
        products = response.json()
    except requests.RequestException as e:
        print(f"Error fetching products: {e}")
        products = []
        
    return render_template('shop.html', products=products, current_category=category_id, search_query=search_query)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect(url_for('profile'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            response = requests.post(f'{API_BASE_URL}/users/login/', json={
                'username': username,
                'password': password
            })
            if response.status_code == 200:
                data = response.json()
                session['token'] = data['token']
                session['user'] = {
                    'username': data['username'],
                    'email': data['email'],
                    'id': data['user_id']
                }
                flash('Successfully logged in!', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Invalid credentials. Please try again.', 'error')
        except requests.RequestException:
            flash('Error connecting to the server. Please try again later.', 'error')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user'):
        return redirect(url_for('profile'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            response = requests.post(f'{API_BASE_URL}/users/register/', json={
                'username': username,
                'email': email,
                'password': password
            })
            if response.status_code == 201:
                data = response.json()
                session['token'] = data['token']
                session['user'] = data['user']
                flash('Account created successfully!', 'success')
                return redirect(url_for('profile'))
            else:
                flash(f'Error creating account: {response.text}', 'error')
        except requests.RequestException:
            flash('Error connecting to the server. Please try again later.', 'error')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('token', None)
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if not session.get('user'):
        flash('Please log in to view your profile.', 'error')
        return redirect(url_for('login'))
        
    # Optional: fetch fresh data from Django using token
    # token = session.get('token')
    # headers = {'Authorization': f'Token {token}'}
    # requests.get(f'{API_BASE_URL}/users/profile/', headers=headers)
    
    return render_template('profile.html', user=session['user'])

@app.route('/order-success/<int:order_id>')
def order_success(order_id):
    return render_template('order_success.html', order_id=order_id)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
