import requests
import urllib.parse
import json
import re
import base64
import time

SOURCES = [
    "https://raw.githubusercontent.com/luxxuria/harvester/refs/heads/main/top_600.txt",
    "https://raw.githubusercontent.com/zieng2/wl/refs/heads/main/vless_universal.txt",
    "https://raw.githubusercontent.com/lm705/vair/refs/heads/main/vless_alive.txt"
]

def get_links_from_text(text):
    decoded = ""
    try:
        pad = len(text.strip()) % 4
        padded = text.strip() + '=' * (4 - pad) if pad else text.strip()
        decoded = base64.b64decode(padded).decode('utf-8', errors='ignore')
    except: pass
    combined = text + "\n" + decoded
    return re.findall(r'vless://[^\s"\'<>]+', combined)

def batch_check_locations(links):
    ip_map = {}
    ips_to_check = set()
    for link in links:
        try:
            ip = urllib.parse.urlparse(link).hostname
            if not ip: continue
            name_match = re.search(r'#(.*)$', link)
            name = urllib.parse.unquote(name_match.group(1)).lower() if name_match else ""
            if any(x in name for x in ['ru', 'russia', 'россия', 'москва', 'msk']):
                ip_map[ip] = 'RU'
            else:
                ips_to_check.add(ip)
        except: continue

    ips_list = list(ips_to_check)
    for i in range(0, len(ips_list), 100):
        try:
            data = [{"query": ip, "fields": "query,countryCode"} for ip in ips_list[i:i+100]]
            res = requests.post("http://ip-api.com/batch", json=data, timeout=10).json()
            for item in res: ip_map[item['query']] = item.get('countryCode', 'EU')
        except: pass
        time.sleep(0.5)
    return ip_map

def parse_vless_link(link, tag_name):
    try:
        parsed = urllib.parse.urlparse(link)
        user_id = parsed.username
        address = parsed.hostname
        port = int(parsed.port) if parsed.port else 443 
        
        if not address or len(user_id) < 10: return None

        params = urllib.parse.parse_qs(parsed.query)
        flow = params.get('flow', [''])[0]
        network = params.get('type', ['tcp'])[0]
        security = params.get('security', ['none'])[0]

        user_obj = {"id": user_id, "encryption": "none", "flow": flow if flow else ""}
        if network not in ['tcp', 'ws', 'grpc', 'xhttp', 'http', 'kcp', 'quic']: network = 'tcp'
            
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
            stream_settings["tlsSettings"] = {"serverName": params.get('sni', [address])[0], "show": False}
            fp = params.get('fp', [''])[0]
            if fp: stream_settings["tlsSettings"]["fingerprint"] = fp

        if network == "tcp": stream_settings["tcpSettings"] = {}
        elif network == "ws":
            stream_settings["wsSettings"] = {"path": params.get('path', ['/'])[0]}
            host = params.get('host', [''])[0]
            if host: stream_settings["wsSettings"]["headers"] = {"Host": host}
        elif network == "grpc":
            svc = params.get('serviceName', [''])[0]
            if not svc: svc = params.get('path', [''])[0]
            stream_settings["grpcSettings"] = {"serviceName": svc, "multiMode": True}

        return {
            "tag": tag_name, "protocol": "vless",
            "settings": {"vnext": [{"address": address, "port": port, "users": [user_obj]}]},
            "streamSettings": stream_settings
        }
    except: return None

def generate_profile(name, servers_chunk):
    outbounds = []
    tags = [] 
    
    for i, link in enumerate(servers_chunk):
        tag = f"cand-{i+1:02d}"
        parsed = parse_vless_link(link, tag)
        if parsed:
            outbounds.append(parsed)
            tags.append(tag)
            
    if not tags: return None
        
    outbounds.append({"tag": "direct", "protocol": "freedom"})
    outbounds.append({"tag": "block", "protocol": "blackhole"})

    return {
        "remarks": name,
        "dns": {
            "servers": ["https://8.8.8.8/dns-query", "https://8.8.8.8/dns-query"],
            "queryStrategy": "UseIP"
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
        ],
        "log": {
            "loglevel": "warning"
        },
        "outbounds": outbounds,
        "observatory": {
            "enableConcurrency": True,
            "probeInterval": "1m",
            "probeUrl": "https://www.google.com/generate_204",
            "subjectSelector": tags 
        },
        "routing": {
            "domainMatcher": "hybrid",
            "domainStrategy": "IPIfNonMatch",
            "balancers": [
                {
                    "tag": "best_ping_balancer",
                    "selector": tags, 
                    "strategy": {"type": "leastPing"} 
                }
            ],
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
                {
                    "type": "field",
                    "inboundTag": ["socks", "http"], 
                    "network": "tcp,udp",
                    "balancerTag": "best_ping_balancer"
                }
            ]
        }
    }

def main():
    raw_links = []
    for url in SOURCES:
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200: raw_links.extend(get_links_from_text(r.text))
        except: pass

    raw_links = list(set(raw_links))
    ip_map = batch_check_locations(raw_links)
    
    ru_links = []
    eu_links = []
    
    for link in raw_links:
        try:
            ip = urllib.parse.urlparse(link).hostname
            if ip_map.get(ip) == 'RU': ru_links.append(link)
            else: eu_links.append(link)
        except: continue

    final_json_array = []
    
    for i in range(0, len(ru_links), 10):
        profile = generate_profile(f"🇲🇦 🗽 LTE RU {(i // 10) + 1} | t.me/telegaproxys", ru_links[i:i + 10])
        if profile: final_json_array.append(profile)

    for i in range(0, len(eu_links), 10):
        profile = generate_profile(f"🇲🇦 🗽 LTE EU {(i // 10) + 1} | t.me/telegaproxys", eu_links[i:i + 10])
        if profile: final_json_array.append(profile)

    with open('custom_sub.json', 'w', encoding='utf-8') as f:
        json.dump(final_json_array, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
