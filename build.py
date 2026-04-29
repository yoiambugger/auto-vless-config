import requests
import urllib.parse
import json
import re

# Твои источники
SOURCES = [
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-all.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-9.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-8.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-7.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-6.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-5.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-4.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-3.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-2.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-12.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-11.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-10.txt",
    "https://raw.githubusercontent.com/whoahaow/rjsxrd/refs/heads/main/githubmirror/bypass-unsecure/bypass-unsecure-1.txt"
]

MAX_NODES = 150 # Совет: не делай больше 150-200, иначе пинг каждые 5 сек положит роутер/пк

def parse_vless_link(link, index):
    try:
        link = urllib.parse.unquote(link.strip())
        if not link.startswith("vless://"):
            return None
        
        # Парсим основную часть и параметры
        main_part = link[8:].split('#')[0]
        if '?' in main_part:
            credentials, query_string = main_part.split('?', 1)
        else:
            credentials, query_string = main_part, ""
            
        uuid, server_port = credentials.split('@', 1)
        address, port = server_port.split(':', 1)
        params = dict(urllib.parse.parse_qsl(query_string))

        # Формируем outbound блок
        outbound = {
            "tag": f"proxy_{index}",
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": address,
                    "port": int(port),
                    "users": [{
                        "id": uuid,
                        "encryption": params.get("encryption", "none"),
                        "flow": params.get("flow", "")
                    }]
                }]
            },
            "streamSettings": {
                "network": params.get("type", "tcp"),
                "security": params.get("security", "none")
            }
        }

        # Если это Reality, добавляем настройки
        if params.get("security") == "reality":
            outbound["streamSettings"]["realitySettings"] = {
                "serverName": params.get("sni", ""),
                "publicKey": params.get("pbk", ""),
                "shortId": params.get("sid", ""),
                "fingerprint": params.get("fp", "chrome"),
                "show": False
            }
            
        return outbound
    except Exception as e:
        return None

def main():
    raw_links = []
    # 1. Собираем все ссылки
    for url in SOURCES:
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                raw_links.extend(resp.text.splitlines())
        except Exception as e:
            print(f"Ошибка загрузки {url}: {e}")

    # 2. Убираем дубликаты (используя set)
    unique_links = list(set([link.strip() for link in raw_links if link.strip().startswith("vless://")]))
    
    outbounds = []
    # 3. Парсим ссылки в JSON-объекты
    for i, link in enumerate(unique_links):
        if len(outbounds) >= MAX_NODES:
            break # Ограничиваем количество, чтобы не перегрузить ядро
        parsed = parse_vless_link(link, i)
        if parsed:
            outbounds.append(parsed)

    # 4. Формируем финальный конфиг с Балансировщиком
    config = {
        "remarks": "🇲🇦 🗽 LTE | @telegaproxys",
        "observatory": {
            "subjectSelector": ["proxy_"], # Наблюдаем за всеми тегами, начинающимися на proxy_
            "probeUrl": "https://www.google.com/generate_204",
            "probeInterval": "5s" # Пинг каждые 5 секунд
        },
        "routing": {
            "domainStrategy": "IPIfNonMatch",
            "domainMatcher": "hybrid",
            "balancers": [
                {
                    "tag": "best_ping_balancer",
                    "selector": ["proxy_"],
                    "strategy": {"type": "leastPing"} # Выбираем самый низкий пинг
                }
            ],
            "rules": [
                {
                    "type": "field",
                    "protocol": ["bittorrent"],
                    "outboundTag": "direct"
                },
                {
                    "type": "field",
                    "network": "tcp,udp",
                    "balancerTag": "best_ping_balancer" # Пускаем трафик через балансировщик
                }
            ]
        },
        "outbounds": outbounds + [
            {"tag": "direct", "protocol": "freedom"},
            {"tag": "block", "protocol": "blackhole"}
        ],
        "inbounds": [
            {
                "tag": "socks", "port": 10808, "listen": "127.0.0.1", "protocol": "socks",
                "settings": {"udp": True, "auth": "noauth"},
                "sniffing": {"enabled": True, "routeOnly": True, "destOverride": ["http", "tls", "quic"]}
            },
            {
                "tag": "http", "port": 10809, "listen": "127.0.0.1", "protocol": "http",
                "settings": {"allowTransparent": False},
                "sniffing": {"enabled": True, "routeOnly": True, "destOverride": ["http", "tls", "quic"]}
            }
        ],
        "dns": {
            "servers": ["https://8.8.8.8/dns-query"],
            "queryStrategy": "UseIP"
        }
    }

    # 5. Сохраняем в файл
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        print("Конфиг успешно собран! Сохранено нодов:", len(outbounds))

if __name__ == "__main__":
    main()

