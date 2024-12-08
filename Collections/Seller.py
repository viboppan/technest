import datetime

from flask import Blueprint, request, render_template, redirect
from mongoengine import connect

from Collections.Order import get_orders_for_seller

from utils.MongoUtility import Product
from utils.MongoUtility import Seller
from flask import session

seller_endpoints = Blueprint('seller_endpoints', __name__, template_folder='templates')
connect(host="mongodb://localhost:27017/technest")


def get_seller(username):
    seller = Seller.objects(email=username).first()
    seller_dict = seller_to_dict(seller)
    return seller_dict


def seller_to_dict(seller):
    products_list = [str(product_id) for product_id in seller.products]

    seller_dict = {
        'seller_name': seller.seller_name,
        'email': seller.email,
        'contact_number': seller.contact_number,
        'products': products_list
    }

    return seller_dict


@seller_endpoints.route("/seller/add", methods=['POST'])
def add_user():
    if request.method == 'POST':
        seller_name = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        seller = Seller.objects(seller_name=seller_name).first()
        if seller:
            return "username already taken"
            # Get the other fields
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')  # The form field was named 'phone'
        ssn = request.form.get('ssn')
        dob_str = request.form.get('dob')
        address_line1 = request.form.get('address_line1')
        address_line2 = request.form.get('address_line2')
        city = request.form.get('city')
        state = request.form.get('state')
        zipcode = request.form.get('zipcode')
        full_address = f"{address_line1}, {address_line2}, {city}, {state} {zipcode}".strip(", ")
        # Parse the DOB from the form (assuming format YYYY-MM-DD)
        dob = None
        if dob_str:
            try:
                dob = datetime.datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                return "Invalid date format for DOB. Please use YYYY-MM-DD."

        # Create a new seller
        # Create a new seller with additional fields
        new_seller = Seller(
            first_name=first_name,
            last_name=last_name,
            seller_name=seller_name,
            email=email,
            password=password,
            mobile_number=phone,
            ssn=ssn,
            dob=dob,
            address=full_address
        )
        new_seller.save()
        return redirect('/seller')

    else:
        return "method not allowed"


@seller_endpoints.route('/seller/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if the user exists
        seller = Seller.objects(seller_name=username).first()
        if seller and seller.password == password:
            if not seller.approved:
                error = "Your account is not approved by the admin yet. Please wait for approval."
                return render_template('seller_login.html', error=error)
            session['seller_id'] = str(seller.id)
            ordered_products1 = get_orders_for_seller(str(seller.id))
            print("post order")
            print(ordered_products1)
            return redirect('/seller_home/' + str(seller.id))
        else:
            error = "Invalid username or password. Please try again."
            return render_template('seller_login.html', error=error)


@seller_endpoints.route('/seller_home/<seller_id>')
def seller_home(seller_id):
    seller_id = session.get('seller_id')
    products = Product.objects(seller_id=seller_id)
    products_data = []
    if products:
        products_data = format_products(products)
    return render_template('seller.html', ordered_products=get_orders_for_seller(seller_id), seller_id=seller_id,
                           products_data=products_data)


@seller_endpoints.route('/seller/products/', methods=['GET'])
def get_seller_products():
    seller_id = session.get('seller_id')
    products = Product.objects(seller_id=seller_id)
    return {"products": format_products(products)}


@seller_endpoints.route('/seller_logout')
def seller_logout():
    session.clear()
    return redirect('/')


def get_products():
    products = Product.objects()
    products_data = [
        {"name": p.name, "cost": p.cost, "dimensions": p.dimensions, "color": p.color, "brand": p.brand,
         "material": p.material_type, "weight": p.weight, "seller_id": p.seller_id,
         "image_url": p.image_url, "product_id": str(p.id),
         "available_quantity": p.available_quantity, "category": p.category} for p in products]
    return products_data


def format_products(products):
    products_data = [
        {
            "name": p.name,
            "cost": p.cost,
            "dimensions": p.dimensions,
            "color": p.color,
            "brand": p.brand,
            "material": p.material_type,
            "weight": p.weight,
            "seller_id": p.seller_id,
            "image_url": p.image_url,
            "product_id": str(p.id),
            "available_quantity": p.available_quantity,
            "category": p.category
        }
        for p in products
    ]
    return products_data
