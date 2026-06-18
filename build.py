import requests
import urllib.parse
import json
import re
import base64
import time

# Источники конфигураций
SOURCES = [
    "https://raw.githubusercontent.com/luxxuria/harvester/refs/heads/main/top_600.txt",
    "https://raw.githubusercontent.com/zieng2/wl/refs/heads/main/vless_universal.txt"
]

def decode_base64(data):
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    return base64.b64decode(data).decode('utf-8', errors='ignore')

def check_location(ip, original_name):
    name_lower = urllib.parse.unquote(original_name).lower()
    if any(x in name_lower for x in ['ru', 'russia', 'россия', 'москва', 'msk']): 
        return 'RU'
    if ip:
        try:
            time.sleep(1) # Задержка, чтобы ip-api не забанил за частые запросы
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=countryCode", timeout=5).json()
            if res.get('countryCode') == 'RU': 
                return 'RU'
        except: 
            pass
    return 'EU'

def parse_vless_link(link, tag_name):
    """Превращает строку vless:// в Xray outbound JSON"""
    try:
        parsed = urllib.parse.urlparse(link)
        user_id = parsed.username
        address = parsed.hostname
        port = parsed.port
        params = urllib.parse.parse_qs(parsed.query)
        
        outbound = {
            "tag": tag_name,
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": address,
                    "port": int(port),
                    "users": [{"id": user_id, "encryption": "none", "flow": params.get('flow', [''])[0]}]
                }]
            },
            "streamSettings": {
                "network": params.get('type', ['tcp'])[0],
                "security": params.get('security', ['none'])[0]
            }
        }

        if outbound["streamSettings"]["security"] == "reality":
            outbound["streamSettings"]["realitySettings"] = {
                "serverName": params.get('sni', [''])[0],
                "publicKey": params.get('pbk', [''])[0],
                "shortId": params.get('sid', [''])[0],
                "fingerprint": params.get('fp', ['chrome'])[0],
                "show": False
            }
        return outbound
    except Exception as e:
        return None

def generate_profile(name, servers_chunk):
    """Генерирует профиль с балансировщиком для группы серверов"""
    outbounds = []
    tags = []
    
    for i, link in enumerate(servers_chunk):
        tag = f"proxy_{i}"
        parsed_outbound = parse_vless_link(link, tag)
        if parsed_outbound:
            outbounds.append(parsed_outbound)
            tags.append(tag)
            
    outbounds.append({"tag": "direct", "protocol": "freedom"})
    outbounds.append({"tag": "block", "protocol": "blackhole"})

    profile = {
        "remarks": name,
        "observatory": {
            "subjectSelector": ["proxy_"],
            "probeUrl": "https://www.google.com/generate_204",
            "probeInterval": "10s"
        },
        "routing": {
            "domainStrategy": "IPIfNonMatch",
            "balancers": [{
                "tag": "best_ping_balancer",
                "selector": ["proxy_"],
                "strategy": {"type": "leastPing"}
            }],
            "rules": [
                {"type": "field", "protocol": ["bittorrent"], "outboundTag": "direct"},
                {"type": "field", "domain": ["geosite:telegram", "domain:t.me"], "balancerTag": "best_ping_balancer"},
                {"type": "field", "network": "tcp,udp", "balancerTag": "best_ping_balancer"}
            ]
        },
        "outbounds": outbounds,
        "inbounds": [
            {"tag": "socks", "port": 10808, "protocol": "socks", "settings": {"udp": True, "auth": "noauth"}},
            {"tag": "http", "port": 10809, "protocol": "http", "settings": {"allowTransparent": False}}
        ]
    }
    return profile

def main():
    raw_links = []
    
    print("Начинаю скачивание источников...")
    for url in SOURCES:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                # Пробуем декодировать (если это Base64 подписка)
                try:
                    decoded_text = decode_base64(r.text.strip())
                    lines = decoded_text.splitlines()
                except:
                    # Если текст не в Base64, читаем как обычный список строк
                    lines = r.text.splitlines()
                    
                raw_links.extend(lines)
        except Exception as e:
            print(f"Ошибка парсинга {url}: {e}")

    ru_links = []
    eu_links = []
    
    print(f"Всего получено строк для проверки: {len(raw_links)}")
    print("Сортирую по гео-локации...")
    
    for link in raw_links:
        link = link.strip()
        if not link.startswith('vless://'): 
            continue
        
        host_match = re.search(r'@([^:]+):', link)
        name_match = re.search(r'#(.*)$', link)
        ip = host_match.group(1) if host_match else None
        name = name_match.group(1) if name_match else ""
        
        if check_location(ip, name) == 'RU': 
            ru_links.append(link)
        else: 
            eu_links.append(link)

    final_json_array = []
    chunk_size = 30
    
    # Сборка балансировщиков RU
    for i in range(0, len(ru_links), chunk_size):
        chunk = ru_links[i:i + chunk_size]
        profile_num = (i // chunk_size) + 1
        final_json_array.append(generate_profile(f"🇲🇦 🗽 LTE RU {profile_num} | t.me/telegaproxys", chunk))

    # Сборка балансировщиков EU
    for i in range(0, len(eu_links), chunk_size):
        chunk = eu_links[i:i + chunk_size]
        profile_num = (i // chunk_size) + 1
        final_json_array.append(generate_profile(f"🇲🇦 🗽 LTE EU {profile_num} | t.me/telegaproxys", chunk))

    # Сохраняем в custom_sub.json
    with open('custom_sub.json', 'w', encoding='utf-8') as f:
        json.dump(final_json_array, f, indent=2, ensure_ascii=False)
        
    print(f"Успех! Собрано RU серверов: {len(ru_links)}, EU серверов: {len(eu_links)}")

if __name__ == "__main__":
    main()
