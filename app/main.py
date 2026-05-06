import base64
import re
import csv
import json
import asyncio
import threading
import websockets
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import requests
from vpn import VPN
from monitor import Monitor

URL = "https://www.vpngate.net/api/iphone/"

SERVER_LIST = []
CONNECTED_CLIENTS = set()
CURRENT_VPN_STATUS = {"connected": False, "server": None}
MONITOR = Monitor("trgame.exe")

def getTcpPort(config):
    try:
        data = base64.b64decode(config).decode('utf-8', errors='ignore')
        tcpMatch = re.search(r'proto\s+tcp.*?remote\s+\S+\s+(\d+)', data, re.DOTALL | re.IGNORECASE)
        
        if tcpMatch:
            return tcpMatch.group(1)
        
        return None
    except Exception as e:
        print(f"Error parsing TCP port: {e}")
        return None

def fetchServers():
    global SERVER_LIST
    try:
        response = requests.get(URL, timeout=10)
        data = response.text
        
        lines = data.strip().split('\n')
        if lines[0].startswith('*'): # skip the first line
            lines = lines[1:]
            
        if lines[0].startswith('#'): # skip the header
            header_line = lines[0].lstrip('#')  # Remove the # at the beginning
            headers = header_line.split(',')
            
            print("="*80)
            for idx, header in enumerate(headers):
                print(f"{idx:2d}: {header}")
            print("="*80 + "\n")
            
            # Skip the header line
            lines = lines[1:]
            
        data = csv.reader(lines)

        servers = []
        for row in data:
            if len(row) >= 15:
                tcpPort = getTcpPort(row[14]) # 14 is config base64 
                server = {
                    'hostname': row[0] + ".opengw.net:" + tcpPort,
                    'ip': row[1],
                    'ping': row[3],
                    'speed': row[4],
                    'countryShort': row[6],
                    'uptime': row[8],
                    'totalUsers': row[9],
                    'totalTraffic': row[10],

                }
                servers.append(server)
            
        SERVER_LIST = servers
        return servers
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []
    
async def broadcast(message):
    """Send message to all connected clients"""
    if CONNECTED_CLIENTS:
        await asyncio.wait([client.send(json.dumps(message)) for client in CONNECTED_CLIENTS])
        

async def wsService(websocket):
    """Handle WebSocket connections"""
    CONNECTED_CLIENTS.add(websocket)
    print(f"Client connected. Total clients: {len(CONNECTED_CLIENTS)}")
    
    try:
        # Send initial data
        await websocket.send(json.dumps({
            'type': 'connection_status',
            'connected': True,
            'message': 'Connected to VPN Controller'
        }))
        
        # Send current VPN status
        await websocket.send(json.dumps({
            'type': 'vpn_status',
            'connected': VPN.isConnecting()
        }))
        
        # Send server list (simple, matching your fetchServers structure)
        if SERVER_LIST:
            formatted_servers = []
            for server in SERVER_LIST:
                formatted_servers.append({
                    'hostname': server['hostname'],
                    'ip': server['ip'],
                    'ping': server['ping'],
                    'speed': server['speed'],
                    'countryShort': server['countryShort'],
                    'uptime': server['uptime'],
                    'totalUsers': server['totalUsers'],
                    'totalTraffic': server['totalTraffic']
                })

            await websocket.send(json.dumps({
                'type': 'server_list',
                'servers': formatted_servers
            }))
        
        # Handle incoming messages
        async for message in websocket:
            data = json.loads(message)
            command = data.get('command')
            
            if command == 'connect':
                hostname = data.get('hostname')
                name = data.get('name', 'MyVPN')
                
                result = VPN.connect(hostname, name, "vpn", "vpn")
                
                if result:
                    # Start monitoring with callback to disconnect VPN
                    MONITOR.start(callback=lambda: VPN.disconnect())

                await broadcast({
                    'type': 'vpn_status',
                    'connected': result,
                    'server': hostname
                })
                await websocket.send(json.dumps({
                    'type': 'command_result',
                    'command': 'connect',
                    'success': result,
                    'message': f"Connected to {hostname}" if result else "Connection failed"
                }))
                
            elif command == 'disconnect':
                result = VPN.disconnect()
                MONITOR.stop() 
                await broadcast({
                    'type': 'vpn_status',
                    'connected': not result
                })
                await websocket.send(json.dumps({
                    'type': 'command_result',
                    'command': 'disconnect',
                    'success': result,
                    'message': "VPN Disconnected" if result else "Disconnect failed"
                }))
                
            elif command == 'get_status':
                await websocket.send(json.dumps({
                    'type': 'vpn_status',
                    'connected': VPN.isConnecting()
                }))
                
            elif command == 'refresh_servers':
                servers = fetchServers()
                formatted_servers = []
                for server in servers:
                    formatted_servers.append({
                        'hostname': server['hostname'],
                        'ip': server['ip'],
                        'ping': server['ping'],
                        'speed': server['speed'],
                        'countryShort': server['countryShort'],
                        'uptime': server['uptime'],
                        'totalUsers': server['totalUsers'],
                        'totalTraffic': server['totalTraffic']
                    })
                await websocket.send(json.dumps({
                    'type': 'server_list',
                    'servers': formatted_servers
                }))
                
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        CONNECTED_CLIENTS.remove(websocket)
        

def startHTTP():
    httpd = HTTPServer(('localhost', 8080), SimpleHTTPRequestHandler)
    print("HTTP Server running on http://localhost:8080")
    httpd.serve_forever()

async def main():
    # Fetch initial server list
    print("Fetching server list...")
    fetchServers()
    print(f"Loaded {len(SERVER_LIST)} servers")
    
    # Start WebSocket server
    async with websockets.serve(wsService, "localhost", 8766):
        print("=" * 50)
        print(f"WebSocket: ws://localhost:8766")
        print(f"Web UI: http://localhost:8080")
        print("=" * 50)
        
        # Keep running
        await asyncio.Future()

if __name__ == "__main__":
    threading.Thread(target=startHTTP, daemon=True).start()
    # Open browser
    webbrowser.open('http://localhost:8080')
    # Run WebSocket server
    asyncio.run(main())