# 🖥 PreScaler Server Monitor

Saatlik SSH health check ile sunucu durumunu izleyen, günlük macOS bildirimi gönderen ve detaylı log tutan bir monitoring aracı.

## Özellikler

- ⏰ Saatlik otomatik SSH health check (uptime, disk, memory)
- 🔐 IP doğrulama (ofis / VPN IP kontrolü)
- 📊 Rich ile renkli terminal tabloları
- 🔔 macOS bildirimleri (sunucu down → anlık, günlük özet → 18:00)
- 📈 Yanıt süresi (latency) takibi
- 📋 JSON formatında yapılandırılmış loglar
- 🔄 Otomatik log rotation (30 gün)

## Kurulum

```bash
git clone <repo-url>
cd server-monitor
python3 -m venv .venv
source .venv/bin/activate
pip install rich
```

## SSH Yapılandırması

`~/.ssh/config` dosyanızda sunucu tanımlı olmalıdır:

```
Host prescaler
    HostName <sunucu-ip>
    User <kullanıcı>
    IdentityFile ~/.ssh/keys/<key-dosyası>.pem
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

## Kullanım

```bash
# Alias tanımla (tek seferlik)
echo "alias monitor='~/Desktop/Projects/server-monitor/.venv/bin/python3 ~/Desktop/Projects/server-monitor/monitor.py'" >> ~/.zshrc
source ~/.zshrc
```

| Komut | Açıklama |
|-------|----------|
| `monitor status` | Anlık durum kontrolü |
| `monitor summary` | Günlük özet tablosu + macOS bildirimi |
| `monitor logs` | Son 20 kontrol logu |
| `monitor logs 50` | Son 50 kontrol logu |
| `monitor check` | Manuel kontrol tetikle |

## Cron Kurulumu

```bash
crontab -e
```

Aşağıdaki satırları ekleyin:

```cron
# Saatlik health check
0 * * * * /path/to/server-monitor/.venv/bin/python3 /path/to/server-monitor/monitor.py check >> /path/to/server-monitor/logs/cron.log 2>&1

# Günlük özet bildirimi (18:00)
0 18 * * * /path/to/server-monitor/.venv/bin/python3 /path/to/server-monitor/monitor.py summary >> /path/to/server-monitor/logs/cron.log 2>&1
```

## Yapılandırma

`monitor.py` dosyasının başındaki ayarlar:

| Değişken | Açıklama | Varsayılan |
|----------|----------|------------|
| `ALLOWED_IPS` | İzin verilen IP adresleri | Ofis + VPN IP'leri |
| `SSH_HOST` | SSH config'deki host adı | `prescaler` |
| `MAX_LOG_DAYS` | Log saklama süresi | 30 gün |

## Proje Yapısı

```
server-monitor/
├── monitor.py          # Ana uygulama
├── logs/
│   ├── monitor.jsonl   # Kontrol logları (JSON Lines)
│   ├── daily_summary.json  # Günlük özet verisi
│   └── cron.log        # Cron çıktı logu
├── README.md
└── ADMIN_GUIDE.md
```

## Gereksinimler

- Python 3.9+
- macOS (bildirimler için)
- SSH erişimi yapılandırılmış olmalı
- VPN veya ofis ağı bağlantısı
