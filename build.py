import requests
import urllib.parse
import json

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

CHUNK_SIZE = 250 

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

        network_type = params.get("type", "tcp")
        security_type = params.get("security", "none")

        # ЖЕСТКИЙ ФИЛЬТР: если Reality без ключа - это сломает ядро, выкидываем
        if security_type == "reality" and not params.get("pbk"):
            return None

        user = {
            "id": uuid,
            "encryption": params.get("encryption", "none")
        }

        # ЖЕСТКИЙ ФИЛЬТР: Flow разрешен только на TCP. Иначе краш ядра.
        flow = params.get("flow", "")
        if flow and network_type == "tcp":
            user["flow"] = flow

        outbound = {
            "tag": f"proxy_{index}",
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": address,
                    "port": int(port),
                    "users": [user]
                }]
            },
            "streamSettings": {
                "network": network_type,
                "security": security_type
            }
        }

        # 1. Настройки безопасности
        if security_type == "reality":
            outbound["streamSettings"]["realitySettings"] = {
                "serverName": params.get("sni", address), # Если нет SNI, ставим IP
                "publicKey": params.get("pbk", ""),
                "shortId": params.get("sid", ""),
                "fingerprint": params.get("fp", "chrome"),
                "spiderX": params.get("spx", "/")
            }
        elif security_type == "tls":
            outbound["streamSettings"]["tlsSettings"] = {
                "serverName": params.get("sni", params.get("host", address)),
                "fingerprint": params.get("fp", "chrome")
            }
            alpn = params.get("alpn", "")
            if alpn:
                outbound["streamSettings"]["tlsSettings"]["alpn"] = alpn.split(',')

        # 2. Настройки транспорта
        if network_type == "ws":
            outbound["streamSettings"]["wsSettings"] = {
                "path": params.get("path", "/"),
                "headers": {
                    "Host": params.get("host", params.get("sni", address))
                }
            }
        elif network_type == "grpc":
            # Ищем имя сервиса либо в serviceName, либо в path
            service_name = params.get("serviceName", params.get("path", ""))
            outbound["streamSettings"]["grpcSettings"] = {
                "serviceName": service_name,
                "multiMode": params.get("mode", "multi") == "multi"
            }
        elif network_type == "tcp":
            header_type = params.get("headerType", "none")
            if header_type == "http":
                outbound["streamSettings"]["tcpSettings"] = {
                    "header": {
                        "type": "http",
                        "request": {
                            "path": [params.get("path", "/")]
                        }
                    }
                }
        
        return outbound
    except Exception:
        return None

def main():
    raw_links = []
    for url in SOURCES:
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                raw_links.extend(resp.text.splitlines())
        except Exception:
            pass

    unique_links_dict = {}
    for link in raw_links:
        link = link.strip()
        if link.startswith("vless://"):
            core_link = link.split('#')[0] 
            if core_link not in unique_links_dict:
                unique_links_dict[core_link] = link
                
    unique_links = list(unique_links_dict.values())
    
    valid_outbounds = []
    for i, link in enumerate(unique_links):
        parsed = parse_vless_link(link, i)
        if parsed:
            valid_outbounds.append(parsed)

    configs_array = []
    total_chunks = (len(valid_outbounds) + CHUNK_SIZE - 1) // CHUNK_SIZE 

    for chunk_idx in range(total_chunks):
        start_idx = chunk_idx * CHUNK_SIZE
        end_idx = start_idx + CHUNK_SIZE
        chunk_outbounds = valid_outbounds[start_idx:end_idx]
        
        if not chunk_outbounds:
            continue
            
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

    with open("custom_sub.json", "w", encoding="utf-8") as f:
        json.dump(configs_array, f, indent=2, ensure_ascii=False)
        print(f"Готово! Создан custom_sub.json, внутри {len(configs_array)} серверов.")

if __name__ == "__main__":
    main()
