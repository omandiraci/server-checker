# 🛠 Administrative Guide - Server Checker

## İlk Kurulum Adımları

### 1. Projeyi Klonla ve Bağımlılıkları Kur

```bash
git clone https://github.com/omandiraci/server-checker.git
cd server-checker
python3 -m venv .venv
source .venv/bin/activate
pip install rich
```

### 2. Yapılandırma

```bash
cp .env.example .env
```

`.env` dosyasını kendi bilgilerinizle düzenleyin:

```env
ALLOWED_IPS=<ofis-ip>,<vpn-ip>
SSH_HOST=<ssh-config-host-adı>
MAX_LOG_DAYS=30
```

### 3. SSH Erişimini Doğrula

```bash
ssh <ssh-host> "uptime"
```

Bu komut sunucunun uptime bilgisini döndürmelidir.

### 4. Cron Job'ları Kur

```bash
VENV_PY="$HOME/path/to/server-checker/.venv/bin/python3"
SCRIPT="$HOME/path/to/server-checker/monitor.py"
LOGF="$HOME/path/to/server-checker/logs/cron.log"

(crontab -l 2>/dev/null | grep -v "server-checker"; \
echo "0 * * * * $VENV_PY $SCRIPT check >> $LOGF 2>&1"; \
echo "0 18 * * * $VENV_PY $SCRIPT summary >> $LOGF 2>&1") | crontab -
```

Doğrulama:

```bash
crontab -l | grep server-checker
```

### 5. Shell Alias Ekle

```bash
echo "alias monitor='~/path/to/server-checker/.venv/bin/python3 ~/path/to/server-checker/monitor.py'" >> ~/.zshrc
source ~/.zshrc
```

---

## Günlük Operasyonlar

### Anlık Durum Kontrolü

```bash
monitor status
```

Çıktı: IP doğrulama, SSH bağlantı durumu, uptime, disk kullanımı, memory bilgisi ve yanıt süresi.

### Logları İnceleme

```bash
monitor logs        # Son 20 kayıt
monitor logs 100    # Son 100 kayıt
```

Her log kaydı şunları içerir:
- Zaman damgası
- Durum (UP / DOWN / SKIP)
- SSH yanıt süresi (latency)
- Sunucu çıktısı (uptime, disk, memory)

### Günlük Özet

```bash
monitor summary
```

Son 14 günün tablosunu gösterir ve macOS bildirimi gönderir.

---

## Sorun Giderme

### "SKIP - IP eşleşmedi"

İzin verilen ağda değilsiniz.

**Çözüm:** VPN'e bağlanın veya `.env` dosyasındaki `ALLOWED_IPS`'e yeni IP ekleyin.

### "SKIP - Public IP alınamadı"

İnternet bağlantısı yok veya `api.ipify.org` erişilemez.

### "DOWN - SSH zaman aşımı"

Sunucu erişilemez veya SSH portu kapalı.

**Kontrol:**
```bash
ssh -v <ssh-host> "uptime"
```

### Cron Çalışmıyor

```bash
# Cron logunu kontrol et
cat /path/to/server-checker/logs/cron.log

# macOS'ta cron izni gerekebilir:
# Sistem Ayarları → Gizlilik ve Güvenlik → Tam Disk Erişimi → cron
```

### macOS Bildirimleri Gelmiyor

```bash
osascript -e 'display notification "Test" with title "Monitor" sound name "default"'
```

Bildirim gelmiyorsa: **Sistem Ayarları → Bildirimler → Script Editor** bildirimlerinin açık olduğundan emin olun.

---

## Bakım

### Manuel Log Temizliği

```bash
rm /path/to/server-checker/logs/*.jsonl
rm /path/to/server-checker/logs/daily_summary.json
```

### Cron Job'ları Kaldırma

```bash
crontab -l | grep -v "server-checker" | crontab -
```

### Kontrol Sıklığını Değiştirme

```cron
# Her 30 dakikada bir
*/30 * * * * /path/to/monitor.py check

# Sadece mesai saatlerinde (09-18, Pzt-Cum)
0 9-18 * * 1-5 /path/to/monitor.py check
```

---

## Güvenlik Notları

- `.env` dosyası repoya dahil edilmez (`.gitignore`'da)
- IP adresleri ve SSH host bilgileri sadece `.env` dosyasında tutulur
- `monitor status` komutu IP adresini maskeleyerek gösterir
- SSH bağlantısı mevcut `~/.ssh/config` yapılandırmasını kullanır
- Log dosyaları otomatik olarak belirtilen süre sonunda temizlenir
