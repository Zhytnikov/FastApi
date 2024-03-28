from sqlalchemy import create_engine, Column, Integer, String, Date
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import date, timedelta
from pydantic import BaseModel
from typing import List

# З'єднання з базою даних
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:1234@localhost/db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String)
    birth_date = Column(Date)
    additional_data = Column(String, nullable=True)

# Оголошення схем Pydantic 
class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birth_date: date
    additional_data: str = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(ContactBase):
    pass

class ContactResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    phone_number: str
    birth_date: date
    additional_data: str = None

# Ініціалізація FastAPI
app = FastAPI()

Base.metadata.create_all(bind=engine)

# Отримання сесії бази даних
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_contact(db_session, contact_id: int):
    contact = db_session.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

# Функції CRUD

@app.post("/contacts/", response_model=ContactResponse)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    db_contact = Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.get("/contacts/", response_model=List[ContactResponse])
def read_contacts(
    db: Session = Depends(get_db),
    name: str = None,
    email: str = None,
    surname: str = None,
    skip: int = 0,
    limit: int = 10,
):
    contacts = db.query(Contact)
    if name:
        contacts = contacts.filter(Contact.first_name.ilike(f"%{name}%"))
    if surname:
        contacts = contacts.filter(Contact.last_name.ilike(f"%{surname}%"))
    if email:
        contacts = contacts.filter(Contact.email.ilike(f"%{email}%"))
    return contacts.offset(skip).limit(limit).all()

@app.get("/contacts/{contact_id}", response_model=ContactResponse)
def read_contact(contact_id: int, db: Session = Depends(get_db)):
    return get_contact(db, contact_id)

@app.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: int, contact: ContactUpdate, db: Session = Depends(get_db)):
    db_contact = get_contact(db, contact_id)
    for key, value in contact.dict().items():
        if value is not None:
            setattr(db_contact, key, value)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.delete("/contacts/{contact_id}", response_model=ContactResponse)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = get_contact(db, contact_id)
    db.delete(db_contact)
    db.commit()
    return db_contact

@app.get("/contacts/birthday", response_model=List[ContactResponse])
def get_contacts_with_upcoming_birthdays(db: Session = Depends(get_db)):
    today = date.today()
    next_week = today + timedelta(days=7)
    return db.query(Contact).filter(Contact.birth_date >= today, Contact.birth_date <= next_week).all()
