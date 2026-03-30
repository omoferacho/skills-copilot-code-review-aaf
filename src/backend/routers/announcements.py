"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("/list")
def list_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements (respecting start and expiration dates)"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Find announcements that are currently active
    announcements = list(announcements_collection.find({
        "$and": [
            {"expiration_date": {"$gte": today}},
            {
                "$or": [
                    {"start_date": None},
                    {"start_date": {"$lte": today}}
                ]
            }
        ]
    }))
    
    # Convert ObjectId to string for JSON serialization
    for ann in announcements:
        ann["_id"] = str(ann["_id"])
    
    return announcements


@router.get("/all")
def get_all_announcements(username: str) -> List[Dict[str, Any]]:
    """Get all announcements for management (admin only)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")

    announcements = list(announcements_collection.find())
    
    # Convert ObjectId to string for JSON serialization
    for ann in announcements:
        ann["_id"] = str(ann["_id"])
    
    return announcements


@router.post("/create")
def create_announcement(
    username: str,
    title: str,
    message: str,
    expiration_date: str,
    start_date: str = None,
    priority: str = "normal"
) -> Dict[str, Any]:
    """Create a new announcement (authenticated users only)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Validate dates
    try:
        datetime.strptime(expiration_date, "%Y-%m-%d")
        if start_date:
            datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Create announcement
    announcement = {
        "title": title,
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "priority": priority,
        "created_by": username,
        "created_at": datetime.now().isoformat()
    }
    
    result = announcements_collection.insert_one(announcement)
    announcement["_id"] = str(result.inserted_id)
    return announcement


@router.put("/update")
def update_announcement(
    username: str,
    announcement_id: str,
    title: str,
    message: str,
    expiration_date: str,
    start_date: str = None,
    priority: str = "normal"
) -> Dict[str, Any]:
    """Update an announcement (authenticated users only)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Validate dates
    try:
        datetime.strptime(expiration_date, "%Y-%m-%d")
        if start_date:
            datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Update announcement
    try:
        result = announcements_collection.update_one(
            {"_id": ObjectId(announcement_id)},
            {
                "$set": {
                    "title": title,
                    "message": message,
                    "start_date": start_date,
                    "expiration_date": expiration_date,
                    "priority": priority,
                    "updated_by": username,
                    "updated_at": datetime.now().isoformat()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        # Return updated announcement
        announcement = announcements_collection.find_one({"_id": ObjectId(announcement_id)})
        announcement["_id"] = str(announcement["_id"])
        return announcement
    except Exception as e:
        if "invalid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid announcement ID")
        raise


@router.delete("/delete")
def delete_announcement(username: str, announcement_id: str) -> Dict[str, str]:
    """Delete an announcement (authenticated users only)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        result = announcements_collection.delete_one({"_id": ObjectId(announcement_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Announcement not found")
        
        return {"message": "Announcement deleted successfully"}
    except Exception as e:
        if "invalid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid announcement ID")
        raise
