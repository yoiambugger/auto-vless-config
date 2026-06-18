import requests
import urllib.parse
import json
import re
import base64
import time
import uuid

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
            time.sleep(1)
            res = requests.get(f"http://ip-api.com/json/{ip}?fields=countryCode", timeout=5).json()
            if res.get('countryCode') == 'RU': 
                return 'RU'
        except: 
            pass
    return 'EU'

def is_valid_uuid(val):
    """Проверка на то, что ID это настоящий UUID, иначе Xray крашится"""
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def parse_vless_link(link, tag_name):
    """Жесткая фильтрация и парсинг ссылки"""
    try:
        parsed = urllib.parse.urlparse(link)
        user_id = parsed.username
        address = parsed.hostname
        port = int(parsed.port) if parsed.port else 443 
        
        # 1. Защита от пустых IP и битых портов
        if not address or not (1 <= port <= 65535): 
            return None
            
        # 2. Защита от кривых UUID (главная причина краша ядра)
        if not is_valid_uuid(user_id):
            return None

        params = urllib.parse.parse_qs(parsed.query)
        flow = params.get('flow', [''])[0]
        network = params.get('type', ['tcp'])[0]
        security = params.get('security', ['none'])[0]

        user_obj = {"id": user_id, "encryption": "none", "flow": flow if flow else ""}
        
        # Ограничиваем известными протоколами
        if network not in ['tcp', 'ws', 'grpc', 'xhttp', 'http', 'kcp', 'quic']:
            network = 'tcp'
            
        stream_settings = {
            "network": network,
            "security": security if security in ['none', 'tls', 'reality'] else 'none'
        }

        if stream_settings["security"] == "reality":
            stream_settings["realitySettings"] = {
                "serverName": params.get('sni', [''])[0],
                "publicKey": params.get('pbk', [''])[0],
                "shortId": params.get('sid', [''])[0],
                "fingerprint": params.get('fp', ['chrome'])[0],
                "show": False
            }
        elif stream_settings["security"] == "tls":
            stream_settings["tlsSettings"] = {
                "serverName": params.get('sni', [address])[0],
                "show": False
            }
            fp = params.get('fp', [''])[0]
            if fp: 
                stream_settings["tlsSettings"]["fingerprint"] = fp

        # Специфичные настройки транспорта
        if network == "tcp":
            stream_settings["tcpSettings"] = {}
        elif network == "ws":
            stream_settings["wsSettings"] = {"path": params.get('path', ['/'])[0]}
            host = params.get('host', [''])[0]
            if host: 
                stream_settings["wsSettings"]["headers"] = {"Host": host}
        elif network == "grpc":
            svc = params.get('serviceName', [''])[0]
            if not svc: 
                svc = params.get('path', [''])[0] # Иногда лежит в path
            stream_settings["grpcSettings"] = {"serviceName": svc, "multiMode": True}

        return {
            "tag": tag_name,
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": address,
                    "port": port,
                    "users": [user_obj]
                }]
            },
            "streamSettings": stream_settings
        }
    except Exception:
        return None

