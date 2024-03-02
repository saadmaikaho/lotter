from typing import List
from fastapi import FastAPI, HTTPException
from tortoise.contrib.fastapi import register_tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from datetime import datetime, timedelta
import random
import uvicorn
import string
import csv

from models import LotteryTicket  # Import your LotteryTicket model from models.py
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()


# Add CORS middleware to allow requests from your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Create Pydantic model for LotteryTicket
LotteryTicket_Pydantic = pydantic_model_creator(LotteryTicket, name="LotteryTicket")

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

# Register Tortoise ORM
register_tortoise(
    app,
    db_url='sqlite://data/db.sqlite3',
    modules={'models': ['models']},
    generate_schemas=True,
    add_exception_handlers=True,
)

if __name__ == "__main__":
    uvicorn.run(app)
