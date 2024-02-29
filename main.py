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
import csv
import uvicorn
from models import LotteryTicket, AdminUser
from pydantic import BaseModel

class TokenData(BaseModel):
    username: str | None = None

# JWT configuration
SECRET_KEY = "your_secret_key"  # Replace with a secure key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# CORS configuration
origins = [
    "*",
    # Add other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

register_tortoise(
    app,
    db_url='sqlite://data/db.sqlite3',
    modules={'models': ['models']},
    generate_schemas=True,
    add_exception_handlers=True,
)

async def phoneNumberExists(phoneNumber: str):
    with open('data.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if phoneNumber == row[0]:
                return True
    return False

@app.post("/savePhoneNumber/")
async def save_phone_number(phone_data: dict):
    phoneNumber = phone_data.get('phoneNumber')
    if not phoneNumber:
        raise HTTPException(status_code=400, detail='Phone number is required')

    exists = await phoneNumberExists(phoneNumber)
    if exists:
        raise HTTPException(status_code=400, detail='Phone number already exists')

    try:
        with open('data.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([phoneNumber])
    except Exception as e:
        print(f"Error saving phone number: {e}")
        raise HTTPException(status_code=500, detail='Failed to save phone number')

    return {'message': 'Phone number saved successfully'}

@app.on_event("startup")
async def startup_event():
    print("Starting up...")
    await AdminUser.create_admin()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)

async def authenticate_user(username: str, password: str):
    user = await AdminUser.get_or_none(username=username)
    if user and user.verify_password(password):
        return user
    return None

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

LotteryTicket_Pydantic = pydantic_model_creator(LotteryTicket, name="LotteryTicket")

@app.get("/tickets/", response_model=List[LotteryTicket_Pydantic])
async def get_tickets():
    return await LotteryTicket_Pydantic.from_queryset(LotteryTicket.all())

@app.post("/generate_ticket/")
async def generate_ticket():
    ticket_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    ticket = await LotteryTicket.create(ticket_code=ticket_code)
    return {"ticket_code": ticket.ticket_code}

@app.post("/submit_ticket/{ticket_code}")
async def submit_ticket(ticket_code: str):
    ticket = await LotteryTicket.get_or_none(ticket_code=ticket_code)
    if ticket is None:
        raise HTTPException(status_code=400, detail="Invalid ticket code")
    if ticket.used:
        # return {"result": "Ticket already used"}
        raise HTTPException(status_code=400, detail="Ticket already used")
    
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

@app.get("/ticket_prize/{ticket_code}")
async def get_ticket_prize(ticket_code: str):
    # Retrieve prize information for the given ticket code
    ticket = await LotteryTicket.get_or_none(ticket_code=ticket_code)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    elif not ticket.used:
        return {"message": "Ticket code has not been used yet"}
    else:
        return {"ticket_code": ticket_code, "prize": ticket.result}


def get_random_result():
    # Simulate getting a random result (prize)
    prizes = ["谢谢参与", "300", "600", "900", "1500", "3000", "8800", "再来一次"]
    return random.choice(prizes)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
