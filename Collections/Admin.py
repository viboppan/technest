import datetime
from flask import Blueprint, request, render_template, redirect
from mongoengine import connect
from utils.MongoUtility import Admin, Seller

admin_endpoints = Blueprint('admin_endpoints', __name__, template_folder='templates')
connect(host="mongodb://localhost:27017/technest")


@admin_endpoints.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin_user = Admin.objects(admin_username=username).first()
        if admin_user and admin_user.password == password:
            return redirect('/admin_view/' + str(admin_user.id))
        else:
            error = "Invalid username or password. Please try again."
            return render_template('admin_login.html', error=error)
    else:
        return render_template('admin_login.html')


@admin_endpoints.route("/admin_view/<admin_id>")
def admin_view(admin_id):
    # Fetch all sellers who are not yet approved
    pending_sellers = Seller.objects(approved=False)
    return render_template('admin_view.html', admin_id=admin_id, pending_sellers=pending_sellers)


@admin_endpoints.route('/admin/approve_seller/<seller_id>', methods=['POST'])
def approve_seller(seller_id):
    seller = Seller.objects(id=seller_id).first()
    if seller:
        seller.approved = True
        seller.save()
    return redirect(f'/admin_view/{request.form.get("admin_id")}')


@admin_endpoints.route('/admin/deny_seller/<seller_id>', methods=['POST'])
def deny_seller(seller_id):
    seller = Seller.objects(id=seller_id).first()
    if seller:
        seller.delete()
    return redirect(f'/admin_view/{request.form.get("admin_id")}')
