from typing import List
from fastapi import FastAPI, HTTPException, Security, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from tortoise.contrib.pydantic import pydantic_model_creator
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
from jose import JWTError, jwt
import random
import string
import uvicorn
from models import LotteryTicket, AdminUser
from pydantic import BaseModel

# Configuration
SECRET_KEY = "your_secret_key"  # Replace with a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI instance
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
register_tortoise(
    app,
    db_url='sqlite://data/db.sqlite3',
    modules={'models': ['models']},
    generate_schemas=True,
    add_exception_handlers=True,
)

# JWT Token data model
class TokenData(BaseModel):
    username: str | None = None

# JWT token creation function
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# JWT token verification function
def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as e:
        raise credentials_exception
    return token_data

# OAuth2 password bearer scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency to get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)

# Authentication function
async def authenticate_user(username: str, password: str):
    user = await AdminUser.get_or_none(username=username)
    if user and user.verify_password(password):
        return user
    return None

# Route to get access token
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token}

# Pydantic model for LotteryTicket
LotteryTicket_Pydantic = pydantic_model_creator(LotteryTicket, name="LotteryTicket")

# Route to get all tickets
@app.get("/tickets/", response_model=List[LotteryTicket_Pydantic])
async def get_tickets():
    return await LotteryTicket_Pydantic.from_queryset(LotteryTicket.all())

# Route to generate a new ticket
@app.post("/generate_ticket/")
async def generate_ticket():
    ticket_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    ticket = await LotteryTicket.create(ticket_code=ticket_code)
    return {"ticket_code": ticket.ticket_code}

# Route to submit a ticket
@app.post("/submit_ticket/{ticket_code}")
async def submit_ticket(ticket_code: str):
    ticket = await LotteryTicket.get_or_none(ticket_code=ticket_code)
    if ticket is None:
        raise HTTPException(status_code=400, detail="Invalid ticket code")
    if ticket.used:
        raise HTTPException(status_code=400, detail="Ticket already used")

# Route to spin the wheel and get prize
@app.get("/spin/{ticket_code}")
async def spin(ticket_code: str):
    ticket = await LotteryTicket.get_or_none(ticket_code=ticket_code)
    if ticket is None:
        raise HTTPException(status_code=400, detail="Invalid ticket code")
    if ticket.used:
        raise HTTPException(status_code=400, detail="Ticket already used")

    result = get_random_result()  # Get the prize associated with the ticket code
    ticket.result = result
    ticket.used = True
    await ticket.save()

    return {"prize": result}

# Route to get the prize of a ticket
@app.get("/ticket_prize/{ticket_code}")
async def get_ticket_prize(ticket_code: str, current_user: AdminUser = Security(get_current_user)):
    ticket = await LotteryTicket.get_or_none(ticket_code=ticket_code)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.result is None:
        raise HTTPException(status_code=404, detail="No prize assigned to this ticket yet")
    return {"ticket_code": ticket.ticket_code, "prize": ticket.result}

# Function to get a random result/prize
def get_random_result():
    prizes = ["谢谢参与", "300", "600", "900", "1500", "3000", "8800", "再来一次"]
    probabilities = [0.10, 0.36, 0.25, 0.10, 0.5, 0.03, 0.01, 0.10]
    return random.choices(prizes, probabilities)[0]

# Run the FastAPI application
if __name__ == "__main__":
    uvicorn.run("main:app")
