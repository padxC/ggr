import subprocess
import time


class VPN:
    @staticmethod
    def isConnecting():
        """Check if VPN is currently connected"""
        try:
            result = subprocess.run(['powershell.exe', 'rasdial'], 
                                  capture_output=True, text=True, timeout=5)
            return "Connected" in result.stdout
        except:
            return False
    
    @staticmethod
    def remove(vpnName):
        """Remove/Delete VPN connection completely from system"""
        try:
            # First disconnect if connected
            if VPN.isConnecting():
                print(f"Disconnecting {vpnName}...")
                VPN.disconnect()
            
            # Remove the VPN connection
            print(f"Removing VPN connection: {vpnName}")
            result = subprocess.run(
                ['powershell.exe', 'Remove-VpnConnection', '-Name', vpnName, '-Force'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(f"✓ Successfully removed {vpnName}")
                return True
            else:
                # Check if connection doesn't exist
                if "not found" in result.stderr.lower() or "does not exist" in result.stderr.lower():
                    print(f"Connection {vpnName} does not exist")
                    return True
                else:
                    print(f"✗ Failed to remove: {result.stderr}")
                    return False
                    
        except subprocess.TimeoutExpired:
            print("❌ Remove operation timeout")
            return False
        except Exception as e:
            print(f"❌ Error removing VPN: {e}")
            return False

    @staticmethod
    def disconnect():
        try:
            subprocess.run(['powershell.exe', 'rasdial', '/disconnect'], capture_output=True)
            time.sleep(1)
            return not VPN.isConnecting()
        except:
            return False
        
    @staticmethod
    def connect(address, vpnName="KoreaVPN", userName="vpn", password="vpn"):
        try:
            # Remove existing connections
            VPN.remove(vpnName);
            
            # create new VPN
            subprocess.run(
                ['powershell.exe', 'Add-VpnConnection', '-Name', vpnName, '-ServerAddress', address, '-Force'],
                capture_output=True,
                text=True
            )
            
            print("🔌 Establishing VPN connection...")
            connectResult = subprocess.run(
                ['powershell.exe', 'rasdial', vpnName, userName, password],
                capture_output=True,
                text=True
            )

            if connectResult.returncode == 0:
                return True;
            else:
                print("Connection Failed: {connectResult.stdout}")
                return False;

        except subprocess.TimeoutExpired:
            print("❌ Connection timeout")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False;