# 🖥 Server Checker

SSH health check ile sunucu durumunu izleyen, günlük macOS bildirimi gönderen ve detaylı log tutan bir monitoring aracı.

## Özellikler

- ⏰ Saatlik otomatik SSH health check (uptime, disk, memory)
- 🔐 IP doğrulama (izin verilen ağ kontrolü)
- 📊 Rich ile renkli terminal tabloları
- 🔔 macOS bildirimleri (sunucu down → anlık, günlük özet → 18:00)
- 📈 Yanıt süresi (latency) takibi
- 📋 JSON formatında yapılandırılmış loglar
- 🔄 Otomatik log rotation (30 gün)
- 🔒 Hassas bilgiler `.env` dosyasında (repoya dahil değil)

## Kurulum

```bash
git clone https://github.com/omandiraci/server-checker.git
cd server-checker
python3 -m venv .venv
source .venv/bin/activate
pip install rich
```

### Yapılandırma

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin:

```env
ALLOWED_IPS=1.2.3.4,5.6.7.8      # İzin verilen IP adresleri (virgülle ayır)
SSH_HOST=your-ssh-host              # ~/.ssh/config'deki host adı
MAX_LOG_DAYS=30                     # Log saklama süresi (gün)
```

### SSH Yapılandırması

`~/.ssh/config` dosyanızda sunucu tanımlı olmalıdır:

```
Host your-ssh-host
    HostName <sunucu-ip>
    User <kullanıcı>
    IdentityFile ~/.ssh/keys/<key-dosyası>.pem
```

## Kullanım

```bash
# Alias tanımla (tek seferlik)
echo "alias monitor='~/path/to/server-checker/.venv/bin/python3 ~/path/to/server-checker/monitor.py'" >> ~/.zshrc
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

```cron
# Saatlik health check
0 * * * * /path/to/.venv/bin/python3 /path/to/monitor.py check >> /path/to/logs/cron.log 2>&1

# Günlük özet bildirimi (18:00)
0 18 * * * /path/to/.venv/bin/python3 /path/to/monitor.py summary >> /path/to/logs/cron.log 2>&1
```

## Proje Yapısı

```
server-checker/
├── .env.example        # Örnek yapılandırma
├── .env                # Gerçek yapılandırma (gitignore)
├── .gitignore
├── monitor.py          # Ana uygulama
├── logs/               # Log dosyaları (gitignore)
├── README.md
└── ADMIN_GUIDE.md
```

## Gereksinimler

- Python 3.9+
- macOS (bildirimler için)
- SSH erişimi yapılandırılmış olmalı
