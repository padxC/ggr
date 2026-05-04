import base64

import re
import csv
import time
import subprocess

import json
import asyncio
import threading
import websockets
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

import requests

URL = "https://www.vpngate.net/api/iphone/"

SERVER_LIST = []
CONNECTED_CLIENTS = set()
CURRENT_VPN_STATUS = {"connected": False, "server": None}

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
            
        data = csv.reader(lines)

        servers = []
        for row in data:
            if len(row) >= 15:
                ping = row[3]
                ping = int(ping) if ping and ping != '-' else 9999
                

                tcpPort = getTcpPort(row[14]) # 14 is config base64 
                server = {
                    'hostname': row[0] + ".opengw.net:" + tcpPort,
                    'ip': row[1],
                    'ping': ping,
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
    
def getVpnStatus():
    try:
        result = subprocess.run(['powershell.exe', 'rasdial'], 
                              capture_output=True, text=True, timeout=5)
        return "Connected" in result.stdout
    except:
        return False
    
def disconnectVpn():
    try:
        subprocess.run(['powershell.exe', 'rasdial', '/disconnect'], capture_output=True)
        time.sleep(1)
        return True
    except:
        return False
    
def connectVpn(address, name):
    try:
        print("Disconnecting any existing VPN connections...")
        subprocess.run(['powershell.exe', 'rasdial', '/disconnect'], capture_output=True, text=True)
        time.sleep(1)

        subprocess.run(
            ['powershell.exe', 'Set-VpnConnection', '-Name', name, "-ServerAddress", address],
            capture_output=True,
            text=True
        )
        
        vpnStatus = subprocess.run(
            ['powershell.exe', 'Get-VpnConnection', '-Name', name, '|', 
             'Select-Object', 'Name,ServerAddress'],
            capture_output=True, text=True, check=False
        )
        print(vpnStatus.stdout)
        time.sleep(1)
        
        print("🔌 Establishing VPN connection...")
        connectResult = subprocess.run(
            ['powershell.exe', 'rasdial', name, 'vpn', 'vpn'],
            capture_output=True,
            text=True
        )

        if connectResult.returncode == 0:
            return True;
        else:
            print("Connection Failed: {connectResult.stdout}")
            return False;

    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False;
    
async def broadcast(message):
    """Send message to all connected clients"""
    if CONNECTED_CLIENTS:
        await asyncio.wait([client.send(json.dumps(message)) for client in CONNECTED_CLIENTS])
        

async def websocket_handler(websocket):
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
            'connected': getVpnStatus()
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
                
                result = connectVpn(hostname, name)
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
                result = disconnectVpn()
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
                    'connected': getVpnStatus()
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
        
class HTTPHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs

def run_http_server():
    handler = HTTPHandler
    httpd = HTTPServer(('localhost', 8080), handler)
    print("HTTP Server running on http://localhost:8080/frontend")
    httpd.serve_forever()

async def main():
    # Fetch initial server list
    print("Fetching server list...")
    fetchServers()
    print(f"Loaded {len(SERVER_LIST)} servers")
    
    # Start WebSocket server
    async with websockets.serve(websocket_handler, "localhost", 8765):
        print("=" * 50)
        print("VPN Controller - WebSocket Server")
        print("=" * 50)
        print(f"WebSocket: ws://localhost:8765")
        print(f"Web UI: http://localhost:8080")
        print("=" * 50)
        
        # Keep running
        await asyncio.Future()

if __name__ == "__main__":
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Open browser
    webbrowser.open('http://localhost:8080')
    
    # Run WebSocket server
    asyncio.run(main())