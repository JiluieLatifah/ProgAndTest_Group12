from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, AddressBook, Contact, Group

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

    # Hash password
    hashed_password = generate_password_hash(data.get('password'), method='sha256')

    # Tạo User
    new_user = User(
        fullname=data.get('fullname'),
        email=data.get('email'),
        password=hashed_password,
        date_of_birth=None, # Có thể parse từ data nếu cần
        gender=data.get('gender'),
        address=data.get('address'),
        phoneNumber=data.get('phoneNumber')
    )

    db.session.add(new_user)
    db.session.commit() # Commit để lấy user_id

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

# --- 2. CONTACT MANAGEMENT (Core Logic) ---

@app.route('/api/books/<int:book_id>/contacts', methods=['POST'])
def add_contact(book_id):
    """
    API to add a new contact to a specific address book.
    Includes logic to verify if the groups belong to the same address book.
    """
    # 1. Lấy dữ liệu gửi lên
    data = request.json
    
    # 2. Kiểm tra AddressBook có tồn tại không
    book = AddressBook.query.get(book_id)
    if not book:
        return jsonify({'message': 'AddressBook not found'}), 404

    # 3. Tạo đối tượng Contact (chưa lưu vào DB)
    new_contact = Contact(
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        notes=data.get('notes'),
        address_book_id=book_id  # Quan trọng: Gán contact vào cuốn sổ hiện tại
    )

    # 4. --- LOGIC KIỂM TRA BOOK ID (Check bookID Logic) ---
    
    # Lấy danh sách ID nhóm muốn thêm (ví dụ: [1, 2])
    group_ids = data.get('group_ids', [])
    
    if group_ids:
        for g_id in group_ids:
            group_obj = Group.query.get(g_id)
            
            if group_obj:
                # KIỂM TRA: Group này có thuộc về cuốn sổ hiện tại không?
                # group_obj.address_book_id: ID cuốn sổ của nhóm
                # book_id: ID cuốn sổ đang thêm contact
                
                if group_obj.address_book_id == book_id:
                    # Nếu trùng khớp -> Cho phép thêm vào danh sách nhóm của contact
                    new_contact.group.append(group_obj) 
                else:
                    # Nếu KHÔNG trùng khớp -> Báo lỗi ngay lập tức
                    return jsonify({
                        'message': f'Logic Error: Group ID {g_id} belongs to a different AddressBook. Cannot assign.'
                    }), 400
            else:
                return jsonify({'message': f'Group ID {g_id} not found'}), 404

    # 5. Lưu vào Database
    db.session.add(new_contact)
    db.session.commit
