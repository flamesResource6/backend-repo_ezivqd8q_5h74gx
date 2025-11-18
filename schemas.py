"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# -------------------- Notepad App Schemas --------------------

class Folder(BaseModel):
    """Folders collection schema
    Collection name: "folder"
    """
    name: str = Field(..., description="Folder name")
    color: Optional[str] = Field(None, description="Hex color or Tailwind color name")
    icon: Optional[str] = Field(None, description="Icon name for UI")

class Note(BaseModel):
    """Notes collection schema
    Collection name: "note"
    """
    title: str = Field("Untitled", description="Note title")
    content: str = Field("", description="Note content (Markdown/plain text)")
    folder_id: Optional[str] = Field(None, description="Associated folder id as string")
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for filtering")
    pinned: bool = Field(False, description="Pinned to top")

# Example schemas (kept for reference):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
