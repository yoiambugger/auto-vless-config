import requests
import urllib.parse
import json
import ipaddress
import socket

# Тот самый источник для Резерва
RESERVE_SOURCE = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile.txt"

# Список источников
SOURCES = [
    "https://raw.githubusercontent.com/VAL41K/bypass-rkn-blocks/refs/heads/main/configs/obhod_WL",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-CIDR-RU-checked.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/WHITE-SNI-RU-all.txt",
    "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/refs/heads/main/Vless-Reality-White-Lists-Rus-Mobile-2.txt"
]

CHUNK_SIZE = 50 # Вернули 50 штук на профиль

# Ссылка на актуальный список всех российских IP-подсетей
RU_CIDR_URL = "https://raw.githubusercontent.com/herrbischoff/country-ip-blocks/master/ipv4/ru.cidr"

# Список сайтов для прямого подключения (мимо VPN)
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

def get_ru_networks():
    """Скачивает и парсит базу всех российских IP-адресов"""
    networks = []
    try:
        print("Скачиваем базу RU IP подсетей...")
        resp = requests.get(RU_CIDR_URL, timeout=15)
        if resp.status_code == 200:
            for line in resp.text.splitlines():
                if line.strip() and not line.startswith('#'):
                    networks.append(ipaddress.ip_network(line.strip()))
        print(f"Успешно загружено {len(networks)} российских подсетей.")
    except Exception as e:
        print(f"Ошибка загрузки базы IP: {e}")
    return networks

def is_masquerading(parsed, ru_networks):
    """Проверяет: SNI должен быть русским, а IP сервера - заграничным"""
    try:
        address = parsed["settings"]["vnext"][0]["address"]
        sni = parsed.get("streamSettings", {}).get("realitySettings", {}).get("serverName", "").lower()
        
        # 1. Проверяем, маскируется ли он под РФ (SNI)
        is_ru_sni = sni.endswith(".ru") or sni.endswith(".su") or sni.endswith(".рф") or "yandex" in sni or "vk.com" in sni or "mail.ru" in sni
        if not is_ru_sni:
            return False # Не маскируется под РФ - отбрасываем
            
        # 2. Проверяем, находится ли IP-адрес за границей
        try:
            ip_obj = ipaddress.ip_address(address)
        except ValueError:
            # Если вместо IP указан домен, пробуем узнать его IP
            try:
                resolved_ip = socket.gethostbyname(address)
                ip_obj = ipaddress.ip_address(resolved_ip)
            except Exception:
                return True # Если не удалось пробить, на всякий случай оставляем
                
        # Ищем IP в списке российских
        for net in ru_networks:
            if ip_obj in net:
                return False # Сервер физически в РФ! Отбрасываем.
                
        return True # Маскируется под РФ, а IP заграничный. Идеально!
    except Exception:
        return False

