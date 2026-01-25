from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, AddressBook, Contact, Group

app = Flask(__name__)
# Cấu hình database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///address_book.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- 1. AUTHENTICATION (Đăng ký / Đăng nhập) ---

@app.route('/api/register', methods=['POST'])
def register():
    """
    API đăng ký người dùng mới.
    """
    data = request.json
    
    # Kiểm tra email đã tồn tại chưa
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'message': 'Email already exists'}), 400

    # Mã hóa mật khẩu
    hashed_password = generate_password_hash(data.get('password'), method='sha256')

    # Tạo User mới
    new_user = User(
        fullname=data.get('fullname'),
        email=data.get('email'),
        password=hashed_password,
        date_of_birth=None, 
        gender=data.get('gender'),
        address=data.get('address'),
        phoneNumber=data.get('phoneNumber')
    )

    db.session.add(new_user)
    db.session.commit()

    # [LOGIC NGHIỆP VỤ] Tự động tạo AddressBook mặc định cho User
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
    API đăng nhập.
    """
    data = request.json
    user = User.query.filter_by(email=data.get('email')).first()

    # Kiểm tra thông tin đăng nhập
    if not user or not check_password_hash(user.password, data.get('password')):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    # Lấy danh sách ID các danh bạ của user
    book_ids = [book.book_id for book in user.address_books]

    return jsonify({
        'message': 'Login successful',
        'user_id': user.user_id,
        'fullname': user.fullname,
        'address_books': book_ids
    }), 200

# --- 2. CONTACT MANAGEMENT (Logic cốt lõi) ---

@app.route('/api/books/<int:book_id>/contacts', methods=['POST'])
def add_contact(book_id):
    """
    Thêm Contact vào AddressBook.
    Kiểm tra logic Group phải cùng AddressBook.
    """
    data = request.json
    
    # Kiểm tra AddressBook có tồn tại không
    book = AddressBook.query.get(book_id)
    if not book:
        return jsonify({'message': 'AddressBook not found'}), 404

    # Tạo Contact mới
    new_contact = Contact(
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        notes=data.get('notes'),
        address_book_id=book_id
    )

    # [LOGIC QUAN TRỌNG] Xử lý thêm vào Group
    group_ids = data.get('group_ids', [])
    
    if group_ids:
        for g_id in group_ids:
            group_obj = Group.query.get(g_id)
            if group_obj:
                # KIỂM TRA RÀNG BUỘC: Group phải thuộc cùng AddressBook
                if group_obj.address_book_id == book_id:
                    new_contact.group.append(group_obj) 
                else:
                    return jsonify({
                        'message': f'Group ID {g_id} belongs to a different AddressBook. Action denied.'
                    }), 400
            else:
                return jsonify({'message': f'Group ID {g_id} not found'}), 404

    db.session.add(new_contact)
    db.session.commit()

    return jsonify({'message': 'Contact added successfully', 'contact_id': new_contact.contact_id}), 201

@app.route('/api/contacts/<int:contact_id>', methods=['PUT'])
def edit_contact(contact_id):
    """
    Sửa thông tin Contact và cập nhật Group.
    """
    data = request.json
    contact = Contact.query.get(contact_id)
    
    if not contact:
        return jsonify({'message': 'Contact not found'}), 404

    # Cập nhật thông tin cơ bản
    contact.name = data.get('name', contact.name)
    contact.email = data.get('email', contact.email)
    contact.phone = data.get('phone', contact.phone)
    contact.address = data.get('address', contact.address)
    contact.notes = data.get('notes', contact.notes)

    # Cập nhật Group (nếu có danh sách mới)
    if 'group_ids' in data:
        # Xóa liên kết cũ
        contact.group = [] 
        
        group_ids = data['group_ids']
        for g_id in group_ids:
            group_obj = Group.query.get(g_id)
            if group_obj:
                # KIỂM TRA RÀNG BUỘC
                if group_obj.address_book_id == contact.address_book_id:
                    contact.group.append(group_obj)
                else:
                    return jsonify({'message': 'Cannot add contact to a group in a different AddressBook'}), 400

    db.session.commit()
    return jsonify({'message': 'Contact updated successfully'}), 200

@app.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """
    Xóa Contact khỏi danh bạ.
    """
    contact = Contact.query.get(contact_id)
    if not contact:
        return jsonify({'message': 'Contact not found'}), 404
    
    db.session.delete(contact)
    db.session.commit()
    return jsonify({'message': 'Contact deleted successfully'}), 200

# --- API PHỤ: TẠO GROUP (Để phục vụ kiểm thử logic) ---
@app.route('/api/books/<int:book_id>/groups', methods=['POST'])
def create_group(book_id):
    """
    Tạo Group mới cho một AddressBook.
    """
    data = request.json
    book = AddressBook.query.get(book_id)
    if not book:
        return jsonify({'message': 'AddressBook not found'}), 404
    
    new_group = Group(
        group_name=data['group_name'],
        address_book_id=book_id
    )
    db.session.add(new_group)
    db.session.commit()
    return jsonify({'message': 'Group created successfully', 'group_id': new_group.group_id}), 201

# --- Chạy ứng dụng ---
if __name__ == '__main__':
    with app.app_context():
        # Tạo bảng dữ liệu nếu chưa có
        db.create_all()
    app.run(debug=True)
