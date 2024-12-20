from flask import request, Blueprint, render_template, session, redirect, url_for, jsonify, json
from mongoengine import *
from mongoengine.base.common import get_document
from utils.MongoUtility import Customer, Order, ProductBought, Product, Payment
from Collections.Customer import get_product_page

order_endpoints = Blueprint('order_endpoints', __name__,
                            template_folder='templates')

connect(host="mongodb://localhost:27017/technest")


def update_product_instances_to_ordered(product, status, product_quantity):
    productInstance1 = get_document('ProductInstance')
    # Now find the required number of ProductInstances that are 'in_stock' for this product
    available_instances = productInstance1.objects(product=product, status='in_stock').limit(
        product_quantity)
    if available_instances.count() < product_quantity:
        return jsonify({"error": f"Not enough in-stock units for product with ID {product_id}"}), 400
    allocated_serials = []
    # Update each selected unit's status to 'ordered'
    for instance in available_instances:
        instance.status = status
        instance.save()
        allocated_serials.append(instance.serial_number)
    return allocated_serials


@order_endpoints.route("/add_order", methods=['POST'])
def add_order():
    try:
        order_data = request.get_json()

        # Validate product existence and gather product details
        product1 = get_document('Product')
        product_bought_instances = []
        for product_info in order_data.get('products', []):
            product_id = product_info.get('product_id')
            product_quantity = product_info.get('quantity', 0)

            product = product1.objects(id=product_id).first()
            if not product:
                return jsonify({"error": f"Product with ID {product_id} does not exist"}), 400

            if product_quantity > product.available_quantity:
                return jsonify({"error": f"Not enough stock available for product with ID {product_id}"}), 400
            else:
                product.available_quantity -= product_quantity
                product.save()
                allocated_serial_numbers = update_product_instances_to_ordered(product, 'ordered', product_quantity)
                # Create ProductBought instance
                product_bought_instance = ProductBought(product_id=product_id, quantity=product_quantity,
                                                        serial_numbers=allocated_serial_numbers)
                product_bought_instances.append(product_bought_instance)

        # Calculate total cost
        total_cost = order_data.get('total_cost')

        # Create the order instance
        order = Order(
            customer_id=order_data.get('customer_id'),
            products=product_bought_instances,
            total_cost=total_cost,
            delivery_type=order_data.get('delivery_type')
        )
        order.save()
        generated_id = str(order.id)
        print(order)
        # Update the customer's order history
        customer = Customer.objects(id=order.customer_id).first()
        if customer:
            customer.order_history.append(order.id)
            customer.save()

            return jsonify({"message": "Order added successfully!", "order_id": generated_id}), 201
        else:
            return jsonify({"error": "Customer not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@order_endpoints.route("/get_order/<order_id>", methods=['GET'])
def get_order(order_id):
    try:
        # Retrieve the order based on the order ID
        order = Order.objects(id=order_id).first()

        if order:
            # Convert the order object to a dictionary for JSON serialization
            order_data = order_dict = orderedprods_to_dict(order)
            return jsonify(order_data), 200
        else:
            return jsonify({"error": f"Order with ID {order_id} not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@order_endpoints.route("/cancel_order/<order_id>", methods=['GET'])
def cancel_order(order_id):
    try:
        # Retrieve the order based on the order ID
        order = Order.objects(id=str(order_id)).first()
        if order:
            if order.order_status == "cancelled":
                return jsonify({"error": f"Order with ID {order_id} already cancelled"}), 400

            # Iterate through products in the order
            for product_info in order.products:
                product_id = product_info.product_id.id
                quantity = product_info.quantity

                # Retrieve the product based on the product ID
                product = Product.objects(id=product_id).first()

                if product:
                    # Increase the available quantity for the product
                    product.available_quantity += quantity
                    product.save()

            order.order_status = "cancelled"
            order.save()

            # Convert the order object to a dictionary for JSON serialization
            order_data = order_dict = order_to_dict(order)
            return render_template('seller.html', ordered_products=get_orders_for_seller(product.seller_id))
        else:
            return jsonify({"error": f"Order with ID {order_id} not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@order_endpoints.route("/customer/cancel_order", methods=['POST'])
def cancel_order_by_customer():
    try:
        order_data = request.json
        order_id = order_data.get('order_id')
        # customer_id=order_data.get('customer_id')
        # Retrieve the order based on the order ID
        order = Order.objects(id=str(order_id)).first()
        if order:
            if order.order_status == "cancelled":
                return jsonify({"error": f"Order with ID {order_id} already cancelled"}), 400
            product_instance_model = get_document('ProductInstance')
            # Iterate through products in the order
            for product_info in order.products:
                product_id = product_info.product_id.id
                quantity = product_info.quantity

                # Retrieve the product based on the product ID
                product = Product.objects(id=product_id).first()

                if product:
                    # Increase the available quantity for the product
                    product.available_quantity += quantity
                    product.save()

                    # Revert ProductInstance statuses to 'in_stock'
                    for serial_num in product_info.serial_numbers:
                        instance = product_instance_model.objects(serial_number=serial_num).first()
                        if instance and instance.status == 'ordered':
                            instance.status = 'in_stock'
                            instance.save()

            order.order_status = "cancelled"
            order.save()

            # Cancel associated payment(s)
            print("Order ID: " + order_id)
            payments = Payment.objects(order_id=str(order_id))
            if payments:
                for payment in payments:
                    if payment.status != "refunded":
                        payment.status = "refunded"
                        payment.save()
            # Convert the order object to a dictionary for JSON serialization
            # order_data = order_dict = order_to_dict(order)
            # return get_product_page(customer_id)
            return jsonify({"message": "Order Cancelled successfully"}), 201
        else:
            return jsonify({"error": f"Order with ID {order_id} not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@order_endpoints.route("/customer/return_order", methods=['POST'])
def return_order_by_customer():
    try:
        print("hi")
        order_data = request.json
        print("id: "+order_data.get('order_id'))
        order_id = order_data.get('order_id')
        # Retrieve the order based on the order ID
        order = Order.objects(id=str(order_id)).first()
        print("hi2")
        if not order:
            return jsonify({"error": f"Order with ID {order_id} not found"}), 404

        if order.order_status.lower() not in ["delivered", "picked up"]:
            return jsonify({"error": "Order cannot be returned as it is not delivered or picked up"}), 400
        print("hi3")
        product_instance_model = get_document('ProductInstance')
        print("hi4")
        # Iterate through products in the order
        for product_info in order.products:
            product_id = product_info.product_id.id
            quantity = product_info.quantity

            # Retrieve the product based on the product ID
            product = Product.objects(id=product_id).first()

            if product:
                # Increase the available quantity for the product
                product.available_quantity += quantity
                product.save()

                # Revert ProductInstance statuses to 'in_stock'
                for serial_num in product_info.serial_numbers:
                    instance = product_instance_model.objects(serial_number=serial_num).first()
                    if instance and instance.status in ['delivered', 'picked_up']:
                        instance.status = 'in_stock'
                        instance.save()

        # Update the order status
        order.order_status = "returned"
        order.save()

        # Process refund (if applicable)
        payments = Payment.objects(order_id=str(order_id))
        if payments:
            for payment in payments:
                if payment.status != "refunded":
                    payment.status = "refunded"
                    payment.save()

        return jsonify({"message": "Order returned successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@order_endpoints.route("/confirm_order/<order_id>", methods=['GET', 'POST'])
def dispatch_order(order_id):
    try:
        # Retrieve the order based on the order ID
        order = Order.objects(id=str(order_id)).first()
        seller_id = request.form.get('seller_id')
        if order:
            if order.order_status == "cancelled":
                return jsonify({"error": f"Order with ID {order_id} already cancelled"}), 400
            order.order_status = "confirmed"
            order.save()

            # Convert the order object to a dictionary for JSON serialization
            order_data = order_dict = order_to_dict(order)
            return render_template('seller.html', ordered_products=get_orders_for_seller(seller_id))
        else:
            return jsonify({"error": f"Order with ID {order_id} not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@order_endpoints.route("/pick_up_order/<order_id>", methods=['GET', 'POST'])
def pickup_order(order_id):
    try:
        # Retrieve the order based on the order ID
        order = Order.objects(id=str(order_id)).first()
        seller_id = request.form.get('seller_id')
        if order:
            if order.order_status == "cancelled":
                return jsonify({"error": f"Order with ID {order_id} already cancelled"}), 400
            order.order_status = "Picked up"
            order.save()

            # Convert the order object to a dictionary for JSON serialization
            order_data = order_dict = order_to_dict(order)
            return redirect('/seller_home/' + str(seller_id))
        else:
            return jsonify({"error": f"Order with ID {order_id} not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@order_endpoints.route("/deliver_order/<order_id>", methods=['GET', 'POST'])
def delivered_order(order_id):
    try:
        # Retrieve the order based on the order ID
        order = Order.objects(id=str(order_id)).first()
        seller_id = request.form.get('seller_id')
        if order:
            if order.order_status == "cancelled":
                return jsonify({"error": f"Order with ID {order_id} already cancelled"}), 400
            order.order_status = "Delivered"
            order.save()

            # Convert the order object to a dictionary for JSON serialization
            order_data = order_dict = order_to_dict(order)
            return render_template('seller.html', ordered_products=get_orders_for_seller(seller_id))
        else:
            return jsonify({"error": f"Order with ID {order_id} not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@order_endpoints.route("/get_orders_for_seller/<seller_id>", methods=['GET'])
def get_orders_for_seller(seller_id):
    try:
        # Retrieve the products sold by the seller
        print(seller_id + " here")
        seller_products = Product.objects(seller_id=seller_id)
        print(seller_products)
        # Extract product IDs
        product_ids = [str(product.id) for product in seller_products]
        print((product_ids))
        # Retrieve orders containing the seller's products
        orders = Order.objects(
            Q(products__product_id__in=product_ids) &
            (Q(order_status="processing") | Q(order_status="confirmed"))
        )
        print(orders)
        # Convert orders to a list of dictionaries for JSON serialization
        orders_data = [orderedprods_to_dict(order, seller_products) for order in orders]

        return orders_data

    except Exception as e:
        return jsonify({"error": str(e)}), 400


def order_to_dict(order):
    products_list = []
    for product_bought in order.products:
        product_dict = {
            'product_id': str(product_bought.product_id.id),
            'quantity': product_bought.quantity
        }
        products_list.append(product_dict)

    order_dict = {
        'order_id': str(order.id),
        'customer_id': str(order.customer_id),
        'products': products_list,
        'order_date': order.order_date.strftime('%Y-%m-%d %H:%M:%S'),
        'total_cost': order.total_cost,
        'order_status': order.order_status,
        'delivery_type': order.delivery_type

    }
    return order_dict


def orderedprods_to_dict(order, product_objects):
    products_list = []
    for product_bought in order.products:
        # Find the product object in product_objects list based on product ID
        product_object = next((prod for prod in product_objects if str(prod.id) == str(product_bought.product_id.id)),
                              None)

        if product_object:
            product_dict = {
                'product': {
                    'id': str(product_object.id),
                    'name': product_object.name,
                    'cost': product_object.cost,
                    'dimensions': product_object.dimensions,
                    'color': product_object.color,
                    'brand': product_object.brand,
                    'material_type': product_object.material_type,
                    'weight': product_object.weight,
                    'seller_id': product_object.seller_id,
                    'image_url': product_object.image_url,
                    'category': product_object.category,
                    'description': product_object.description,
                    'available_quantity': product_object.available_quantity
                },
                'quantity': product_bought.quantity
            }
            products_list.append(product_dict)

    order_dict = {
        'order_id': str(order.id),
        'customer_id': str(order.customer_id),
        'products': products_list,
        'order_date': order.order_date.strftime('%Y-%m-%d %H:%M:%S'),
        'total_cost': order.total_cost,
        'order_status': order.order_status,
        'delivery_type': order.delivery_type
    }
    return order_dict
