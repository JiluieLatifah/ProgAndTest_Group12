from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, AddressBook, Contact, Group
from datetime import datetime

app = Flask(__name__)
# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///address_book.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def home():
    contacts = Contact.query.all()
    return render_template('index.html', contacts=contacts)

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_view():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')

        # Check if email exists
        if User.query.filter_by(email=email).first():
            return "Email already exists! <a href='/register'>Try again</a>"

        hashed_pw = generate_password_hash(password)
        new_user = User(
            fullname=fullname,
            email=email,
            password=hashed_pw,
            phoneNumber=phone 
        )

        db.session.add(new_user)
        db.session.commit()

        # Default AddressBook creation
        new_book = AddressBook(book_name=f"{fullname}'s Book", user_id=new_user.user_id)
        db.session.add(new_book)
        db.session.commit()

        return redirect(url_for('login_view'))

    return render_template('register.html')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/contacts')
def contacts_page():
    contacts = Contact.query.all()
    return render_template('contact_list.html', contacts=contacts)

@app.route('/contact/add')
def add_contact_page():
    return render_template('contact_form.html')

@app.route('/contact/view/<int:contact_id>')
def view_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    return render_template('contact_detail.html', contact=contact)

@app.route('/contact/edit/<int:contact_id>')
def edit_contact_page(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    return render_template('contact_form.html', contact=contact)

@app.route('/groups')
def group_manage_page():
    all_groups = Group.query.all()
    # Debug info
    print(f"--- DEBUG: Total groups found: {len(all_groups)} ---")
    for g in all_groups:
        print(f"Group: {g.group_name}, ID: {g.group_id}")

    return render_template('group_manage.html', groups=all_groups)

@app.route('/group/add')
def add_group_page():
    all_contacts = Contact.query.all() 
    return render_template('group_form.html', all_contacts=all_contacts)

@app.route('/contact/delete/<int:contact_id>')
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    try:
        db.session.delete(contact)
        db.session.commit()
        return redirect(url_for('dashboard_page')) 
    except Exception as e:
        db.session.rollback()
        return f"Error while deleting: {e}"

@app.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            return redirect(url_for('dashboard_page'))
        return "Invalid email or password!" 
    return render_template('login.html')

@app.route('/api/contact/add', methods=['POST'])
def add_contact_api():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        user_id_test = 1 

        book = AddressBook.query.filter_by(user_id=user_id_test).first()
        if not book:
            book = AddressBook(book_name="My First Book", user_id=user_id_test)
            db.session.add(book)
            db.session.flush()

        new_contact = Contact(
            name=name,
            email=email,
            phone=phone,
            address_book_id=book.book_id
        )
        
        db.session.add(new_contact)
        db.session.commit()
        return jsonify({"status": "success", "message": "Contact added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/api/contact/edit', methods=['POST'])
def edit_contact_api():
    try:
        contact_id = request.form.get('id')
        contact = Contact.query.get(contact_id)
        if not contact:
            return jsonify({"status": "error", "message": "Contact not found"}), 404

        contact.name = request.form.get('name')
        contact.email = request.form.get('email')
        contact.phone = request.form.get('phone')

        db.session.commit()
        return jsonify({"status": "success", "message": "Contact updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/group/add', methods=['POST'])
def add_group_api():
    try:
        group_name = request.form.get('group_name')
        contact_ids = request.form.getlist('contact_ids')
        book = AddressBook.query.filter_by(user_id=1).first()
        
        if not book:
            book = AddressBook(book_name="My Book", user_id=1)
            db.session.add(book)
            db.session.flush()

        new_group = Group(group_name=group_name, address_book_id=book.book_id)
        for c_id in contact_ids:
            contact_obj = Contact.query.get(c_id)
            if contact_obj:
                new_group.contacts.append(contact_obj)
        
        db.session.add(new_group)
        db.session.commit()
        return jsonify({"status": "success", "message": "Group added successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/group/delete/<int:group_id>')
def delete_group(group_id):
    group = Group.query.get_or_404(group_id)
    try:
        db.session.delete(group)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"Error while deleting: {e}"
    return redirect(url_for('group_manage_page'))

@app.route('/group/edit/<int:group_id>')
def edit_group_page(group_id):
    group = Group.query.get_or_404(group_id)
    all_contacts = Contact.query.all() 
    current_contact_ids = [c.contact_id for c in group.contacts]
    return render_template('group_form.html', group=group, all_contacts=all_contacts, current_contact_ids=current_contact_ids)

@app.route('/api/group/<int:group_id>/remove_member/<int:contact_id>', methods=['POST'])
def remove_member_from_group(group_id, contact_id):
    try:
        group = Group.query.get_or_404(group_id)
        contact = Contact.query.get_or_404(contact_id)
        if contact in group.contacts:
            group.contacts.remove(contact)
            db.session.commit()
            return jsonify({"status": "success", "message": "Member removed successfully"}), 200
        return jsonify({"status": "error", "message": "Contact not in this group"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/api/group/edit', methods=['POST'])
def edit_group_api():
    try:
        group_id = request.form.get('id')
        group = Group.query.get(group_id)
        if not group:
            return jsonify({"status": "error", "message": "Group not found"}), 404

        group.group_name = request.form.get('group_name')
        selected_contact_ids = request.form.getlist('contact_ids') 
        for c_id in selected_contact_ids:
            contact_obj = Contact.query.get(c_id)
            if contact_obj and contact_obj not in group.contacts:
                group.contacts.append(contact_obj)

        db.session.commit()
        return jsonify({"status": "success", "message": "Group name updated and members added successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

with app.app_context():
    db.create_all()
    print("Database initialized successfully!")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
