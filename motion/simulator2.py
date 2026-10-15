import tkinter as tk

# Kedinin eklemleri ve hareket araliklari
EKLEMLER = {
    "body_yaw": (-45, 45),
    "head_pan": (-90, 90),
    "head_tilt": (-10, 45),
    "ear_left": (0, 1),
    "ear_right": (0, 1),
}



class KediSimulatoru:
    def __init__(self, pencere):
        self.pencere = pencere
        self.pencere.title("Kedi Simülatörü")

        # Kaydirma cubuklarini saklayacagimiz sozluk
        self.cubuklar = {}

        self.surum = {ad: 0 for ad in EKLEMLER}

        # Her eklem icin bir kaydirma cubugu olustur
        for ad, (en_az, en_cok) in EKLEMLER.items():
            adim = 0.01 if en_cok <= 1 else 1

            cubuk = tk.Scale(
                pencere,
                from_=en_az,
                to=en_cok,
                resolution=adim,
                orient="horizontal",
                length=320,
                label=ad
            )

            cubuk.pack(padx=12, pady=4)

            self.cubuklar[ad] = cubuk

    def git(self, ad, hedef, sure_ms=1000):
        self.surum[ad] += 1
        benim_surumum = self.surum[ad]

        baslangic = self.cubuklar[ad].get()
        adim_sayisi = max(1, sure_ms // 20)

        def adim(i):
            if self.surum[ad] != benim_surumum:
                return

            oran = i / adim_sayisi
            deger = baslangic + (hedef - baslangic) * oran

            self.cubuklar[ad].set(deger)

            if i < adim_sayisi:
                self.pencere.after(20, adim, i + 1)

        adim(1)



if __name__ == "__main__":
    kok = tk.Tk()
    simulator = KediSimulatoru(kok)

    # Pencere acildiktan 500 ms sonra sol kulagi hareket ettir
    kok.after(500, simulator.git, "ear_left", 1.0, 1000)

    kok.mainloop()
