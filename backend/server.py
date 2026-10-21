from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File
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
import base64
import re, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("server")

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://127.0.0.1:27017/fintracker")
DB_NAME   = os.getenv("DB_NAME", "fintracker")

MASKED = re.sub(r"://(.*?):(.*?)@", r"://\\1:***@", MONGO_URL)
logger.info("🔧 Mongo URL efetiva: %s | DB=%s", MASKED, DB_NAME)

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET')
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET não definido. Configure no backend/.env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24  # 30 days

security = HTTPBearer()

# Enums
class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: UserRole = UserRole.USER
    avatar: Optional[str] = None  # Base64 encoded image
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    name: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Category Models
class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: TransactionType
    color: str = "#3B82F6"  # Default blue color
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CategoryCreate(BaseModel):
    name: str
    type: TransactionType
    color: Optional[str] = "#3B82F6"

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
    category_color: str
    total_amount: float
    transaction_count: int

class MonthlySummary(BaseModel):
    month: str
    income: float
    expense: float
    balance: float

class UserSummary(BaseModel):
    id: str
    name: str
    email: str
    role: str
    transactions_count: int
    created_at: datetime

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
    
    # Create default categories with colors
    default_categories = [
        {"name": "Salário", "type": TransactionType.INCOME, "color": "#10B981", "user_id": user.id},
        {"name": "Freelance", "type": TransactionType.INCOME, "color": "#059669", "user_id": user.id},
        {"name": "Alimentação", "type": TransactionType.EXPENSE, "color": "#EF4444", "user_id": user.id},
        {"name": "Transporte", "type": TransactionType.EXPENSE, "color": "#F59E0B", "user_id": user.id},
        {"name": "Lazer", "type": TransactionType.EXPENSE, "color": "#8B5CF6", "user_id": user.id},
        {"name": "Contas", "type": TransactionType.EXPENSE, "color": "#DC2626", "user_id": user.id}
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

# User Profile Routes
@api_router.get("/profile", response_model=User)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.put("/profile", response_model=User)
async def update_profile(profile_data: UserUpdate, current_user: User = Depends(get_current_user)):
    update_fields = {}
    
    if profile_data.name:
        update_fields['name'] = profile_data.name
    
    if profile_data.new_password and profile_data.current_password:
        # Verify current password
        user_doc = await db.users.find_one({"id": current_user.id})
        if not verify_password(profile_data.current_password, user_doc['password']):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        update_fields['password'] = hash_password(profile_data.new_password)
    
    if update_fields:
        await db.users.update_one({"id": current_user.id}, {"$set": update_fields})
        updated_user = await db.users.find_one({"id": current_user.id})
        return User(**{k: v for k, v in updated_user.items() if k != 'password'})
    
    return current_user

@api_router.post("/profile/avatar")
async def upload_avatar(avatar_data: dict, current_user: User = Depends(get_current_user)):
    # avatar_data should contain base64 encoded image
    if 'avatar' not in avatar_data:
        raise HTTPException(status_code=400, detail="Avatar data required")
    
    await db.users.update_one({"id": current_user.id}, {"$set": {"avatar": avatar_data['avatar']}})
    return {"message": "Avatar updated successfully"}

# User Management Routes (Admin only)
async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@api_router.get("/users", response_model=List[UserSummary])
async def get_users(admin_user: User = Depends(get_admin_user)):
    users = await db.users.find({}, {"password": 0}).to_list(100)
    user_summaries = []
    
    for user in users:
        transaction_count = await db.transactions.count_documents({"user_id": user['id']})
        user_summaries.append(UserSummary(
            id=user['id'],
            name=user['name'],
            email=user['email'],
            role=user.get('role', 'user'),
            transactions_count=transaction_count,
            created_at=user['created_at']
        ))
    
    return user_summaries

@api_router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role_data: dict, admin_user: User = Depends(get_admin_user)):
    if 'role' not in role_data or role_data['role'] not in ['user', 'admin']:
        raise HTTPException(status_code=400, detail="Valid role required")
    
    await db.users.update_one({"id": user_id}, {"$set": {"role": role_data['role']}})
    return {"message": "User role updated successfully"}

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
                category_color=category.get("color", "#3B82F6"),
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

@app.on_event("startup")
async def _ping_mongo():
    try:
        await client.admin.command("ping")
        logger.info("✅ Mongo conectado")
    except Exception as e:
        logger.exception("❌ Falha ao conectar no Mongo: %s", e)