import requests
import urllib.parse
import json

# Тот самый источник для Резерва (Топ-50 нерусских, приоритет Германия)
RESERVE_SOURCE = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt"

# Остальные актуальные источники
SOURCES = [
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-SNI-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt"
]

CHUNK_SIZE = 50 # <--- ОПТИМИЗАЦИЯ ДЛЯ МОБИЛОК (по 50 штук на профиль)

# Список сайтов, которые будут работать НАПРЯМУЮ, минуя VPN
DIRECT_DOMAINS = [
    "max.ru", "domain:2gis.ru", "domain:ads.x5.ru", "domain:2gis.com", 
    "domain:aif.ru", "domain:aeroflot.ru", "domain:alfabank.ru", "domain:avito.ru", 
    "domain:beeline.ru", "domain:burgerkingrus.ru", "domain:dellin.ru", "domain:drive2.ru", 
    "domain:dzen.ru", "domain:flypobeda.ru", "domain:forbes.ru", "domain:gazeta.ru", 
    "domain:gazprombank.ru", "domain:gismeteo.ru", "domain:gosuslugi.ru", "domain:hh.ru", 
    "domain:kontur.ru", "domain:kontur.host", "domain:kp.ru", "domain:kuper.ru", 
    "domain:lenta.ru", "domain:mail.ru", "domain:megamarket.ru", "domain:megamarket.tech", 
    "domain:megafon.ru", "domain:moex.com", "domain:motivtelecom.ru", "domain:ozon.ru", 
    "domain:pervye.ru", "domain:psbank.ru", "domain:rambler.ru", "domain:rambler-co.ru", 
    "domain:rbc.ru", "domain:reg.ru", "domain:reviews.2gis.com", "domain:rg.ru", 
    "domain:ria.ru", "domain:ruwiki.ru", "domain:rustore.ru", "domain:rutube.ru", 
    "domain:rzd.ru", "domain:sirena-travel.ru", "domain:sravni.ru", "domain:t-j.ru", 
    "domain:t2.ru", "domain:tank-online.com", "domain:taximaxim.ru", "domain:tbank-online.com", 
    "domain:tildaapi.com", "domain:tns-counter.ru", "domain:trvl.yandex.net", "domain:tutu.ru", 
    "domain:vk.com", "domain:vk.ru", "domain:vkvideo.ru", "domain:vtb.ru", "domain:x5.ru", 
    "domain:ya.ru", "domain:yandex.ru", "domain:yandex.net", "domain:yandex.com", 
    "domain:yastatic.net", "domain:yandexcloud.net", "full:go.yandex", "full:ru.ruwiki.ru", 
    "domain:xn--90acagbhgpca7c8c7f.xn--p1ai", "domain:xn--80ajghhoc2aj1c8b.xn--p1ai", 
    "domain:xn--90aivcdt6dxbc.xn--p1ai", "domain:xn--b1aew.xn--p1ai", "domain:api.oneme.ru", 
    "domain:fd.oneme.ru", "domain:i.oneme.ru", "domain:miniapps.max.ru", 
    "domain:sdk-api.apptracer.ru", "domain:st.max.ru", "domain:tracker-api.vk-analytics.ru"
]

