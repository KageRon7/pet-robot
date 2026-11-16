"""Gövde demosu: Wokwi'deki ESP32'ye sırayla hareket komutları gönderir."""
import json, sys, time
import serial

PORT = sys.argv[1] if len(sys.argv) > 1 else "rfc2217://localhost:4000"
ser = serial.serial_for_url(PORT, baudrate=115200, timeout=0.5)
seq = 0

def gonder(cmd, **alanlar):
    global seq
    seq += 1
    mesaj = json.dumps({"v": 1, "seq": seq, "cmd": cmd, **alanlar}) + "\n"
    ser.write(mesaj.encode())
    bitis = time.time() + 2
    while time.time() < bitis:
        satir = ser.readline().decode(errors="ignore").strip()
        if satir.startswith("{"):
            try:
                cevap = json.loads(satir)
            except ValueError:
                continue
            # Echo yansımasını yoksay, sadece ack dönen cevabı al
            if "ack" in cevap and cevap.get("ack") == seq:
                print(f"[{seq}] {cmd} -> {cevap}")
                return cevap
    print(f"[{seq}] {cmd} -> CEVAP YOK")

def hareket(deg, ms, isim=""):
    print("==", isim)
    gonder("move", deg=deg, ms=ms)
    time.sleep(ms / 1000 + 0.2)

# Sıra: [S0 gövde, S1 baş sağ-sol, S2 baş yukarı-aşağı, S3 sol kulak, S4 sağ kulak]
time.sleep(2)  # ESP32 açılışı için
gonder("ping")
gonder("neutral"); time.sleep(1.2)

hareket([60, 90, 90, 132, 48], 800, "gövde sola")
hareket([120, 90, 90, 132, 48], 1200, "gövde sağa")
hareket([90, 90, 90, 132, 48], 800, "gövde ortaya")

hareket([90, 50, 90, 132, 48], 700, "baş sola")
hareket([90, 130, 90, 132, 48], 1200, "baş sağa")
hareket([90, 90, 90, 132, 48], 700, "baş ortaya")

hareket([90, 90, 120, 132, 48], 600, "baş yukarı")
hareket([90, 90, 85, 132, 48], 800, "baş aşağı")
hareket([90, 90, 90, 132, 48], 600, "baş düz")

hareket([90, 90, 90, 100, 80], 400, "kulaklar oynuyor 1")
hareket([90, 90, 90, 140, 40], 400, "kulaklar oynuyor 2")
hareket([90, 90, 90, 100, 80], 400, "kulaklar oynuyor 3")

hareket([75, 70, 105, 100, 80], 900, "mutlu poz")

print("== Sınır Dışı Açı Testi (out_of_range bekleniyor)")
gonder("move", deg=[10, 90, 90, 132, 48], ms=500)
time.sleep(1)

print("== 3 Saniye Güvenlik Sigortası Testi (Otomatik nötre dönecek...)")
time.sleep(3.5)
print("Demo bitti!")