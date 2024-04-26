from decimal import Decimal
from typing import Union, List
from pydantic import BaseModel
from passlib.hash import pbkdf2_sha256

from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select

from fastapi import Depends, FastAPI, HTTPException, Query

"""Team Models"""


class TeamBase(SQLModel):
    name: str = Field(index=True)
    headquarters: str


class Team(TeamBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    users: List["User"] = Relationship(back_populates="team")


class TeamCreate(TeamBase):
    pass


class TeamPublic(TeamBase):
    id: int


class TeamUpdate(SQLModel):
    name: str | None = None
    headquarters: str | None = None


"""User Models"""


class UserBase(SQLModel):
    name: str
    email: str | None = None
    age: int | None = Field(default=None, index=True)
    team_id: int | None = Field(default=None, foreign_key="team.id")


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str = Field()
    team: Team | None = Relationship(back_populates="users")


class UserCreate(UserBase):
    password: str


class UserPublic(UserBase):
    id: int


class UserUpdate(SQLModel):
    name: str | None = None
    email: str | None = None
    age: int | None = None
    password: str | None = None
    team_id: int | None = None


"""Item Models"""


class ItemBase(SQLModel):
    name: str
    price: Decimal = Field(default=0, max_digits=5, decimal_places=3)
    is_offer: bool = False
    units: int = Field(description="How much of the item is available")
    units_measurement: str = Field(description="Way of measuring the item")


class Item(ItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ItemCreate(ItemBase):
    pass


class ItemPublic(ItemBase):
    id: int


class ItemUpdate(SQLModel):
    name: str | None = None
    price: Decimal | None = None
    is_offer: bool | None = None
    units: int | None = None
    units_measurement: str | None = None


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


app = FastAPI()


@app.on_event("startup")
async def on_startup():
    create_db_and_tables()


def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)


"""Team Path operations"""


@app.post("/teams/", response_model=TeamPublic)
def create_team(*, session: Session = Depends(get_session), team: TeamCreate):
    # TODO: Refactor into crud.py file to reduce data duplication
    db_team = Team.model_validate(team)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team


@app.get("/teams/", response_model=List[TeamPublic])
def read_teams(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    teams = session.exec(select(Team).offset(offset).limit(limit)).all()
    return teams


@app.get("/teams/{team_id}", response_model=TeamPublic)
def read_team(*, team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@app.patch("/teams/{team_id}", response_model=TeamPublic)
def update_team(
    *,
    session: Session = Depends(get_session),
    team_id: int,
    team: TeamUpdate,
):
    db_team = session.get(Team, team_id)
    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")
    team_data = team.model_dump(exclude_unset=True)
    for key, value in team_data.items():
        setattr(db_team, key, value)
    session.add(db_team)
    session.commit()
    session.refresh(db_team)
    return db_team


@app.delete("/teams/{team_id}")
def delete_team(*, session: Session = Depends(get_session), team_id: int):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    session.delete(team)
    session.commit()
    return {"ok": True}


"""User Path operations"""


@app.post("/users/", response_model=UserPublic)
def create_user(*, session: Session = Depends(get_session), user: UserCreate):
    # TODO: Refactor into crud.py file to reduce data duplication
    hashed_password = hash_password(user.password)
    extra_data = {"hashed_password": hashed_password}
    db_user = User.model_validate(user, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.get("/users/", response_model=UserPublic)
def read_users(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    # TODO: Refactor into crud.py file to reduce data duplication
    users = session.exec(select(User).offset(offset).limit(limit)).all()
    return users


@app.get("/users/{user_id}", response_model=List[UserPublic])
def read_user(*, session: Session = Depends(get_session), user_id: int):
    # TODO: Refactor into crud.py file to reduce data duplication
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="No User found")
    return user


@app.patch("/users/{user_id}", response_model=UserPublic)
def update_user(
    *, session: Session = Depends(get_session), user_id: int, user: UserUpdate
):
    # TODO: Refactor into crud.py file to reduce data duplication
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(satus_response=404, detail="User not found")
    user_data = user.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = hash_password(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}")
def delete_user(*, session: Session = Depends(get_session), user_id: int):
    # TODO: Refactor into crud.py file to reduce data duplication
    user = session.get(User, user_id)
    if not User:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"ok": True}


"""Item Path operations"""


@app.post("/items/", response_model=ItemPublic)
def create_item(*, session: Session = Depends(get_session), item: ItemCreate):
    # TODO: Refactor into crud.py file to reduce data duplication
    db_item = Item.model_validate(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@app.get("/items/", response_model=List[ItemPublic])
def read_items(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    # TODO: Refactor into crud.py file to reduce data duplication
    items = session.exec(select(Item).offset(offset).limit(limit)).all()
    return items


@app.get("/items/{item_id}", response_model=ItemPublic)
def read_item(*, session: Session = Depends(get_session), item_id: int):
    # TODO: Refactor into crud.py file to reduce data duplication
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="No Item found")
    return item


@app.patch("/items/{item_id}", response_model=ItemPublic)
def update_item(
    *, session: Session = Depends(get_session), item_id: int, item: ItemUpdate
):
    # TODO: Refactor into crud.py file to reduce data duplication
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    item_data = item.model_dump(exclude_unset=True)
    db_item.sqlmodel_update(item_data)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@app.delete("/items/{item_id}")
def delete_item(*, session: Session = Depends(get_session), item_id: int):
    # TODO: Refactor into crud.py file to reduce data duplication
    item = session.get(Item, item_id)
    if not Item:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()
    return {"ok": True}
