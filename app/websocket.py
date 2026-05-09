import asyncio
import inspect
import json
import time
import websockets

class Ws:
    def __init__(self, host="localhost", port=8766, maxClients=2):
        self.host = host
        self.port = port
        self.clients = set()
        self.maxClients = maxClients
        self.server = None
        self.running = False
        self.messageProcessor = {}
        
    def on(self, command, processor):
        self.messageProcessor[command] = processor
        
    async def start(self):
        self.running = True
        self.server = await websockets.serve(
            self._processConnection,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        print(f"WebSocket running on ws://{self.host}:{self.port}")
        await self.server.wait_closed()
    
        
    async def _processConnection(self, websocket):
        if len(self.clients) >= self.maxClients:
            print(f"Connection rejected: Max clients ({self.maxClients}) reached")
            await websocket.close(1008, "Max connections limit reached")
            return

        await self._addClient(websocket)
        
        try:
            await self.send(websocket, {
                "type": "connected",
                "message": "Connected to server"
            })
            
            async for message in websocket:
                await self._processMessage(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self._removeClient(websocket)
        
    async def send(self, websocket, message):
        try:
            await websocket.send(json.dumps(message))
            return True
        except:
            await self._removeClient(websocket)
            return False
    
    async def _addClient(self, websocket):
        self.clients.add(websocket)
        print(f"Client connected. Total: {len(self.clients)}")
        
    async def _removeClient(self, websocket):
        if websocket not in self.clients:
            return
        self.clients.discard(websocket)
        print(f"Client disconnected. Total: {len(self.clients)}")
        
    async def _processMessage(self, websocket, message):
        try:
            data = json.loads(message)
            command = data.get("command")
            
            if command in self.messageProcessor:
                handler = self.messageProcessor[command]
                if inspect.iscoroutinefunction(handler):
                    await handler(websocket, data)
                else:
                    handler(websocket, data)
            else:
                await self.send(websocket, {
                    "type": "error",
                    "message": f"Unknown command: {command}"
                })

        except json.JSONDecodeError:
            await self.send(websocket, {
                "type": "error",
                "message": "Invalid JSON"
            })
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            await self.send(websocket, {
                "type": "error",
                "message": "Internal error"
            })
            
    async def stop(self):
        self.running = False
        for client in list(self.clients):
            try:
                await client.close()
            except:
                pass
            await self._removeClient(client)
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        print("WebSocket server stopped")
    
    async def broadcast(self, message, exclude=None):
        if not self.clients:
            return
            
        exclude = exclude or set()
        dead = set()
        msg = json.dumps(message)
        
        for client in list(self.clients):
            if client in exclude:
                continue
            try:
                await client.send(msg)
            except:
                dead.add(client)
                
        for client in dead:
            await self._removeClient(client)