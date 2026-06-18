import requests
import urllib.parse
import json
import re
import time

SOURCES = [
    # Твои источники подписок
]

def check_location(ip, original_name):
    # Упрощенная проверка гео (оставил логику RU/EU)
    name_lower = urllib.parse.unquote(original_name).lower()
    if any(x in name_lower for x in ['ru', 'russia', 'россия', 'москва', 'msk']): return 'RU'
    if ip:
        try:
            time.sleep(1)
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=countryCode", timeout=5).json()
            if res.get('countryCode') == 'RU': return 'RU'
        except: pass
    return 'EU'

def parse_vless_link(link, tag_name):
    """Превращает строку vless:// в Xray outbound JSON"""
    try:
        parsed = urllib.parse.urlparse(link)
        user_id = parsed.username
        address = parsed.hostname
        port = parsed.port
        params = urllib.parse.parse_qs(parsed.query)
        
        # Базовый скелет outbound
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

        # Если это Reality
        if outbound["streamSettings"]["security"] == "reality":
            outbound["streamSettings"]["realitySettings"] = {
                "serverName": params.get('sni', [''])[0],
                "publicKey": params.get('pbk', [''])[0],
                "shortId": params.get('sid', [''])[0],
                "fingerprint": params.get('fp', ['chrome'])[0],
                "show": False
            }
        
        # Если network = grpc или ws, нужно добавить настройки (для простоты тут база)
        return outbound
    except Exception as e:
        return None

def generate_profile(name, servers_chunk):
    """Генерирует один профиль с балансировщиком для чанка серверов"""
    outbounds = []
    tags = []
    
    for i, link in enumerate(servers_chunk):
        tag = f"proxy_{i}"
        parsed_outbound = parse_vless_link(link, tag)
        if parsed_outbound:
            outbounds.append(parsed_outbound)
            tags.append(tag)
            
    # Добавляем обязательные системные outbounds
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
    # 1. Собираем все ссылки (код парсинга base64 опускаю для краткости)
    raw_links = [] # Сюда попадут все vless:// после декодирования источников
    
    ru_links = []
    eu_links = []
    
    # 2. Сортируем по Гео
    for link in raw_links:
        if not link.startswith('vless://'): continue
        host_match = re.search(r'@([^:]+):', link)
        name_match = re.search(r'#(.*)$', link)
        ip = host_match.group(1) if host_match else None
        name = name_match.group(1) if name_match else ""
        
        if check_location(ip, name) == 'RU': ru_links.append(link)
        else: eu_links.append(link)

    final_json_array = []
    
    # 3. Дробим на балансировщики по 30 серверов
    chunk_size = 30
    
    # Обрабатываем RU сервера
    for i in range(0, len(ru_links), chunk_size):
        chunk = ru_links[i:i + chunk_size]
        profile_num = (i // chunk_size) + 1
        profile = generate_profile(f"🇲🇦 🗽 LTE RU {profile_num} | t.me/telegaproxys", chunk)
        final_json_array.append(profile)

    # Обрабатываем EU сервера
    for i in range(0, len(eu_links), chunk_size):
        chunk = eu_links[i:i + chunk_size]
        profile_num = (i // chunk_size) + 1
        profile = generate_profile(f"🇲🇦 🗽 LTE EU {profile_num} | t.me/telegaproxys", chunk)
        final_json_array.append(profile)

    # 4. Сохраняем в JSON файл для GitHub Pages
    with open('sub.json', 'w', encoding='utf-8') as f:
        json.dump(final_json_array, f, indent=2, ensure_ascii=False)
        
    print("Конфиги с балансировщиками успешно собраны!")

if __name__ == "__main__":
    main()
