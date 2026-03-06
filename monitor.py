#!/usr/bin/env python3
"""PreScaler Sunucu Monitör"""

import subprocess
import datetime
import json
import os
import sys
import time

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

# Ayarlar
ALLOWED_IPS = ["185.139.196.1", "34.240.218.44"]
SSH_HOST = "prescaler"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "monitor.jsonl")
DAILY_FILE = os.path.join(LOG_DIR, "daily_summary.json")
MAX_LOG_DAYS = 30

console = Console()


# ─── Yardımcı Fonksiyonlar ───

def get_public_ip():
    try:
        r = subprocess.run(["curl", "-s", "--max-time", "5", "https://api.ipify.org"],
                           capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    except:
        return None


def ip_matches(ip):
    return ip in ALLOWED_IPS


def ssh_health_check():
    cmd = ["ssh", "-o", "ConnectTimeout=10", "-o", "StrictHostKeyChecking=no",
           SSH_HOST, "uptime && df -h / | tail -1 && free -h 2>/dev/null | grep Mem || echo 'memory: N/A'"]
    start = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        latency = round(time.time() - start, 2)
        if r.returncode == 0:
            return True, r.stdout.strip(), latency
        return False, r.stderr.strip(), latency
    except subprocess.TimeoutExpired:
        return False, "SSH zaman aşımı", round(time.time() - start, 2)
    except Exception as e:
        return False, str(e), 0


def notify(title, message):
    subprocess.run([
        "osascript", "-e",
        f'display notification "{message}" with title "{title}" sound name "default"'
    ], capture_output=True)


# ─── Log Fonksiyonları ───

def write_log(entry):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_logs(days=None, limit=None):
    if not os.path.exists(LOG_FILE):
        return []
    logs = []
    cutoff = None
    if days:
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    with open(LOG_FILE) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if cutoff and entry.get("time", "") < cutoff:
                    continue
                logs.append(entry)
            except:
                continue
    if limit:
        logs = logs[-limit:]
    return logs


def rotate_logs():
    """30 günden eski logları sil"""
    if not os.path.exists(LOG_FILE):
        return
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=MAX_LOG_DAYS)).isoformat()
    kept = []
    with open(LOG_FILE) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("time", "") >= cutoff:
                    kept.append(line)
            except:
                continue
    with open(LOG_FILE, "w") as f:
        f.writelines(kept)


