import requests
import urllib.parse
import json
import time

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

CHUNK_SIZE = 250 # Количество серверов внутри одного балансировщика

def get_non_ru_links(unique_links):
    print(f"Начинаем проверку локаций для {len(unique_links)} серверов. Удаляем RU...")
    safe_links = []
    
    # Разбиваем на пачки по 100 для API
    for i in range(0, len(unique_links), 100):
        chunk = unique_links[i:i+100]
        batch_data = []
        
        for link in chunk:
            try:
                # Вытаскиваем IP или домен из ссылки
                address = link[8:].split('@')[1].split(':')[0]
                batch_data.append({"query": address})
            except:
                batch_data.append({"query": "127.0.0.1"}) # заглушка если не удалось распарсить
        
        try:
            # Отправляем пачку на проверку в ip-api
            resp = requests.post("http://ip-api.com/batch", json=batch_data, timeout=10).json()
            
            for j, res in enumerate(resp):
                address = batch_data[j]["query"]
                
                # Быстрый сброс по домену
                if address.endswith('.ru'):
                    continue
                    
                # Сброс по ответу от геолокации
                if res.get("status") == "success" and res.get("countryCode") == "RU":
                    continue
                
                # Если всё чисто, добавляем в белый список
                safe_links.append(chunk[j])
        except Exception as e:
            print(f"Ошибка API (пропускаем фильтрацию для пачки): {e}")
            safe_links.extend(chunk) # В случае ошибки API просто оставляем как есть
            
        time.sleep(1.5) # Пауза чтобы бесплатный API не забанил нас
        
    print(f"Осталось зарубежных серверов: {len(safe_links)}")
    return safe_links

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

    # ---> ФИЛЬТРАЦИЯ РОССИЙСКИХ СЕРВЕРОВ <---
    unique_links = get_non_ru_links(unique_links)

    # 3. Парсим в JSON объекты
    valid_outbounds = []
    for i, link in enumerate(unique_links):
        parsed = parse_vless_link(link, i)
        if parsed:
            valid_outbounds.append(parsed)

    # 4. Фасуем по чанкам
    configs_array = []
    total_chunks = (len(valid_outbounds) + CHUNK_SIZE - 1) // CHUNK_SIZE 

    for chunk_idx in range(total_chunks):
        start_idx = chunk_idx * CHUNK_SIZE
        end_idx = start_idx + CHUNK_SIZE
        chunk_outbounds = valid_outbounds[start_idx:end_idx]
        
        server_number = chunk_idx + 1
        
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
        
        configs_array.append(config_profile)

    # 5. Сохраняем
    with open("custom_sub.json", "w", encoding="utf-8") as f:
        json.dump(configs_array, f, indent=2, ensure_ascii=False)
        print(f"Готово! Создан custom_sub.json, внутри {len(configs_array)} серверов.")

if __name__ == "__main__":
    main()
