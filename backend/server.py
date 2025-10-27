from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
import base64
from twilio.rest import Client
import requests

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_DAYS = int(os.environ.get('JWT_EXPIRATION_DAYS', 7))

# Twilio Config
twilio_client = Client(
    os.environ['TWILIO_ACCOUNT_SID'],
    os.environ['TWILIO_AUTH_TOKEN']
)
TWILIO_PHONE = os.environ['TWILIO_PHONE_NUMBER']

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ['EMERGENT_LLM_KEY']

app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Models
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str
    role: str = "user"  # user or admin

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    phone: str
    role: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GoogleAuthSession(BaseModel):
    session_id: str

class SessionData(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str]
    session_token: str

class RationCardApplication(BaseModel):
    name: str
    address: str
    family_members: int
    aadhaar: str
    income_proof: str  # base64 encoded
    photo: str  # base64 encoded

class RationCard(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    card_number: Optional[str] = None
    name: str
    address: str
    family_members: int
    aadhaar: str
    income_proof: str
    photo: str
    status: str = "pending"  # pending, approved, rejected, fake
    ai_verification_result: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RationCardUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    family_members: Optional[int] = None
    aadhaar: Optional[str] = None
    income_proof: Optional[str] = None
    photo: Optional[str] = None

class TokenDistribution(BaseModel):
    user_ids: List[str]
    message: str
    time_slot: str

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str, role: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": expiration
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def verify_ration_card_with_ai(card_data: dict) -> dict:
    """Use Claude Sonnet 4 to verify ration card authenticity"""
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"verification_{card_data['id']}",
            system_message="You are an expert at detecting fake documents and verifying ration card applications. Analyze the provided information and determine if it appears genuine or fake."
        ).with_model("anthropic", "claude-3-7-sonnet-20250219")
        
        message = UserMessage(
            text=f"""Analyze this ration card application:
            Name: {card_data['name']}
            Address: {card_data['address']}
            Family Members: {card_data['family_members']}
            Aadhaar: {card_data['aadhaar']}
            
            Check for:
            1. Aadhaar format validity (12 digits)
            2. Reasonable family member count
            3. Address completeness
            4. Any suspicious patterns
            
            Respond with: GENUINE or FAKE followed by a brief reason."""
        )
        
        response = await chat.send_message(message)
        return {
            "result": "fake" if "FAKE" in response.upper() else "genuine",
            "details": response
        }
    except Exception as e:
        logging.error(f"AI verification error: {str(e)}")
        return {"result": "error", "details": str(e)}

# Auth Endpoints
@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        role=user_data.role
    )
    
    user_dict = user.model_dump()
    user_dict['password'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    token = create_jwt_token(user.id, user.email, user.role)
    return {"token": token, "user": user}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user['id'], user['email'], user['role'])
    user_obj = User(**user)
    return {"token": token, "user": user_obj}

@api_router.post("/auth/google-session")
async def google_session(data: GoogleAuthSession):
    """Process Google OAuth session ID"""
    try:
        response = requests.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": data.session_id}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid session")
        
        session_data = response.json()
        
        # Check if user exists
        existing_user = await db.users.find_one({"email": session_data['email']}, {"_id": 0})
        
        if existing_user:
            user = User(**existing_user)
        else:
            # Create new user
            user = User(
                name=session_data['name'],
                email=session_data['email'],
                phone="",
                role="user"
            )
            user_dict = user.model_dump()
            user_dict['password'] = hash_password(str(uuid.uuid4()))  # Random password for OAuth users
            user_dict['created_at'] = user_dict['created_at'].isoformat()
            await db.users.insert_one(user_dict)
        
        # Store session
        session_expiry = datetime.now(timezone.utc) + timedelta(days=7)
        await db.sessions.insert_one({
            "session_token": session_data['session_token'],
            "user_id": user.id,
            "expires_at": session_expiry.isoformat()
        })
        
        token = create_jwt_token(user.id, user.email, user.role)
        return {"token": token, "user": user, "session_token": session_data['session_token']}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    return user

