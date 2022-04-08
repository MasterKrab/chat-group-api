from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.oauth2 import get_current_user

router = APIRouter(tags=["Channels"])


def normalize_members(db: Session, members):
    normalized_members = []

    for member in members:
        user = db.query(models.User).filter(models.User.id == member.user_id).first()

        normalized_members.append({
            "id": user.id,
            "username": user.username,
            "avatar": user.avatar
        })

    return normalized_members


sockets = []


@router.websocket("/channels")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    try:
        await websocket.accept()
        sockets.append(websocket)

        channels = db.query(models.Channel).order_by(models.Channel.created_at.asc()).all()

        normalized_channels = []

        for channel in channels:
            normalized_channels.append({
                "id": channel.id,
                "name": channel.name,
                "description": channel.description,
            })

        await websocket.send_json({"type": "channels", "channels": normalized_channels})

        while True:
            await websocket.receive_json()

    except WebSocketDisconnect:
        sockets.remove(websocket)

        await websocket.close()


@router.post("/channels")
async def create_channel(channel: schemas.Channel, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if db.query(models.Channel).filter(models.Channel.name == channel.name).first():
        raise HTTPException(status_code=400, detail="Channel already exists")

    channel = models.Channel(name=channel.name.strip().lower(), description=channel.description.strip())

    db.add(channel)
    db.commit()
    db.refresh(channel)

    data = {
        "type": "new",
        "channel": {
            "id": channel.id,
            "name": channel.name,
            "description": channel.description,
        }
    }

    for socket in sockets:
        await socket.send_json(data)

    return {"id": channel.id, "name": channel.name, "description": channel.description}
