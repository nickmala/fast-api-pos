from decimal import Decimal
from typing import Union
from pydantic import BaseModel

from sqlmodel import Field, Session, SQLModel, create_engine, select

from fastapi import FastAPI

app = FastAPI()


class Item(SQLModel):
    name: str
    price: Decimal = Field(default=0, max_digits=5, decimal_places=3)
    is_offer: bool = False
    units: int = Field(description="How much of the item is available")
    units_measurement: str = Field(description="Way of measuring the item")


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# @app.get("/")
# async def read_root():
#     return {"Hello": "World"}


# @app.get("/items/{item_id}")
# async def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}


# @app.put("/items/{item_id}")
# def update_item(item_id: int, item: Item):
#     return {"item_name": item.name, "item_id": item_id}


@app.put("/items/")
def create_item(
    name: str, price: Decimal, is_offer: bool, units: int, units_measurement: str
):
    create_db_and_tables()
    print(f"here: {name}")

    item = Item(
        name=name,
        price=price,
        is_offer=is_offer,
        units=units,
        units_measurement=units_measurement,
    )

    # with Session(engine) as session:
    #     session.add(item)
    #     session.commit()

    return {"Successfully created item: {item}"}
