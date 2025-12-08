import requests
import socket
import sys

def test_connections():
    """Test connection to scraper from Docker container"""
    
    print("Testing connections FROM INSIDE DOCKER CONTAINER")
    print("=" * 60)
    
    # Common Docker hostnames to test
    test_hosts = [
        ("cheese_radar", "Container name"),
        ("localhost", "Localhost"),
        ("127.0.0.1", "Localhost IP"),
        ("host.docker.internal", "Docker internal"),
        ("host-gateway", "Docker gateway"),
        ("172.17.0.1", "Docker bridge"),
        ("172.18.0.1", "Docker network 1"),
        ("172.19.0.1", "Docker network 2"),
    ]
    
    # Find container IP if exists
    try:
        import subprocess
        result = subprocess.run(
            ["sh", "-c", "ip route | grep default | awk '{print $3}'"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            gateway = result.stdout.strip()
            test_hosts.append((gateway, "Default gateway"))
    except:
        pass
    
    working = []
    
    for host, desc in test_hosts:
        url = f"http://{host}:8081"
        print(f"\n🔍 Testing: {host} ({desc})")
        print(f"   URL: {url}")
        
        # Test DNS
        try:
            ip = socket.gethostbyname(host)
            print(f"   ✅ DNS resolves to: {ip}")
        except socket.gaierror:
            print(f"   ❌ DNS failed")
            continue
        
        # Test port
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, 8081))
            sock.close()
            if result == 0:
                print(f"   ✅ Port 8081 is OPEN")
            else:
                print(f"   ❌ Port 8081 CLOSED")
                continue
        except Exception as e:
            print(f"   ❌ Port test error: {e}")
            continue
        
        # Test HTTP
        try:
            response = requests.get(url, timeout=3)
            print(f"   ✅ HTTP status: {response.status_code}")
            
            # Try scrape endpoint
            try:
                scrape_resp = requests.post(f"{url}/scrape", timeout=5, json={})
                print(f"   ✅ Scrape endpoint: {scrape_resp.status_code}")
                working.append((host, desc, url))
            except:
                print(f"   ⚠️  Scrape endpoint not working (might need auth)")
                working.append((host, desc, url))
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection refused")
        except Exception as e:
            print(f"   ❌ HTTP error: {e}")
    
    print(f"\n{'='*60}")
    if working:
        print("✅ WORKING CONNECTIONS FOUND:")
        for host, desc, url in working:
            print(f"   • {desc}: '{host}'")
            print(f"     Use in code: requests.post('{url}/scrape', ...)")
    else:
        print("❌ NO WORKING CONNECTIONS")
        print("\nPossible solutions:")
        print("1. Check if scraper is running: docker ps | grep cheese")
        print("2. Connect to same network: docker network connect NETWORK_NAME airflow-scheduler")
        print("3. Use host networking for scraper")
    
    return working

if __name__ == "__main__":
    test_connections()
