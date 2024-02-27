from typing import List
from fastapi import FastAPI, HTTPException
from tortoise.contrib.fastapi import register_tortoise
import random
import string
import uvicorn
from models import LotteryTicket
from pydantic import BaseModel

# FastAPI instance
app = FastAPI()

# Database initialization
register_tortoise(
    app,
    db_url='sqlite://data/db.sqlite3',
    modules={'models': ['models']},
    generate_schemas=True,
    add_exception_handlers=True,
)

# Pydantic model for LotteryTicket
class LotteryTicket_Pydantic(BaseModel):
    ticket_code: str

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
async def get_ticket_prize(ticket_code: str):
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
