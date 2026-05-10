import json
import os
import subprocess
import time


class VPN:
    DATA_FILE = "data.json"
    
    # using thread
    @staticmethod
    def _load():
        """Load or create database"""
        if os.path.exists(VPN.DATA_FILE):
            with open(VPN.DATA_FILE, 'r') as f:
                return json.load(f)
        return {'vpn': None}
    
    @staticmethod
    def _save(data):
        """Save to database"""
        with open(VPN.DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
            
    @staticmethod
    def saveConnection(hostname, region):
        """Save last connection"""
        data = VPN._load()
        data['vpn'] = {
            'hostname': hostname,
            'last_connection': time.time(),
            'region': region
        }
        VPN._save(data)
    
    @staticmethod
    def getInfo():
        """Get last connection"""
        data = VPN._load()
        return data.get('vpn')
    

    @staticmethod
    def isReachable(address):
        """Check if VPN server port is reachable using Test-NetConnection"""
        try:
            host, port = address.split(':')
            
            result = subprocess.run(
                ['powershell.exe', '-Command', 'Test-NetConnection', host, '-Port', str(port), '-WarningAction', 'SilentlyContinue'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Check if connection succeeded
            return "TcpTestSucceeded : True" in result.stdout
                
        except Exception as e:
            print(f"✗ Error checking reachability: {e}")
            return False
            
    @staticmethod
    def getHostname(vpnName):
        """Get hostname of a specific VPN connection"""
        try:
            result = subprocess.run(
                ['powershell.exe', 'Get-VpnConnection', '-Name', vpnName, 
                 '|', 'Select-Object', '-ExpandProperty', 'ServerAddress'],
                capture_output=True,
                text=True,
                timeout=3
            )
            print(result)
            hostname = result.stdout.strip()
            return hostname if hostname else None
        except:
            return None
        
    @staticmethod
    def isConnecting():
        """Check if VPN is currently connected"""
        try:
            result = subprocess.run(['powershell.exe', 'rasdial'], 
                                  capture_output=True, text=True, timeout=3)
            return "Connected" in result.stdout
        except:
            return False
    
    @staticmethod
    def remove(vpnName):
        """Remove/Delete VPN connection completely from system"""
        try:
            # Remove the VPN connection
            print(f"Removing VPN connection: {vpnName}")
            result = subprocess.run(
                ['powershell.exe', 'Remove-VpnConnection', '-Name', vpnName, '-Force'],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                print(f"✓ Successfully removed {vpnName}")
                return True
            else:
                print(f"✗ Failed to remove: {result.stderr}")
                return False
                    
        except Exception as e:
            print(f"❌ Error removing VPN: {e}")
            return False

    @staticmethod
    def disconnect():
        try:
            subprocess.run(['powershell.exe', 'rasdial', '/disconnect'], capture_output=True)
            time.sleep(1)
            return True
        except:
            return False
        
    @staticmethod
    def connect(serverAddress, vpnName, userName, password, region):
        try:
            # if connecting diconnect first
            if VPN.isConnecting():
                print(f"Disconnecting {vpnName}...")
                VPN.disconnect()


            isExist = subprocess.run(
                ['powershell.exe', 'Get-VpnConnection', '-Name', vpnName],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if isExist.returncode != 0:
                result = subprocess.run(
                    ['powershell.exe', 'Add-VpnConnection', '-Name', vpnName, '-ServerAddress', serverAddress, '-Force'],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print(f"✓ Create new: {serverAddress}")
                else:
                    print(f"Error creating VPN: {e}")
                    return
            else:
                subprocess.run(
                    ['powershell.exe', 'Set-VpnConnection', '-Name', vpnName, 
                     '-ServerAddress', serverAddress, '-Force'],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
            
            
            print("🔌 Establishing VPN connection...")
            isConnected = subprocess.run(
                ['powershell.exe', 'rasdial', vpnName, userName, password],
                capture_output=True,
                text=True
            )

            if isConnected.returncode == 0:
                VPN.saveConnection(serverAddress, region)
                print(f"✓ Saved: {serverAddress} ({region})")
                return True;
            else:
                print("Connection Failed: {connectResult.stdout}")
                return False;

        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False;
    