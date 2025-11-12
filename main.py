import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document, get_documents
from schemas import Contactmessage

app = FastAPI(title="Agency API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Agency API is running"}

# Public endpoint to submit a contact message
class ContactIn(BaseModel):
    name: str
    email: str
    company: Optional[str] = None
    message: str
    budget: Optional[str] = None
    service: Optional[str] = None

@app.post("/api/contact")
async def submit_contact(payload: ContactIn):
    try:
        # Validate via schema and persist
        data = Contactmessage(**payload.model_dump())
        inserted_id = create_document("contactmessage", data)
        return {"success": True, "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Admin/listing endpoint (basic)
@app.get("/api/contact", response_model=List[dict])
async def list_contacts(limit: int = 50):
    try:
        docs = get_documents("contactmessage", limit=limit)
        # Convert ObjectId to string if present
        cleaned = []
        for d in docs:
            d = {k: (str(v) if k == "_id" else v) for k, v in d.items()}
            cleaned.append(d)
        return cleaned
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
