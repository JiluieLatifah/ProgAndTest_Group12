from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, AddressBook, Contact, Group
from datetime import datetime

app = Flask(__name__)
# Cấu hình database (đảm bảo khớp với models.py của bạn)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///address_book.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- 1. AUTHENTICATION (Registration / Login) ---

@app.route('/api/register', methods=['POST'])
def register():
    """
    Register a new account. 
    Automatically creates a default AddressBook for the User.
    """
    data = request.json
    
    # Kiểm tra email tồn tại
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'message': 'Email already exists'}), 400
    
    dob_raw = data.get('date_of_birth')
    dob_object = None
    if dob_raw:
        try:
            dob_object = datetime.strptime(dob_raw.split(' ')[0], '%Y-%m-%d').date()
        except Exception:
            pass

    # Hash password
    hashed_password = generate_password_hash(data.get('password'))

    # Tạo User
    new_user = User(
        fullname=data.get('fullname'),
        email=data.get('email'),
        password=hashed_password,
        date_of_birth=dob_object, # Có thể parse từ data nếu cần
        gender=data.get('gender'),
        address=data.get('address'),
        phoneNumber=data.get('phoneNumber')
    )

    db.session.add(new_user)
    db.session.flush() 

    # [LOGIC NGHIỆP VỤ] Tự động tạo 1 cuốn danh bạ mặc định
    default_book = AddressBook(
        book_name="Default Phonebook", 
        user_id=new_user.user_id
    )
    db.session.add(default_book)
    db.session.commit()

    return jsonify({'message': 'User registered successfully', 'user_id': new_user.user_id}), 201

@app.route('/api/login', methods=['POST'])
def login():
    """
    Login and return User info + List of their AddressBook IDs.
    """
    data = request.json
    user = User.query.filter_by(email=data.get('email')).first()

    if not user or not check_password_hash(user.password, data.get('password')):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Lấy danh sách ID các danh bạ của user này để frontend tiện dùng
    book_ids = [book.book_id for book in user.address_books]

    return jsonify({
        'message': 'Login successful',
        'user_id': user.user_id,
        'fullname': user.fullname,
        'address_books': book_ids
    }), 200
@app.route('/api/addressbook/<int:book_id>/groups', methods=['POST'])
def create_group(book_id):
    data = request.json
    # Tạo đối tượng Group mới gắn với AddressBook ID
    new_group = Group(
        group_name=data.get('group_name'),
        address_book_id=book_id
    )
    db.session.add(new_group)
    db.session.commit()
    return jsonify({
        'message': 'Group created successfully', 
        'group_id': new_group.group_id
    }), 201

@app.route('/api/books/<int:book_id>/groups/<int:group_id>', methods=['DELETE'])
def delete_group(book_id, group_id):
    # Tìm group thuộc đúng AddressBook
    group = Group.query.filter_by(group_id=group_id, address_book_id=book_id).first()
    
    if not group:
        return jsonify({'message': 'Group not found in this AddressBook'}), 404

    db.session.delete(group)
    db.session.commit()
    return jsonify({'message': f'Group {group_id} deleted successfully'}), 200
# --- 2. CONTACT MANAGEMENT (Core Logic) ---

@app.route('/api/books/<int:book_id>/contacts', methods=['GET', 'POST'])
def handle_contacts(book_id):
    # Kiểm tra AddressBook có tồn tại không 
    book = AddressBook.query.get(book_id)
    if not book:
        return jsonify({'message': 'AddressBook not found'}), 404

    if request.method == 'GET':
        contacts = Contact.query.filter_by(address_book_id=book_id).all()
        result = []
        for c in contacts:
            result.append({
                "contact_id": c.contact_id,
                "name": c.name,
                "groups": [g.group_name for g in c.group] # Lấy tên các nhóm đã gán
            })
        return jsonify(result), 200

    data = request.json
    new_contact = Contact(
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        notes=data.get('notes'),
        address_book_id=book_id
    )

    group_ids = data.get('group_ids', [])
    if group_ids:
        for g_id in group_ids:
            group_obj = Group.query.get(g_id)
            if group_obj and group_obj.address_book_id == book_id:
                new_contact.group.append(group_obj)
            else:
                return jsonify({'message': f'Logic Error: Group ID {g_id} invalid'}), 400

    db.session.add(new_contact)
    db.session.commit()
    return jsonify({'message': 'Contact added successfully', 'contact_id': new_contact.contact_id}), 201

with app.app_context():
    # Lệnh này sẽ tự động tạo file address_book.db và các bảng nếu chưa có
    db.create_all()
    print("Database đã được khởi tạo thành công!")

if __name__ == "__main__":
    # QUAN TRỌNG: host='0.0.0.0' để Docker có thể kết nối ra ngoài
    app.run(host='0.0.0.0', port=5000, debug=True)