def generate_profile(name, servers_chunk):
    outbounds = []
    valid_count = 0
    
    # Собираем только 100% рабочие по структуре аутбаунды
    for link in servers_chunk:
        tag = f"proxy_{valid_count}"
        parsed_outbound = parse_vless_link(link, tag)
        if parsed_outbound:
            outbounds.append(parsed_outbound)
            valid_count += 1
            
    # Защита от "пустых" профилей, которые крашат балансировщик
    if valid_count == 0:
        return None
        
    outbounds.append({"tag": "direct", "protocol": "freedom"})
    outbounds.append({"tag": "block", "protocol": "blackhole"})

    profile = {
        "remarks": name,
        "observatory": {
            "subjectSelector": ["proxy_"],
            "probeUrl": "https://www.google.com/generate_204",
            "probeInterval": "10s"
        },
        "dns": {
            "servers": ["https://8.8.8.8/dns-query", "https://8.8.8.8/dns-query"],
            "queryStrategy": "UseIP"
        },
        "routing": {
            "domainMatcher": "hybrid",
            "domainStrategy": "IPIfNonMatch",
            "balancers": [{
                "tag": "best_ping_balancer",
                "selector": ["proxy_"],
                "strategy": {"type": "leastPing"}
            }],
            "rules": [
                {"type": "field", "protocol": ["bittorrent"], "outboundTag": "direct"},
                {
                    "type": "field",
                    "domain": [
                        "max.ru", "domain:2gis.ru", "domain:ads.x5.ru", "domain:2gis.com",
                        "domain:aif.ru", "domain:aeroflot.ru", "domain:alfabank.ru", "domain:avito.ru",
                        "domain:beeline.ru", "domain:burgerkingrus.ru", "domain:dellin.ru", "domain:drive2.ru",
                        "domain:dzen.ru", "domain:flypobeda.ru", "domain:forbes.ru", "domain:gazeta.ru",
                        "domain:gazprombank.ru", "domain:gismeteo.ru", "domain:gosuslugi.ru", "domain:hh.ru",
                        "domain:kontur.ru", "domain:kontur.host", "domain:kp.ru", "domain:kuper.ru",
                        "domain:lenta.ru", "domain:mail.ru", "domain:max.ru", "domain:megamarket.ru",
                        "domain:megamarket.tech", "domain:megafon.ru", "domain:moex.com", "domain:motivtelecom.ru",
                        "domain:ozon.ru", "domain:pervye.ru", "domain:psbank.ru", "domain:rambler.ru",
                        "domain:rambler-co.ru", "domain:rbc.ru", "domain:reg.ru", "domain:reviews.2gis.com",
                        "domain:rg.ru", "domain:ria.ru", "domain:ruwiki.ru", "domain:rustore.ru",
                        "domain:rutube.ru", "domain:rzd.ru", "domain:sirena-travel.ru", "domain:sravni.ru",
                        "domain:t-j.ru", "domain:t2.ru", "domain:tank-online.com", "domain:taximaxim.ru",
                        "domain:tbank-online.com", "domain:tildaapi.com", "domain:tns-counter.ru",
                        "domain:trvl.yandex.net", "domain:tutu.ru", "domain:vk.com", "domain:vk.ru",
                        "domain:vkvideo.ru", "domain:vtb.ru", "domain:x5.ru", "domain:ya.ru", "domain:yandex.ru",
                        "domain:yandex.net", "domain:yandex.com", "domain:yastatic.net", "domain:yandexcloud.net",
                        "full:go.yandex", "full:ru.ruwiki.ru", "domain:xn--90acagbhgpca7c8c7f.xn--p1ai",
                        "domain:xn--80ajghhoc2aj1c8b.xn--p1ai", "domain:xn--90aivcdt6dxbc.xn--p1ai",
                        "domain:xn--b1aew.xn--p1ai", "domain:api.oneme.ru", "domain:fd.oneme.ru", "domain:i.oneme.ru",
                        "domain:miniapps.max.ru", "domain:sdk-api.apptracer.ru", "domain:st.max.ru",
                        "domain:tracker-api.vk-analytics.ru"
                    ],
                    "outboundTag": "direct"
                },
                {"type": "field", "domain": ["geosite:telegram", "domain:telegram.org", "domain:t.me"], "balancerTag": "best_ping_balancer"},
                {"type": "field", "network": "tcp,udp", "balancerTag": "best_ping_balancer"}
            ]
        },
        "inbounds": [
            {
                "tag": "socks",
                "port": 10808,
                "listen": "127.0.0.1",
                "protocol": "socks",
                "settings": {"udp": True, "auth": "noauth"},
                "sniffing": {"enabled": True, "routeOnly": True, "destOverride": ["http", "tls", "quic"]}
            },
            {
                "tag": "http",
                "port": 10809,
                "listen": "127.0.0.1",
                "protocol": "http",
                "settings": {"allowTransparent": False},
                "sniffing": {"enabled": True, "routeOnly": True, "destOverride": ["http", "tls", "quic"]}
            }
        ]
    }
    return profile

def main():
    raw_links = []
    
    print("Скачивание...")
    for url in SOURCES:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                try:
                    lines = decode_base64(r.text.strip()).splitlines()
                except:
                    lines = r.text.splitlines()
                raw_links.extend(lines)
        except: pass

    ru_links = []
    eu_links = []
    
    for link in raw_links:
        link = link.strip()
        if not link.startswith('vless://'): continue
        
        parsed = urllib.parse.urlparse(link)
        ip = parsed.hostname
        name_match = re.search(r'#(.*)$', link)
        name = name_match.group(1) if name_match else ""
        
        if check_location(ip, name) == 'RU': ru_links.append(link)
        else: eu_links.append(link)

    final_json_array = []
    chunk_size = 30
    
    for i in range(0, len(ru_links), chunk_size):
        profile = generate_profile(f"🇲🇦 🗽 LTE RU {(i // chunk_size) + 1} | t.me/telegaproxys", ru_links[i:i + chunk_size])
        if profile: final_json_array.append(profile)

    for i in range(0, len(eu_links), chunk_size):
        profile = generate_profile(f"🇲🇦 🗽 LTE EU {(i // chunk_size) + 1} | t.me/telegaproxys", eu_links[i:i + chunk_size])
        if profile: final_json_array.append(profile)

    with open('custom_sub.json', 'w', encoding='utf-8') as f:
        json.dump(final_json_array, f, indent=2, ensure_ascii=False)
        
    print(f"Готово! Создано профилей: {len(final_json_array)}")

if __name__ == "__main__":
    main()