def parse_vless_link(link, index_tag):
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

        network = params.get("type", "tcp")
        security = params.get("security", "none")

        # --- АНТИ-КРАШ ФИЛЬТР ---
        if network not in ["tcp", "ws", "grpc", "kcp", "http", "httpupgrade", "xhttp"]:
            return None

        if security == "false":
            security = "none"
        elif security not in ["none", "tls", "reality"]:
            return None
        # ------------------------

        outbound = {
            "tag": index_tag, 
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
                "network": network,
                "security": security
            }
        }

        if security == "reality":
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
    global_unique_cores = set()
    configs_array = []

    # ==========================================
    # 1. ОБРАБОТКА РЕЗЕРВНОГО ИСТОЧНИКА (ТОП 50)
    # ==========================================
    reserve_raw = []
    try:
        resp = requests.get(RESERVE_SOURCE)
        if resp.status_code == 200:
            reserve_raw = resp.text.splitlines()
    except Exception as e:
        print(f"Ошибка загрузки резервного источника: {e}")

    reserve_parsed = []
    for link in reserve_raw:
        link = link.strip()
        if link.startswith("vless://"):
            core_link = link.split('#')[0]
            if core_link not in global_unique_cores:
                global_unique_cores.add(core_link)
                # Пока ставим пустой тег, перезапишем позже
                parsed = parse_vless_link(link, "")
                if parsed:
                    out_str = json.dumps(parsed).lower()
                    # Только нерусские
                    if ".ru" not in out_str and ".su" not in out_str and ".рф" not in out_str:
                        reserve_parsed.append(parsed)

    # Сортируем: Германия в приоритете
    def is_germany(out):
        out_str = json.dumps(out).lower()
        if ".de" in out_str or "-de" in out_str or "germany" in out_str or "fra" in out_str or "frankfurt" in out_str:
            return 1
        return 0

    reserve_parsed.sort(key=is_germany, reverse=True)

    # Забираем ровно 50
    top_reserve = reserve_parsed[:50]
    # Все остальные улетят в общую массу серверов
    leftover_reserve = reserve_parsed[50:]

    # Переписываем теги для Резерва
    for i, out in enumerate(top_reserve):
        out["tag"] = f"proxy_res_{i}"

    if top_reserve:
        reserve_profile = {
            "remarks": "🇲🇦 🗽 LTE | Резерв",
            "observatory": {
                "subjectSelector": ["proxy_res_"], 
                "probeUrl": "https://www.google.com/generate_204",
                "probeInterval": "10s"
            },
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "balancers": [
                    {
                        "tag": "best_ping_balancer",
                        "selector": ["proxy_res_"],
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
                        "domain": DIRECT_DOMAINS,
                        "outboundTag": "direct"
                    },
                    {
                        "type": "field",
                        "network": "tcp,udp",
                        "balancerTag": "best_ping_balancer" 
                    }
                ]
            },
            "outbounds": top_reserve + [
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
        configs_array.append(reserve_profile)


    # ==========================================
    # 2. ОБРАБОТКА ОСТАЛЬНЫХ СЕРВЕРОВ (ПО 50 ШТ)
    # ==========================================
    raw_links = []
    for url in SOURCES:
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                raw_links.extend(resp.text.splitlines())
        except Exception as e:
            print(f"Ошибка загрузки {url}: {e}")

    main_parsed = []
    main_parsed.extend(leftover_reserve)

    for link in raw_links:
        link = link.strip()
        if link.startswith("vless://"):
            core_link = link.split('#')[0] 
            if core_link not in global_unique_cores:
                global_unique_cores.add(core_link)
                parsed = parse_vless_link(link, "")
                if parsed:
                    main_parsed.append(parsed)

    # Переписываем теги для общей массы
    for i, out in enumerate(main_parsed):
        out["tag"] = f"proxy_{i}"

    total_chunks = (len(main_parsed) + CHUNK_SIZE - 1) // CHUNK_SIZE 

    for chunk_idx in range(total_chunks):
        start_idx = chunk_idx * CHUNK_SIZE
        end_idx = start_idx + CHUNK_SIZE
        chunk_outbounds = main_parsed[start_idx:end_idx]
        
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
                        "domain": DIRECT_DOMAINS,
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

    # ==========================================
    # 3. СОХРАНЕНИЕ
    # ==========================================
    with open("custom_sub.json", "w", encoding="utf-8") as f:
        json.dump(configs_array, f, indent=2, ensure_ascii=False)
        print(f"Готово! Создан custom_sub.json, внутри {len(configs_array)} серверов.")

if __name__ == "__main__":
    main()
