from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # self.active_connections: list[WebSocket] = []
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        # self.active_connections.append(websocket)
        self.active_connections[user_id] = websocket

    # def disconnect(self, websocket: WebSocket):
    #     self.active_connections.remove(websocket)

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def broadcast(self, data: dict, sender: WebSocket = None):
        for connection in self.active_connections:
            if connection != sender:
                await connection.send_json(data)

    async def send_private_message(self, receiver_id: str, message: dict):
        print("self.active_connections", self.active_connections)
        websocket = self.active_connections.get(receiver_id)
        print("Found websocket for receiver:", websocket)
        if websocket:
            print("Sending message to receiver:", message)
            await websocket.send_json(message)
