import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Note, Folder

app = FastAPI(title="Notepad API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NoteCreate(BaseModel):
    title: Optional[str] = "Untitled"
    content: Optional[str] = ""
    folder_id: Optional[str] = None
    tags: Optional[List[str]] = []
    pinned: bool = False

class FolderCreate(BaseModel):
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "Notepad Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# ---------------- Notes ----------------
@app.post("/api/notes")
def create_note(note: NoteCreate):
    data = Note(**note.model_dump())
    inserted_id = create_document("note", data)
    return {"id": inserted_id}

@app.get("/api/notes")
def list_notes(folder_id: Optional[str] = None, q: Optional[str] = None):
    filter_dict = {}
    if folder_id:
        filter_dict["folder_id"] = folder_id
    docs = get_documents("note", filter_dict)
    # Simple search filter
    if q:
        q_lower = q.lower()
        docs = [d for d in docs if q_lower in (d.get("title", "").lower() + " " + d.get("content", "").lower())]
    # Convert ObjectId to string
    for d in docs:
        if isinstance(d.get("_id"), ObjectId):
            d["id"] = str(d.pop("_id"))
    return {"items": docs}

@app.delete("/api/notes/{note_id}")
def delete_note(note_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        result = db["note"].delete_one({"_id": ObjectId(note_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"success": True}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid note id")

@app.patch("/api/notes/{note_id}")
def update_note(note_id: str, payload: dict):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    update = {k: v for k, v in payload.items() if k in {"title", "content", "folder_id", "tags", "pinned"}}
    if not update:
        return {"success": True}
    update["updated_at"] = __import__("datetime").datetime.utcnow()
    try:
        result = db["note"].update_one({"_id": ObjectId(note_id)}, {"$set": update})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"success": True}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid note id")

# ---------------- Folders ----------------
@app.post("/api/folders")
def create_folder(folder: FolderCreate):
    data = Folder(**folder.model_dump())
    inserted_id = create_document("folder", data)
    return {"id": inserted_id}

@app.get("/api/folders")
def list_folders():
    docs = get_documents("folder")
    for d in docs:
        if isinstance(d.get("_id"), ObjectId):
            d["id"] = str(d.pop("_id"))
    return {"items": docs}

@app.delete("/api/folders/{folder_id}")
def delete_folder(folder_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        # prevent delete if notes exist in folder
        notes_count = db["note"].count_documents({"folder_id": folder_id})
        if notes_count > 0:
            raise HTTPException(status_code=400, detail="Folder contains notes. Move or delete them first.")
        result = db["folder"].delete_one({"_id": ObjectId(folder_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Folder not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid folder id")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
