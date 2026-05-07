import base64
import re
import csv
import asyncio
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import requests
from vpn import VPN
from monitor import Monitor
from websocket import Ws

URL = "https://www.vpngate.net/api/iphone/"
SERVER_LIST = []
MONITOR = Monitor("trgame.exe")
WS = None

def getTcpPort(config):
    try:
        data = base64.b64decode(config).decode('utf-8', errors='ignore')
        tcpMatch = re.search(r'proto\s+tcp.*?remote\s+\S+\s+(\d+)', data, re.DOTALL | re.IGNORECASE)
        return tcpMatch.group(1) if tcpMatch else None
    except Exception as e:
        print(f"Error parsing TCP port: {e}")
        return None

def fetchServers():
    global SERVER_LIST
    try:
        response = requests.get(URL, timeout=10)
        lines = response.text.strip().split('\n')

        if lines[0].startswith('*'): # skip the first line
            lines = lines[1:]
        if lines[0].startswith('#'): # skip the header
            header_line = lines[0].lstrip('#')  # Remove the # at the beginning
            headers = header_line.split(',')
            
            print("="*80)
            for idx, header in enumerate(headers):
                print(f"{idx:2d}: {header}")
            print("="*80 + "\n")
            lines = lines[1:] # Skip the header line
            
        data = csv.reader(lines)
        servers = []

        seen_countries= set()
        for row in data:
            if len(row) >= 15:
                tcpPort = getTcpPort(row[14]) # 14 is config base64 
                server = {
                    'hostname': row[0] + ".opengw.net:" + tcpPort,
                    'ip': row[1],
                    'ping': row[3],
                    'speed': row[4],
                    'countryLong': row[5],
                    'countryShort': row[6],
                    'uptime': row[8],
                    'totalUsers': row[9],
                    'totalTraffic': row[10],

                }
                
                if server['countryLong'] not in seen_countries:
                    seen_countries.add(server['countryLong'])
                    print(f"Found country: {server['countryLong']} -> Short: {server['countryShort']}")

                servers.append(server)
            
        SERVER_LIST = servers
        return servers
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

async def onConnect(websocket, data):
    hostname = data.get('hostname')
    result = VPN.connect(hostname, "MyVPN", "vpn", "vpn")
    
    if result:
        MONITOR.start(callback=VPN.disconnect)
    
    await WS.broadcast({
        'type': 'vpn_status',
        'connected': result,
        'server': hostname
    })    
    
async def onDisconnect(websocket, data):
    result = VPN.disconnect()
    MONITOR.stop()
    
    await WS.broadcast({
        'type': 'vpn_status',
        'connected': False
    })
    
async def onGetStatus(websocket, data):
    await WS.send(websocket, {
        'type': 'vpn_status',
        'connected': VPN.isConnecting(),
        'last_connection': VPN.getLastConnection()
    })
    
async def onRefreshServers(websocket, data):
    servers = fetchServers()
    formatted = [{
        'hostname': s['hostname'],
        'ip': s['ip'],
        'ping': s['ping'],
        'speed': s['speed'],
        'countryLong': s['countryLong'],
        'countryShort': s['countryShort'],
        'uptime': s['uptime'],
        'totalUsers': s['totalUsers'],
        'totalTraffic': s['totalTraffic']
    } for s in servers]
    
    await WS.send(websocket, {
        'type': 'server_list',
        'servers': formatted
    })
    
def startHTTP():
    httpd = HTTPServer(('localhost', 8080), SimpleHTTPRequestHandler)
    print("HTTP Server running on http://localhost:8080")
    httpd.serve_forever()

async def main():
    global WS
    
    print("Fetching servers...")
    fetchServers()
    print(f"Loaded {len(SERVER_LIST)} servers")
    
    WS = Ws(maxClients=2)
    
    # Register handlers
    WS.on("connect", onConnect)
    WS.on("disconnect", onDisconnect)
    WS.on("get_status", onGetStatus)
    WS.on("refresh_servers", onRefreshServers)
    
    
    # Start HTTP server
    threading.Thread(target=startHTTP, daemon=True).start()
    
    # Open browser
    webbrowser.open('http://localhost:8080')
    
    # Start WebSocket server
    print("=" * 50)
    print("WebSocket: ws://localhost:8766")
    print("Web UI: http://localhost:8080")
    print("=" * 50)
    
    await WS.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")