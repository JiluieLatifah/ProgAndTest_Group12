from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, Table, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

db = SQLAlchemy()

contact_group = Table(
    'contact_group',
    db.Model.metadata,
    Column('contact_id', Integer, ForeignKey('contacts.contact_id')),
    Column('group_id', Integer, ForeignKey('groups.group_id'))
)

class User(db.Model):
    __tablename__ = 'users'

    # Các thuộc tính
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    fullname = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(String(10))
    address = Column(String(255))
    phone = Column(String(20))

    # 1 User có nhiều AddressBook
    address_books = relationship('AddressBook', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User(id={self.user_id}, fullname='{self.fullname}'>"
    
class AddressBook(db.Model):
    __tablename__ = 'address_books'

    book_id = Column(Integer, primary_key=True, autoincrement=True)
    book_name = Column(String(100), nullable=False)
    createdDate = Column(Date, default=func.now())
    # Foreign key tới User
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)

    # Quan hệ
    user = relationship('User', back_populates='address_books')
    contacts = relationship('Contact', back_populates='address_book', cascade='all, delete-orphan')
    group = relationship('Group', back_populates='address_book', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<AddressBook(id={self.book_id}, name='{self.book_name}')>"

# Contact
class Contact(db.Model):
    __tablename__ = 'contacts'

    contact_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(String(255))
    notes = Column(Text)

    # Foreign key tới AddressBook
    address_book_id = Column(Integer, ForeignKey('address_books.book_id'), nullable=False)

    # Quan hệ
    address_book = relationship('AddressBook', back_populates='contacts')

    # Quan hệ n-n
    group = relationship('Group', secondary=contact_group, back_populates='contacts')

    def __repr__(self):
        return f"<Contact(id={self.contact_id}, name='{self.name}')>"
    
# Group
class Group(db.Model):
    __tablename__ = 'groups'

    group_id = Column(Integer, primary_key=True, autoincrement=True)
    group_name = Column(String(50), nullable=False)

    # Foreign key tới AddressBook (1 Group thuộc về 1 AddressBook)
    address_book_id = Column(Integer, ForeignKey('address_books.book_id'), nullable=False)

    # Quan hệ
    address_book = relationship('AddressBook', back_populates='group')

    # Quan hệ n-n
    contacts = relationship('Contact', secondary=contact_group, back_populates='group')

    def __repr__(self):
        return f"<Group(id={self.group_id}, name='{self.group_name}')>"
    
if __name__ == "__main__":

    engine= create_engine('sqlite:///address_book.db', echo=True)
    print("Creating database...")
    db.Model.metadata.create_all(engine)   
    print("Database created.")