from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.oauth2 import verify_access_token

router = APIRouter(tags=["Chat"])

channels = {}


@router.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket, id: int, token: str, db: Session = Depends(get_db)):
    await websocket.accept()

    token = verify_access_token(token)

    if token is None:
        current_user = None
    else:
        current_user = db.query(models.User).filter(models.User.id == token.id).first()

    channel = db.query(models.Channel).filter(models.Channel.id == id).first()

    if channel is None:
        return await websocket.close()

    await websocket.send_json({"type": "joined", "name": channel.name, "description": channel.description})

    if channels.get(id) is None:
        channels[id] = []

    channels[id].append(websocket)

    messages = [{
        "content": message.content,
        "created_at": message.created_at.isoformat(),
        "user": {
            "id": message.user.id,
            "username": message.user.username,
            "avatar": message.user.avatar
        }
    } for message in channel.messages]

    await websocket.send_json({"type": "messages", "messages": messages})

    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "message" and current_user is not None:
                message = models.Message(content=data["content"].strip(), user_id=current_user.id, channel_id=id)

                db.add(message)
                db.commit()
                db.refresh(message)

                for socket in channels[id]:
                    await socket.send_json({
                        "type": "message",
                        "message": {
                            "content": message.content,
                            "created_at": message.created_at.isoformat(),
                            "user": {
                                "id": message.user.id,
                                "username": message.user.username,
                                "avatar": message.user.avatar
                            }
                        }
                    })
    except WebSocketDisconnect as error:
        print(error)

        channels[id].remove(websocket)

        await websocket.close()
