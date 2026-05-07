#!/usr/bin/env python3
"""Working fast.com speed test with all features"""

import argparse
import asyncio
import json
import sys
import time
from typing import List, Optional, Dict, Any

import aiohttp

# Hardcoded token (works perfectly)
TOKEN = "YXNkZmFzZGxmbnNkYWZoYXNkZmhrYWxm"
DEFAULT_TIMEOUT = 10
DEFAULT_URL_COUNT = 5
DEFAULT_BUFFER_SIZE = 8
MAX_CHECK_INTERVAL = 0.2

class SpeedUnits:
    @staticmethod
    def Mbps(raw_bps: float) -> float:
        return (raw_bps * 8) / 1_000_000
    
    @staticmethod
    def Kbps(raw_bps: float) -> float:
        return (raw_bps * 8) / 1000
    
    @staticmethod
    def MBps(raw_bps: float) -> float:
        return raw_bps / 1_000_000

class FastSpeedTest:
    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        url_count: int = DEFAULT_URL_COUNT,
        unit: str = "Mbps",
        verbose: bool = False,
    ):
        self.timeout = timeout
        self.url_count = url_count
        self.unit = unit
        self.verbose = verbose
        self.unit_func = getattr(SpeedUnits, unit)
        
    async def get_targets(self) -> List[str]:
        """Get test URLs from Netflix API"""
        api_url = f"https://api.fast.com/netflix/speedtest/v2?https=true&token={TOKEN}&urlCount={self.url_count}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers={'User-Agent': 'Mozilla/5.0'}) as resp:
                if resp.status != 200:
                    raise Exception(f"API returned {resp.status}")
                data = await resp.json()
                targets = data.get('targets', [])
                return [t['url'].replace('/speedtest', '/speedtest/range/0-') for t in targets]
    
    async def run(self) -> Dict[str, Any]:
        """Run the speed test"""
        if self.verbose:
            print("📡 Fetching test URLs...")
        
        urls = await self.get_targets()
        if not urls:
            raise Exception("No test URLs received")
        
        if self.verbose:
            print(f"✅ Got {len(urls)} test URLs")
            print(f"🚀 Testing for {self.timeout} seconds...")
        
        # Shared counter
        total_bytes = 0
        bytes_lock = asyncio.Lock()
        
        async def download(url: str):
            nonlocal total_bytes
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        async for chunk in resp.content.iter_chunked(65536):
                            async with bytes_lock:
                                total_bytes += len(chunk)
            except Exception as e:
                if self.verbose:
                    print(f"\n⚠️ Download error: {e}")
        
        # Start all downloads
        tasks = [asyncio.create_task(download(url)) for url in urls]
        
        # Progress monitoring
        start_time = time.time()
        last_bytes = 0
        speeds = []
        
        while time.time() - start_time < self.timeout:
            await asyncio.sleep(0.5)
            
            elapsed = time.time() - start_time
            current_bytes = total_bytes
            
            # Calculate current speed (bytes per second)
            bytes_delta = current_bytes - last_bytes
            current_bps = bytes_delta / 0.5  # bytes per second
            current_speed = self.unit_func(current_bps)
            
            # Store for averaging
            speeds.append(current_speed)
            if len(speeds) > 10:
                speeds.pop(0)
            
            avg_speed = sum(speeds) / len(speeds)
            mb_downloaded = current_bytes / 1024 / 1024
            
            if self.verbose:
                print(f"\r⏱️  {elapsed:.1f}s | 📥 {mb_downloaded:.1f} MB | "
                      f"⚡ {current_speed:.1f} {self.unit} (avg: {avg_speed:.1f})", 
                      end='', flush=True)
            
            last_bytes = current_bytes
        
        # Stop all downloads
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate final speed
        duration = time.time() - start_time
        avg_bps = total_bytes / duration  # bytes per second
        final_speed = self.unit_func(avg_bps)
        
        if self.verbose:
            print()  # New line
        
        return {
            'speed': round(final_speed, 2),
            'unit': self.unit,
            'total_mb': round(total_bytes / 1024 / 1024, 2),
            'duration': round(duration, 2),
            'urls_used': len(urls)
        }

async def main():
    parser = argparse.ArgumentParser(description='Fast.com speed test')
    parser.add_argument('-t', '--timeout', type=float, default=10, help='Test duration (seconds)')
    parser.add_argument('-c', '--url-count', type=int, default=5, help='Number of parallel connections')
    parser.add_argument('-u', '--unit', default='Mbps', choices=['Mbps', 'Kbps', 'MBps'], help='Output unit')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show progress')
    parser.add_argument('--json', action='store_true', help='JSON output')
    
    args = parser.parse_args()
    
    try:
        test = FastSpeedTest(
            timeout=args.timeout,
            url_count=args.url_count,
            unit=args.unit,
            verbose=args.verbose
        )
        
        result = await test.run()
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n✅ Download Speed: {result['speed']} {result['unit']}")
            print(f"📥 Total Downloaded: {result['total_mb']} MB")
            print(f"⏱️  Duration: {result['duration']} seconds")
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