# Ration Card Endpoints
@api_router.post("/ration-cards/apply")
async def apply_ration_card(application: RationCardApplication, user: User = Depends(get_current_user)):
    # Check if user already has a pending or approved application
    existing = await db.ration_cards.find_one({
        "user_id": user.id,
        "status": {"$in": ["pending", "approved"]}
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="You already have an active application")
    
    card = RationCard(
        user_id=user.id,
        name=application.name,
        address=application.address,
        family_members=application.family_members,
        aadhaar=application.aadhaar,
        income_proof=application.income_proof,
        photo=application.photo
    )
    
    # AI Verification
    card_dict = card.model_dump()
    ai_result = await verify_ration_card_with_ai(card_dict)
    card_dict['ai_verification_result'] = ai_result['details']
    
    if ai_result['result'] == 'fake':
        card_dict['status'] = 'fake'
    
    card_dict['created_at'] = card_dict['created_at'].isoformat()
    card_dict['updated_at'] = card_dict['updated_at'].isoformat()
    
    await db.ration_cards.insert_one(card_dict)
    
    return {"message": "Application submitted", "card": card, "ai_verification": ai_result}

@api_router.get("/ration-cards/my-card")
async def get_my_card(user: User = Depends(get_current_user)):
    card = await db.ration_cards.find_one({"user_id": user.id}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=404, detail="No ration card found")
    return card

@api_router.put("/ration-cards/update")
async def update_ration_card(update: RationCardUpdate, user: User = Depends(get_current_user)):
    card = await db.ration_cards.find_one({"user_id": user.id, "status": {"$in": ["approved", "pending"]}})
    if not card:
        raise HTTPException(status_code=404, detail="No active ration card found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.ration_cards.update_one(
        {"id": card['id']},
        {"$set": update_data}
    )
    
    return {"message": "Ration card updated successfully"}

# Admin Endpoints
@api_router.get("/admin/cards")
async def get_all_cards(admin: User = Depends(get_admin_user)):
    cards = await db.ration_cards.find({}, {"_id": 0}).to_list(1000)
    return cards

@api_router.put("/admin/cards/{card_id}/approve")
async def approve_card(card_id: str, admin: User = Depends(get_admin_user)):
    card = await db.ration_cards.find_one({"id": card_id})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Generate card number
    card_number = f"RC{str(uuid.uuid4())[:8].upper()}"
    
    await db.ration_cards.update_one(
        {"id": card_id},
        {"$set": {
            "status": "approved",
            "card_number": card_number,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Card approved", "card_number": card_number}

@api_router.put("/admin/cards/{card_id}/reject")
async def reject_card(card_id: str, admin: User = Depends(get_admin_user)):
    await db.ration_cards.update_one(
        {"id": card_id},
        {"$set": {
            "status": "rejected",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Card rejected"}

@api_router.delete("/admin/cards/{card_id}")
async def delete_card(card_id: str, admin: User = Depends(get_admin_user)):
    result = await db.ration_cards.delete_one({"id": card_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Card not found")
    return {"message": "Card deleted"}

@api_router.post("/admin/distribute-tokens")
async def distribute_tokens(distribution: TokenDistribution, admin: User = Depends(get_admin_user)):
    """Send SMS tokens to selected users"""
    sent_count = 0
    failed = []
    
    for user_id in distribution.user_ids[:50]:  # Limit to 50
        try:
            user = await db.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get('phone'):
                message = twilio_client.messages.create(
                    body=f"{distribution.message}\nTime Slot: {distribution.time_slot}",
                    from_=TWILIO_PHONE,
                    to=user['phone']
                )
                sent_count += 1
        except Exception as e:
            failed.append({"user_id": user_id, "error": str(e)})
    
    return {
        "message": f"Tokens sent to {sent_count} users",
        "sent_count": sent_count,
        "failed": failed
    }

@api_router.get("/admin/users")
async def get_all_users(admin: User = Depends(get_admin_user)):
    users = await db.users.find({"role": "user"}, {"_id": 0, "password": 0}).to_list(1000)
    return users

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()