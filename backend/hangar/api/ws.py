from __future__ import annotations
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from ..core.bus import bus
from ..security import validate_websocket_handshake

logger = logging.getLogger("hangar.ws")
router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # 1. Security handshake verification
    is_valid, reason = validate_websocket_handshake(websocket)
    if not is_valid:
        logger.warning("Rejected WebSocket handshake: %s", reason)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=reason)
        return

    # Check for subprotocol
    requested_protocols = websocket.headers.get("sec-websocket-protocol", "").split(",")
    selected_subprotocol = None
    for p in requested_protocols:
        if "x-hangar-client" in p.strip().lower():
            selected_subprotocol = p.strip()
            break

    await websocket.accept(subprotocol=selected_subprotocol)
    await bus.register(websocket)

    try:
        while True:
            text = await websocket.receive_text()
            try:
                data = json.loads(text)
            except Exception:
                continue

            # Handle subscription command: {sub: "status"|"events"|"metrics"|"logs:<cid>"}
            if "sub" in data and isinstance(data["sub"], str):
                channel = data["sub"]
                await bus.subscribe(websocket, channel)
                # Ack subscription
                await websocket.send_text(json.dumps({"type": "subscribed", "channel": channel}))

            # Handle unsubscribe command: {unsub: "..."}
            elif "unsub" in data and isinstance(data["unsub"], str):
                channel = data["unsub"]
                await bus.unsubscribe(websocket, channel)
                await websocket.send_text(json.dumps({"type": "unsubscribed", "channel": channel}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WebSocket exception: %s", e)
    finally:
        await bus.unregister(websocket)

