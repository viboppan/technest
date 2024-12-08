import os
from pathlib import Path

from flask import Blueprint, request, jsonify, render_template, json
from mongoengine.base import get_document

from Collections.Customer import get_product_page
from Collections.Seller import get_products
from utils.MongoUtility import Product

product_endpoints = Blueprint('product_endpoints', __name__, template_folder='templates')


@product_endpoints.route("/add_product", methods=['POST'])
def add_product():
    try:
        # Get product data from the request
        product_data = request.form
        # Read fields from the JSON data
        name = product_data.get('name')
        cost = product_data.get('cost')
        dimensions = product_data.get('dimensions')
        dimensions = dimensions.split('*')
        color = product_data.get('color')
        brand = product_data.get('brand')
        material_type = product_data.get('material_type')
        weight = product_data.get('weight')
        seller_id = product_data.get('seller_id')
        image_file = request.files['image']
        category = product_data.get('category')
        description = product_data.get('description')
        available_quantity = product_data.get('available_quantity')

        # This field comes from the hidden input in the form
        serial_numbers_json = product_data.get('serial_numbers')
        if serial_numbers_json:
            serial_numbers = json.loads(serial_numbers_json)  # Convert JSON string to a Python list
        else:
            serial_numbers = []
        print(serial_numbers)
        if image_file:
            # Create the target folder if it doesn't exist
            parent_folder_path = str(Path(os.path.dirname(__file__)).parents[0])
            target_folder = parent_folder_path + '\\static\\pictures\\' + category
            os.makedirs(target_folder, exist_ok=True)

            # Save the image to the target folder
            image_path = os.path.join(target_folder, image_file.filename)
            image_file.save(image_path)
            ui_image_path = '..' + image_path[len(parent_folder_path):].replace('\\', '/')


            # Create a new Product instance
            new_product = Product(
                name=name,
                cost=cost,
                dimensions=dimensions,
                color=color,
                brand=brand,
                material_type=material_type,
                weight=weight,
                seller_id=seller_id,
                image_url=ui_image_path,
                category=category,
                description=description,
                # Convert "available_quantity" to an integer
                available_quantity=int(product_data.get('available_quantity', 100))
            )
            print("110")
            # Save the new product to the database
            print(new_product.to_json())
            new_product.save()
            # Now use the fetched serial_numbers list to create ProductInstance documents
            productinstance_model = get_document('ProductInstance')
            for sn in serial_numbers:
                product_instance = productinstance_model(
                    product=new_product,
                    serial_number=sn,
                    status='in_stock'
                )
                product_instance.save()
            return render_template('seller.html', isProductAdded=True, products=get_products())
        else:
            return jsonify({"error": "No image provided"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@product_endpoints.route("/get_product_page/<customerid>", methods=['GET'])
def go_to_home(customerid):
    print("customer id  is " + customerid)
    return get_product_page(str(customerid))


from flask import jsonify


@product_endpoints.route('/products', methods=['GET'])
def get_all_products():
    try:
        # Retrieve all products from the database
        products = Product.objects()

        # Convert products to a list of dictionaries
        products_data = [
            {
                "name": product.name,
                "cost": product.cost,
                "dimensions": product.dimensions,
                "color": product.color,
                "brand": product.brand,
                "material_type": product.material_type,
                "weight": product.weight,
                "seller_id": product.seller_id,
                "image_url": product.image_url,
                "product_id": str(product.id),
                "available_quantity": product.available_quantity,
                "category": product.category,
                "description": product.description,
            }
            for product in products
        ]

        # Return the product list as JSON
        return jsonify({"products": products_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
