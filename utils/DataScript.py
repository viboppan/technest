import os
import re
import uuid

from mongoengine import connect, Document, StringField, FloatField, ListField, FloatField, ObjectIdField, IntField
from faker import Faker
import random

from utils.MongoUtility import Seller as Vendor, Product as Item, Customer as Shopper, ProductInstance, Admin

faker_instance = Faker()

# MongoDB Connection
connect(host="mongodb://localhost:27017/technest")

# Predefined list of valid colors
COLOR_LIST = [
    "black", "white", "red", "blue", "green", "yellow", "brown",
    "orange", "pink", "purple", "gray", "gold", "silver", "navy",
    "beige", "maroon", "teal", "cyan", "magenta", "lime", "olive"
]


# Function to extract color from the image name
def get_color_from_filename(file_name):
    # Convert filename to lowercase for case-insensitive matching
    file_name_lowercase = file_name.lower()

    # Check each valid color in the filename
    for color_name in COLOR_LIST:
        if color_name in file_name_lowercase:
            return color_name  # Return the first matching color

    # Default to "black" if no color is found
    return "black"


# Function to insert products from images in folders with random data and color detection
def populate_items_from_images(directory_path):
    vendor_instance = Vendor(
        seller_name="seller123",
        email="seller@gmail.com",
        password="12345",
        first_name="Joe",
        last_name="Root",
        address="Sandstone"
    )
    vendor_instance.save()
    default_shopper = Shopper(
        first_name="John",
        last_name="Doe",
        username="viboppan",
        email="default@example.com",
        password="12345",  # Consider hashing this password in a real scenario
        mobile_number="1234567890",
        address="123 Default Street, Dev City"
    )
    default_shopper.save()
    # Create a sample admin user
    admin = Admin(
        admin_username="admin",
        email="admin@example.com",
        password="admin123",  # Consider hashing this password in a real scenario
        role="superadmin"  # or another role if applicable
    )
    admin.save()
    vendor_identifier = str(vendor_instance.id)
    for folder_name in os.listdir(directory_path):
        category_directory = os.path.join(directory_path, folder_name)
        if os.path.isdir(category_directory):
            for idx, image_name in enumerate(os.listdir(category_directory)):
                image_location = os.path.join(category_directory, image_name)

                # Extract color from the filename
                detected_color = get_color_from_filename(image_name)
                # Random quantity
                available_quantity = round(random.uniform(4, 40), 0)
                # Create a new Product document with random data and detected color
                item_instance = Item(
                    name=f"{folder_name}{idx + 1}",
                    cost=round(random.uniform(50, 500), 2),
                    dimensions=[round(random.uniform(1, 10), 0) for _ in range(3)],
                    color=detected_color,
                    brand=faker_instance.company(),
                    material_type="metal",
                    weight=round(random.uniform(1, 50), 2),
                    seller_id=vendor_identifier,
                    image_url=image_location,  # Store local path as image_url
                    category=folder_name,
                    description="This awesome product provides you fabulous performance",
                    available_quantity=int(available_quantity)
                )
                item_instance.save()
                # Generate ProductInstance documents for each unit
                for i in range(0, int(available_quantity)):
                    ProductInstance(
                        product=item_instance,
                        serial_number=generate_serial_number(item_instance.name),
                        status='in_stock'
                    ).save()


def generate_serial_number(product_name):
    abbreviation = product_name[:3].upper()
    last_char = product_name[-1].upper()
    code = abbreviation + last_char

    # Generate a random UUID and shorten it (e.g., first 8 chars)
    unique_suffix = uuid.uuid4().hex[:8].upper()  # 8-char unique code
    return f"{code}{unique_suffix}"


# Driver code
if __name__ == "__main__":
    directory_path_for_images = "../static/pictures/"  # Replace with your actual path
    populate_items_from_images(directory_path_for_images)
