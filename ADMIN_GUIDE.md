# 🛠 Administrative Guide - PreScaler Server Monitor

## İlk Kurulum Adımları

### 1. Projeyi Klonla ve Bağımlılıkları Kur

```bash
cd ~/Desktop/Projects
git clone <repo-url> server-monitor
cd server-monitor
python3 -m venv .venv
source .venv/bin/activate
pip install rich
```

### 2. SSH Erişimini Doğrula

```bash
ssh prescaler "uptime"
```

Bu komut sunucunun uptime bilgisini döndürmelidir. Hata alıyorsanız `~/.ssh/config` dosyanızı kontrol edin.

### 3. IP Adreslerini Yapılandır

`monitor.py` dosyasında `ALLOWED_IPS` listesini güncelleyin:

```python
ALLOWED_IPS = ["185.139.196.1", "34.240.218.44"]
```

Yeni bir ofis veya VPN IP'si eklemek için bu listeye ekleme yapın.

### 4. Cron Job'ları Kur

```bash
VENV_PY="$HOME/Desktop/Projects/server-monitor/.venv/bin/python3"
SCRIPT="$HOME/Desktop/Projects/server-monitor/monitor.py"
LOGF="$HOME/Desktop/Projects/server-monitor/logs/cron.log"

(crontab -l 2>/dev/null | grep -v "server-monitor"; \
echo "0 * * * * $VENV_PY $SCRIPT check >> $LOGF 2>&1"; \
echo "0 18 * * * $VENV_PY $SCRIPT summary >> $LOGF 2>&1") | crontab -
```

Doğrulama:

```bash
crontab -l | grep server-monitor
```

### 5. Shell Alias Ekle

```bash
echo "alias monitor='~/Desktop/Projects/server-monitor/.venv/bin/python3 ~/Desktop/Projects/server-monitor/monitor.py'" >> ~/.zshrc
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
- Public IP adresi
- SSH yanıt süresi (latency)
- Sunucu çıktısı (uptime, disk, memory)

### Günlük Özet

```bash
monitor summary
```

Son 14 günün tablosunu gösterir ve macOS bildirimi gönderir.

---

## Sorun Giderme

### "SKIP - IP eşleşmedi" Logu

VPN veya ofis ağına bağlı değilsiniz. Bu normal bir durumdur, kontrol atlanır.

**Çözüm:** VPN'e bağlanın veya yeni IP'yi `ALLOWED_IPS` listesine ekleyin.

### "SKIP - Public IP alınamadı" Logu

İnternet bağlantısı yok veya `api.ipify.org` erişilemez.

**Çözüm:** İnternet bağlantınızı kontrol edin.

### "DOWN - SSH zaman aşımı" Logu

Sunucu erişilemez veya SSH portu kapalı.

**Kontrol adımları:**
```bash
# SSH bağlantısını manuel test et
ssh -v prescaler "uptime"

# Sunucu IP'sine ping at
ping -c 3 <sunucu-ip>
```

### Cron Çalışmıyor

```bash
# Cron logunu kontrol et
cat ~/Desktop/Projects/server-monitor/logs/cron.log

# Cron job'ların listesi
crontab -l

# macOS'ta cron izni gerekebilir:
# Sistem Ayarları → Gizlilik ve Güvenlik → Tam Disk Erişimi → cron ekle
```

### macOS Bildirimleri Gelmiyor

```bash
# Bildirimi manuel test et
osascript -e 'display notification "Test" with title "Monitor" sound name "default"'
```

Bildirim gelmiyorsa: **Sistem Ayarları → Bildirimler → Script Editor** bildirimlerinin açık olduğundan emin olun.

---

## Bakım

### Log Rotation

Loglar otomatik olarak 30 gün sonra temizlenir. Bu süreyi değiştirmek için:

```python
MAX_LOG_DAYS = 30  # İstediğiniz gün sayısı
```

### Manuel Log Temizliği

```bash
# Tüm logları sil
rm ~/Desktop/Projects/server-monitor/logs/*.jsonl
rm ~/Desktop/Projects/server-monitor/logs/daily_summary.json

# Cron logunu sil
> ~/Desktop/Projects/server-monitor/logs/cron.log
```

### Cron Job'ları Kaldırma

```bash
crontab -l | grep -v "server-monitor" | crontab -
```

### Kontrol Sıklığını Değiştirme

```bash
crontab -e
```

```cron
# Her 30 dakikada bir
*/30 * * * * /path/to/monitor.py check

# Her 2 saatte bir
0 */2 * * * /path/to/monitor.py check

# Sadece mesai saatlerinde (09-18)
0 9-18 * * 1-5 /path/to/monitor.py check
```

### Yeni Sunucu Ekleme

1. `~/.ssh/config` dosyasına yeni host ekleyin
2. `monitor.py` dosyasını kopyalayıp `SSH_HOST` değerini değiştirin
3. Yeni bir cron job ekleyin
