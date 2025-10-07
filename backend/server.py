from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24  # 30 days

security = HTTPBearer()

# Enums
class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    name: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Category Models
class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: TransactionType
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CategoryCreate(BaseModel):
    name: str
    type: TransactionType

# Transaction Models
class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    amount: float
    type: TransactionType
    category_id: str
    user_id: str
    date: str  # ISO date string
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TransactionCreate(BaseModel):
    description: str
    amount: float
    type: TransactionType
    category_id: str
    date: str  # ISO date string

# Dashboard Models
class DashboardSummary(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    transactions_count: int

class CategorySummary(BaseModel):
    category_name: str
    total_amount: float
    transaction_count: int

class MonthlySummary(BaseModel):
    month: str
    income: float
    expense: float
    balance: float

# Authentication helper functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_current_user(user_id: str = Depends(verify_token)) -> User:
    user = await db.users.find_one({"id": user_id})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Authentication Routes
@api_router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_dict = user_data.dict()
    user_dict['password'] = hash_password(user_dict['password'])
    user = User(**{k: v for k, v in user_dict.items() if k != 'password'})
    
    await db.users.insert_one({**user.dict(), 'password': user_dict['password']})
    
    # Create default categories
    default_categories = [
        {"name": "Salário", "type": TransactionType.INCOME, "user_id": user.id},
        {"name": "Freelance", "type": TransactionType.INCOME, "user_id": user.id},
        {"name": "Alimentação", "type": TransactionType.EXPENSE, "user_id": user.id},
        {"name": "Transporte", "type": TransactionType.EXPENSE, "user_id": user.id},
        {"name": "Lazer", "type": TransactionType.EXPENSE, "user_id": user.id},
        {"name": "Contas", "type": TransactionType.EXPENSE, "user_id": user.id}
    ]
    
    categories = [Category(**cat_data) for cat_data in default_categories]
    await db.categories.insert_many([cat.dict() for cat in categories])
    
    # Generate token
    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.post("/login", response_model=Token)
async def login(login_data: UserLogin):
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc or not verify_password(login_data.password, user_doc['password']):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    user = User(**{k: v for k, v in user_doc.items() if k != 'password'})
    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token, token_type="bearer", user=user)

# Category Routes
@api_router.get("/categories", response_model=List[Category])
async def get_categories(current_user: User = Depends(get_current_user)):
    categories = await db.categories.find({"user_id": current_user.id}).to_list(100)
    return [Category(**cat) for cat in categories]

@api_router.post("/categories", response_model=Category)
async def create_category(category_data: CategoryCreate, current_user: User = Depends(get_current_user)):
    category = Category(**category_data.dict(), user_id=current_user.id)
    await db.categories.insert_one(category.dict())
    return category

# Transaction Routes
@api_router.get("/transactions", response_model=List[Transaction])
async def get_transactions(current_user: User = Depends(get_current_user)):
    transactions = await db.transactions.find({"user_id": current_user.id}).sort("date", -1).to_list(1000)
    return [Transaction(**trans) for trans in transactions]

@api_router.post("/transactions", response_model=Transaction)
async def create_transaction(transaction_data: TransactionCreate, current_user: User = Depends(get_current_user)):
    # Verify category belongs to user
    category = await db.categories.find_one({"id": transaction_data.category_id, "user_id": current_user.id})
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    transaction = Transaction(**transaction_data.dict(), user_id=current_user.id)
    await db.transactions.insert_one(transaction.dict())
    return transaction

@api_router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str, current_user: User = Depends(get_current_user)):
    result = await db.transactions.delete_one({"id": transaction_id, "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}

# Dashboard Routes
@api_router.get("/dashboard/summary", response_model=DashboardSummary)
async def get_dashboard_summary(current_user: User = Depends(get_current_user)):
    transactions = await db.transactions.find({"user_id": current_user.id}).to_list(1000)
    
    total_income = sum(t['amount'] for t in transactions if t['type'] == TransactionType.INCOME)
    total_expense = sum(t['amount'] for t in transactions if t['type'] == TransactionType.EXPENSE)
    balance = total_income - total_expense
    
    return DashboardSummary(
        total_income=total_income,
        total_expense=total_expense,
        balance=balance,
        transactions_count=len(transactions)
    )

@api_router.get("/dashboard/categories", response_model=List[CategorySummary])
async def get_categories_summary(current_user: User = Depends(get_current_user)):
    pipeline = [
        {"$match": {"user_id": current_user.id}},
        {"$group": {
            "_id": "$category_id",
            "total_amount": {"$sum": "$amount"},
            "transaction_count": {"$sum": 1}
        }}
    ]
    
    results = await db.transactions.aggregate(pipeline).to_list(100)
    
    summaries = []
    for result in results:
        category = await db.categories.find_one({"id": result["_id"]})
        if category:
            summaries.append(CategorySummary(
                category_name=category["name"],
                total_amount=result["total_amount"],
                transaction_count=result["transaction_count"]
            ))
    
    return summaries

@api_router.get("/dashboard/monthly", response_model=List[MonthlySummary])
async def get_monthly_summary(current_user: User = Depends(get_current_user)):
    transactions = await db.transactions.find({"user_id": current_user.id}).to_list(1000)
    
    monthly_data = {}
    for trans in transactions:
        month_key = trans['date'][:7]  # YYYY-MM format
        if month_key not in monthly_data:
            monthly_data[month_key] = {"income": 0, "expense": 0}
        
        if trans['type'] == TransactionType.INCOME:
            monthly_data[month_key]["income"] += trans['amount']
        else:
            monthly_data[month_key]["expense"] += trans['amount']
    
    summaries = []
    for month, data in sorted(monthly_data.items()):
        summaries.append(MonthlySummary(
            month=month,
            income=data["income"],
            expense=data["expense"],
            balance=data["income"] - data["expense"]
        ))
    
    return summaries

# Test route
@api_router.get("/")
async def root():
    return {"message": "Financial System API"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()