def update_daily(status):
    today = datetime.date.today().isoformat()
    data = {}
    if os.path.exists(DAILY_FILE):
        with open(DAILY_FILE) as f:
            data = json.load(f)
    if today not in data:
        data[today] = {"total": 0, "up": 0, "down": 0, "skip": 0}
    data[today]["total"] += 1
    data[today][status] += 1
    with open(DAILY_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data


# ─── Ana Komutlar ───

def cmd_check():
    """Saatlik kontrol"""
    now = datetime.datetime.now().isoformat(timespec="seconds")
    entry = {"time": now, "status": "", "ip": "", "output": "", "latency": 0}

    my_ip = get_public_ip()
    entry["ip"] = my_ip or "N/A"

    if not my_ip:
        entry["status"] = "skip"
        entry["output"] = "Public IP alınamadı"
        write_log(entry)
        update_daily("skip")
        print(f"[{now}] SKIP - IP alınamadı")
        return

    if not ip_matches(my_ip):
        entry["status"] = "skip"
        entry["output"] = f"IP eşleşmedi ({my_ip})"
        write_log(entry)
        update_daily("skip")
        print(f"[{now}] SKIP - IP eşleşmedi ({my_ip})")
        return

    ok, output, latency = ssh_health_check()
    entry["latency"] = latency
    entry["output"] = output

    if ok:
        entry["status"] = "up"
        update_daily("up")
        print(f"[{now}] UP ✓ ({latency}s)")
    else:
        entry["status"] = "down"
        update_daily("down")
        notify("⚠️ PreScaler DOWN", f"Sunucu erişilemez: {output[:80]}")
        print(f"[{now}] DOWN ✗ - {output}")

    write_log(entry)
    rotate_logs()


def cmd_summary():
    """Günlük özet bildirimi + terminalde göster"""
    data = {}
    if os.path.exists(DAILY_FILE):
        with open(DAILY_FILE) as f:
            data = json.load(f)

    if not data:
        console.print("[yellow]Henüz veri yok.[/yellow]")
        return

    table = Table(title="📊 PreScaler Sunucu Monitör - Günlük Özet", box=box.ROUNDED, show_lines=True)
    table.add_column("Tarih", style="cyan", justify="center")
    table.add_column("Toplam", justify="center")
    table.add_column("✅ UP", style="green", justify="center")
    table.add_column("❌ DOWN", style="red", justify="center")
    table.add_column("⏭ SKIP", style="yellow", justify="center")
    table.add_column("Durum", justify="center")

    for date in sorted(data.keys(), reverse=True)[:14]:
        d = data[date]
        if d["down"] > 0:
            status = Text("🔴 SORUNLU", style="bold red")
        elif d["up"] > 0:
            status = Text("🟢 SAĞLIKLI", style="bold green")
        else:
            status = Text("⚪ KONTROL YOK", style="dim")
        table.add_row(date, str(d["total"]), str(d["up"]), str(d["down"]), str(d["skip"]), status)

    console.print(table)

    # macOS bildirimi
    today = datetime.date.today().isoformat()
    if today in data:
        s = data[today]
        emoji = "🟢" if s["down"] == 0 and s["up"] > 0 else "🔴" if s["down"] > 0 else "⚪"
        msg = f"{emoji} UP:{s['up']} DOWN:{s['down']} SKIP:{s['skip']} / Toplam:{s['total']}"
        notify("PreScaler Günlük Rapor", msg)


def cmd_logs(limit=20):
    """Son kontrolleri göster"""
    logs = read_logs(limit=limit)
    if not logs:
        console.print("[yellow]Henüz log yok.[/yellow]")
        return

    table = Table(title="📋 Son Kontroller", box=box.ROUNDED, show_lines=True)
    table.add_column("Zaman", style="cyan", width=20)
    table.add_column("Durum", justify="center", width=8)
    table.add_column("IP", width=16)
    table.add_column("Latency", justify="right", width=8)
    table.add_column("Detay", max_width=60)

    for e in logs:
        t = e.get("time", "?")
        s = e.get("status", "?")
        if s == "up":
            status = Text("✅ UP", style="bold green")
        elif s == "down":
            status = Text("❌ DOWN", style="bold red")
        else:
            status = Text("⏭ SKIP", style="yellow")

        lat = f"{e.get('latency', 0)}s" if e.get("latency") else "-"
        output = e.get("output", "")[:60]
        table.add_row(t, status, e.get("ip", ""), lat, output)

    console.print(table)


def cmd_status():
    """Anlık durum kontrolü"""
    console.print(Panel("🔍 Anlık Durum Kontrolü", style="bold blue"))

    my_ip = get_public_ip()
    if not my_ip:
        console.print("[red]❌ Public IP alınamadı[/red]")
        return

    ip_ok = ip_matches(my_ip)
    console.print(f"  IP Adresi: [cyan]{my_ip}[/cyan]  {'[green]✓ Eşleşti[/green]' if ip_ok else '[red]✗ Eşleşmedi[/red]'}")

    if not ip_ok:
        console.print("[yellow]  VPN veya ofis ağına bağlanın.[/yellow]")
        return

    console.print("  SSH bağlantısı deneniyor...")
    ok, output, latency = ssh_health_check()

    if ok:
        console.print(f"  [bold green]✅ Sunucu UP[/bold green] (yanıt: {latency}s)")
        for line in output.split("\n"):
            console.print(f"    [dim]{line}[/dim]")
    else:
        console.print(f"  [bold red]❌ Sunucu DOWN[/bold red] ({latency}s)")
        console.print(f"    [red]{output}[/red]")


def cmd_help():
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column(style="green")
    table.add_column()
    table.add_row("check", "Saatlik kontrol çalıştır (cron)")
    table.add_row("status", "Anlık durum kontrolü")
    table.add_row("summary", "Günlük özet tablosu + bildirim")
    table.add_row("logs [N]", "Son N kontrolü göster (varsayılan: 20)")
    console.print(Panel(table, title="🖥  PreScaler Monitör", subtitle="Kullanım: monitor.py <komut>"))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "check":
        cmd_check()
    elif cmd == "summary":
        cmd_summary()
    elif cmd == "logs":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        cmd_logs(n)
    elif cmd == "status":
        cmd_status()
    else:
        cmd_help()
