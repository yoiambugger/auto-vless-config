import requests
import urllib.parse
import json

# Твои источники
SOURCES = [
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/clean/vless.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/ru-sni-local/vless.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/ru-sni/vless.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_001.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_002.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_003.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_004.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_005.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_006.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_007.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_008.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_009.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_010.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_011.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_012.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_013.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_014.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_015.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_016.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_017.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_018.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_019.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_020.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_021.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_022.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_023.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_024.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_025.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_026.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_027.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_028.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_029.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_030.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_031.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_032.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_033.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_034.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_035.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_036.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_037.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_038.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_039.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_040.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_041.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_042.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_043.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_044.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_045.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_046.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_047.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_048.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_049.txt",
    "https://raw.githubusercontent.com/kort0881/vpn-vless-configs-russia/refs/heads/main/githubmirror/new/by_protocol/vless/vless_050.txt"
]

CHUNK_SIZE = 250 # Количество серверов внутри одного балансировщика

def parse_vless_link(link, index):
    try:
        link = urllib.parse.unquote(link.strip())
        if not link.startswith("vless://"):
            return None
        
        main_part = link[8:].split('#')[0]
        if '?' in main_part:
            credentials, query_string = main_part.split('?', 1)
        else:
            credentials, query_string = main_part, ""
            
        uuid, server_port = credentials.split('@', 1)
        address, port = server_port.split(':', 1)
        params = dict(urllib.parse.parse_qsl(query_string))

        outbound = {
            "tag": f"proxy_{index}", # Уникальный тег для каждого прокси
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

        if params.get("security") == "reality":
            outbound["streamSettings"]["realitySettings"] = {
                "serverName": params.get("sni", ""),
                "publicKey": params.get("pbk", ""),
                "shortId": params.get("sid", ""),
                "fingerprint": params.get("fp", "chrome"),
                "show": False
            }
            
        return outbound
    except Exception:
        return None

def main():
    raw_links = []
    # 1. Скачиваем все
    for url in SOURCES:
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                raw_links.extend(resp.text.splitlines())
        except Exception as e:
            print(f"Ошибка загрузки {url}: {e}")

    # 2. Удаляем дубликаты
    unique_links_dict = {}
    for link in raw_links:
        link = link.strip()
        if link.startswith("vless://"):
            core_link = link.split('#')[0] 
            if core_link not in unique_links_dict:
                unique_links_dict[core_link] = link
                
    unique_links = list(unique_links_dict.values())
    print(f"Найдено уникальных ссылок: {len(unique_links)}")

    # 3. Парсим в JSON объекты
    valid_outbounds = []
    for i, link in enumerate(unique_links):
        parsed = parse_vless_link(link, i)
        if parsed:
            valid_outbounds.append(parsed)

    # 4. Фасуем по чанкам (например, по 250 штук) и собираем массив конфигов
    configs_array = []
    total_chunks = (len(valid_outbounds) + CHUNK_SIZE - 1) // CHUNK_SIZE 

    for chunk_idx in range(total_chunks):
        start_idx = chunk_idx * CHUNK_SIZE
        end_idx = start_idx + CHUNK_SIZE
        chunk_outbounds = valid_outbounds[start_idx:end_idx]
        
        server_number = chunk_idx + 1
        
        # Собираем отдельный профиль-балансировщик
        config_profile = {
            "remarks": f"🇲🇦 🗽 LTE {server_number} | @telegaproxys",
            "observatory": {
                "subjectSelector": ["proxy_"], 
                "probeUrl": "https://www.google.com/generate_204",
                "probeInterval": "10s"
            },
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "balancers": [
                    {
                        "tag": "best_ping_balancer",
                        "selector": ["proxy_"],
                        "strategy": {"type": "leastPing"} 
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
                        "balancerTag": "best_ping_balancer" 
                    }
                ]
            },
            "outbounds": chunk_outbounds + [
                {"tag": "direct", "protocol": "freedom"},
                {"tag": "block", "protocol": "blackhole"}
            ],
            "inbounds": [
                {
                    "tag": "socks", "port": 10808, "protocol": "socks",
                    "settings": {"udp": True, "auth": "noauth"},
                    "sniffing": {"enabled": True, "destOverride": ["http", "tls"]}
                },
                {
                    "tag": "http", "port": 10809, "protocol": "http",
                    "settings": {"allowTransparent": False}
                }
            ],
            "dns": {
                "servers": ["1.1.1.1", "1.0.0.1"],
                "queryStrategy": "IPIfNonMatch"
            }
        }
        
        # Добавляем профиль в общий массив
        configs_array.append(config_profile)

    # 5. Сохраняем весь массив в ОДИН файл
    with open("custom_sub.json", "w", encoding="utf-8") as f:
        # indent=2 делает файл красивым и читаемым, как в твоем примере
        json.dump(configs_array, f, indent=2, ensure_ascii=False)
        print(f"Готово! Создан custom_sub.json, внутри {len(configs_array)} серверов.")

if __name__ == "__main__":
    main()
