"""A small inventory API used as a fixture for the extraction pipeline."""

from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    in_stock: bool = True


class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float


@app.get("/items", response_model=list[Item])
def list_items(category: Optional[str] = None, limit: int = 20):
    """List items in the inventory, optionally filtered by category."""
    return []


@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    """Fetch a single item by its numeric ID."""
    return Item(name="placeholder", price=0.0)


@app.post("/items", response_model=Item, status_code=201)
def create_item(item: ItemCreate):
    """Create a new inventory item."""
    return Item(name=item.name, description=item.description, price=item.price)


@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item: ItemCreate):
    """Replace an existing item's details."""
    return Item(name=item.name, description=item.description, price=item.price)


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    """Remove an item from the inventory."""
    return None