def is_germany(link_str):
    """Ищет упоминания Германии в сырой ссылке для резерва"""
    s = link_str.lower()
    if "-de" in s or "germany" in s or "fra" in s or "frankfurt" in s or "🇩🇪" in s:
        return 1
    return 0

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
    global_unique_cores = set()
    configs_array = []
    main_parsed = [] 
    
    # Загружаем базу РФ-айпишников для фильтра
    ru_networks = get_ru_networks()

    # ==========================================
    # 1. ОБРАБОТКА РЕЗЕРВА
    # ==========================================
    reserve_raw = []
    try:
        resp = requests.get(RESERVE_SOURCE)
        if resp.status_code == 200:
            reserve_raw = resp.text.splitlines()
    except Exception as e:
        print(f"Ошибка загрузки резерва: {e}")

    reserve_valid = []
    for link in reserve_raw:
        link = link.strip()
        if link.startswith("vless://"):
            core_link = link.split('#')[0]
            if core_link not in global_unique_cores:
                global_unique_cores.add(core_link)
                parsed = parse_vless_link(link, "")
                # Применяем наш мощный фильтр!
                if parsed and is_masquerading(parsed, ru_networks):
                    reserve_valid.append((parsed, link))

    # Сортируем: Германия в приоритете
    reserve_valid.sort(key=lambda x: is_germany(x[1]), reverse=True)
    reserve_parsed = [x[0] for x in reserve_valid]

    # Забираем ровно 50
    top_reserve = reserve_parsed[:CHUNK_SIZE]
    main_parsed.extend(reserve_parsed[CHUNK_SIZE:]) # Остальное спасаем в общую кучу

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
                "balancers": [{"tag": "best_ping_balancer", "selector": ["proxy_res_"], "strategy": {"type": "leastPing"}}],
                "rules": [
                    {"type": "field", "protocol": ["bittorrent"], "outboundTag": "direct"},
                    {"type": "field", "domain": DIRECT_DOMAINS, "outboundTag": "direct"},
                    {"type": "field", "domain": ["geosite:telegram", "domain:telegram.org", "domain:t.me"], "balancerTag": "best_ping_balancer"},
                    {"type": "field", "ip": ["geoip:telegram", "91.108.4.0/22", "91.108.8.0/22", "91.108.12.0/22", "91.108.16.0/22", "91.108.56.0/22", "149.154.160.0/20", "185.76.151.0/24"], "balancerTag": "best_ping_balancer"},
                    {"type": "field", "network": "tcp,udp", "balancerTag": "best_ping_balancer"}
                ]
            },
            "outbounds": top_reserve + [{"tag": "direct", "protocol": "freedom"}, {"tag": "block", "protocol": "blackhole"}],
            "inbounds": [{"tag": "socks", "port": 10808, "protocol": "socks", "settings": {"udp": True, "auth": "noauth"}, "sniffing": {"enabled": True, "destOverride": ["http", "tls"]}}, {"tag": "http", "port": 10809, "protocol": "http", "settings": {"allowTransparent": False}}],
            "dns": {"servers": ["1.1.1.1", "1.0.0.1"], "queryStrategy": "IPIfNonMatch"}
        }
        configs_array.append(reserve_profile)

    # ==========================================
    # 2. ОБРАБОТКА ОСТАЛЬНЫХ СЕРВЕРОВ
    # ==========================================
    raw_links = []
    for url in SOURCES:
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                raw_links.extend(resp.text.splitlines())
        except Exception as e:
            print(f"Ошибка загрузки {url}: {e}")

    for link in raw_links:
        link = link.strip()
        if link.startswith("vless://"):
            core_link = link.split('#')[0] 
            if core_link not in global_unique_cores:
                global_unique_cores.add(core_link)
                parsed = parse_vless_link(link, "")
                # Тот же фильтр для общей кучи
                if parsed and is_masquerading(parsed, ru_networks):
                    main_parsed.append(parsed)

    for i, out in enumerate(main_parsed):
        out["tag"] = f"proxy_{i}"

    total_chunks = (len(main_parsed) + CHUNK_SIZE - 1) // CHUNK_SIZE 
    for chunk_idx in range(total_chunks):
        start_idx = chunk_idx * CHUNK_SIZE
        end_idx = start_idx + CHUNK_SIZE
        chunk_outbounds = main_parsed[start_idx:end_idx]
        server_number = chunk_idx + 1
        
        config_profile = {
            "remarks": f"🇲🇦 🗽 LTE {server_number} | t.me/telegaproxys",
            "observatory": {"subjectSelector": ["proxy_"], "probeUrl": "https://www.google.com/generate_204", "probeInterval": "10s"},
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "balancers": [{"tag": "best_ping_balancer", "selector": ["proxy_"], "strategy": {"type": "leastPing"}}],
                "rules": [
                    {"type": "field", "protocol": ["bittorrent"], "outboundTag": "direct"},
                    {"type": "field", "domain": DIRECT_DOMAINS, "outboundTag": "direct"},
                    {"type": "field", "domain": ["geosite:telegram", "domain:telegram.org", "domain:t.me"], "balancerTag": "best_ping_balancer"},
                    {"type": "field", "ip": ["geoip:telegram", "91.108.4.0/22", "91.108.8.0/22", "91.108.12.0/22", "91.108.16.0/22", "91.108.56.0/22", "149.154.160.0/20", "185.76.151.0/24"], "balancerTag": "best_ping_balancer"},
                    {"type": "field", "network": "tcp,udp", "balancerTag": "best_ping_balancer"}
                ]
            },
            "outbounds": chunk_outbounds + [{"tag": "direct", "protocol": "freedom"}, {"tag": "block", "protocol": "blackhole"}],
            "inbounds": [{"tag": "socks", "port": 10808, "protocol": "socks", "settings": {"udp": True, "auth": "noauth"}, "sniffing": {"enabled": True, "destOverride": ["http", "tls"]}}, {"tag": "http", "port": 10809, "protocol": "http", "settings": {"allowTransparent": False}}],
            "dns": {"servers": ["1.1.1.1", "1.0.0.1"], "queryStrategy": "IPIfNonMatch"}
        }
        configs_array.append(config_profile)

    # ==========================================
    # 3. СОХРАНЕНИЕ
    # ==========================================
    with open("custom_sub.json", "w", encoding="utf-8") as f:
        json.dump(configs_array, f, indent=2, ensure_ascii=False)
        print(f"Готово! custom_sub.json обновлен. Идеальных маскировочных нод: {len(main_parsed) + len(top_reserve)}")

if __name__ == "__main__":
    main()
