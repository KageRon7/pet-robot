"""
motion/simulator.py  --  Kedi Simülatörü (Reşat)
 
Bu pencerede iki şey birlikte hareket eder:
    - SOLDA  : kedinin yüz ekranı (gözler, ağız, kaşlar, kulaklar...)  -> motion/yuz.py çizer
    - SAĞDA  : beş motor çubuğu (body_yaw, head_pan, head_tilt, ear_left, ear_right)
 
Kedi açılışta DÜZ durur. Bir duygu çağrılınca (örneğin "happy") ikisi de AYNI klibi aynı anda oynar:
    kontrolcu.duygu_cagir("happy")
Klip bitince kedi yumuşakça düz pozuna döner (ayar: KediKontrolcusu.BITINCE_DAVRANIS).
 
Klipler motion/clips/ klasöründeki JSON dosyalarıdır (Tuğra'nın Yüz Atölyesi'nden).
 
Çalıştırma:
    python motion/simulator.py
"""
 
import logging
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable, Dict, Optional
 
# Dosya doğrudan çalıştırılırsa "klip", paket olarak içe aktarılırsa ".klip" bulunur.
try:
    from .klip import EKLEMLER, YUZ_VARSAYILAN, Enterpolator, Kare, Klip, KlipYukleyici
    from .yuz import KANVAS_GENISLIK, KANVAS_YUKSEKLIK, Cokgen, YuzCizici
except ImportError:
    from klip import EKLEMLER, YUZ_VARSAYILAN, Enterpolator, Kare, Klip, KlipYukleyici
    from yuz import KANVAS_GENISLIK, KANVAS_YUKSEKLIK, Cokgen, YuzCizici
 
logger = logging.getLogger(__name__)
 
# Klipler bu dosyanın yanındaki "clips" klasöründe durur (GitHub: motion/clips).
KLIP_KLASORU = Path(__file__).resolve().parent / "clips"
 
# Duygu butonlarında görünecek Türkçe adlar (Sözleşme B2'deki 7 duygu)
DUYGU_ETIKETLERI = {
    "idle": "Boşta", "happy": "Mutlu", "sad": "Üzgün", "sleepy": "Uykulu",
    "curious": "Meraklı", "playful": "Oyuncu", "startled": "İrkilmiş",
}
 
 
# ----------------------------------------------------------------------------
# 1) YÜZ EKRANI (Tk Canvas)
# ----------------------------------------------------------------------------
 
class YuzEkrani:
    """Kedinin yüzünü gösteren Tk Canvas. Çizim komutlarını yuz.py üretir, burada sadece ekrana koyarız."""
 
    ARKA_PLAN = "#E9E7EF"
 
    def __init__(self, ust: tk.Misc):
        """Canvas'ı oluşturup üst pencereye yerleştirir."""
        self.canvas = tk.Canvas(ust, width=KANVAS_GENISLIK, height=KANVAS_YUKSEKLIK,
                                bg=self.ARKA_PLAN, highlightthickness=0)
        self.canvas.pack()
        self._cizici = YuzCizici(canli=True)   # canli: göz kırpma, akan gözyaşı, dönen spiral gözler
 
    def ciz(self, durum: Dict, t_ms: Optional[float] = None) -> None:
        """Verilen yüz+poz durumunu ekrana çizer (önceki çizimi siler)."""
        if t_ms is None:
            t_ms = time.monotonic() * 1000.0
        ogeler = self._cizici.olustur(durum, t_ms)
        try:
            self.canvas.delete("all")
            for oge in ogeler:
                self._oge_ciz(oge)
        except tk.TclError:
            pass   # Pencere kapanırken gelen son çizim isteğini sessizce yok say
 
    def _oge_ciz(self, oge) -> None:
        """Tek bir çizim komutunu (çokgen veya çizgi) canvas'a koyar."""
        duz = [koordinat for nokta in oge.noktalar for koordinat in nokta]
        if isinstance(oge, Cokgen):
            self.canvas.create_polygon(
                duz, fill=oge.dolgu or "", outline=oge.cizgi or "",
                width=max(1.0, oge.kalinlik) if oge.cizgi else 1)
        else:
            self.canvas.create_line(
                duz, fill=oge.renk, width=max(1.0, oge.kalinlik),
                capstyle="round", joinstyle="round", dash=oge.kesik)
 
 
# ----------------------------------------------------------------------------
# 2) MOTOR ÇUBUKLARI
# ----------------------------------------------------------------------------
 
class KediSimulatoru:
    """Kedinin beş eklemini kaydırma çubuklarıyla gösteren bölüm."""
 
    def __init__(self, pencere: tk.Tk, kap: Optional[tk.Misc] = None):
        """Pencereyi saklar, başlığını koyar ve çubukları 'kap' içinde (verilmezse pencerede) oluşturur."""
        self.pencere = pencere
        self.pencere.title("Kedi Simülatörü")
        self._kap = kap if kap is not None else pencere
        # Çubuklara adlarıyla ulaşabilmek için bir sözlükte tutuyoruz: {"head_pan": <Scale>, ...}
        self.cubuklar: Dict[str, tk.Scale] = {}
        self._cubuklari_olustur()
 
    def _cubuklari_olustur(self) -> None:
        """EKLEMLER tablosundaki her eklem için bir kaydırma çubuğu oluşturup yerleştirir."""
        for ad, (en_az, en_cok) in EKLEMLER.items():
            # Adım küçük tutulur ki animasyon basamak basamak değil, akıcı görünsün.
            # (Gerçek servolar tam sayı derece kullanır; bunu ileride HAL halledecek.)
            adim = 0.01 if en_cok <= 1 else 0.1
            cubuk = tk.Scale(self._kap, from_=en_az, to=en_cok, resolution=adim,
                             orient="horizontal", length=320, label=ad)
            cubuk.set(0)  # Hepsi başlangıçta 0'da dursun
            cubuk.pack(padx=12, pady=4)
            self.cubuklar[ad] = cubuk
 
    def deger_al(self, ad: str) -> float:
        """Bir eklemin çubuğunun o anki değerini döndürür. Eklem adı yanlışsa anlaşılır hata verir."""
        if ad not in self.cubuklar:
            raise KeyError(f"Bilinmeyen eklem: '{ad}'. Geçerli eklemler: {list(EKLEMLER)}")
        return self.cubuklar[ad].get()
 
    def tum_degerler(self) -> Dict[str, float]:
        """Beş eklemin o anki değerlerini sözlük olarak döndürür."""
        return {ad: cubuk.get() for ad, cubuk in self.cubuklar.items()}
 
    def deger_ata(self, ad: str, deger: float) -> None:
        """Bir eklemin çubuğunu verilen değere getirir. Sınır dışı değer, aralığın ucuna kırpılır."""
        if ad not in self.cubuklar:
            raise KeyError(f"Bilinmeyen eklem: '{ad}'. Geçerli eklemler: {list(EKLEMLER)}")
        en_az, en_cok = EKLEMLER[ad]
        self.cubuklar[ad].set(min(max(deger, en_az), en_cok))
 
    def poz_uygula(self, poz: Dict[str, float]) -> None:
        """Bir pozdaki (sözlük) eklemlerin hepsini çubuklara uygular. Bilinmeyen anahtarlar yok sayılır."""
        for ad, deger in poz.items():
            if ad in self.cubuklar:
                self.deger_ata(ad, deger)
 
 
# ----------------------------------------------------------------------------
# 3) KLİP OYNATICI (çubuklar + yüz birlikte)
# ----------------------------------------------------------------------------
 
class KlipOynatici:
    """Bir klibi, zamana bakarak saniyede ~50 kare ile oynatır: hem çubukları hem yüzü.
 
    time.sleep() KULLANMAZ: Tkinter'in after() komutu "şu kadar ms sonra şunu çalıştır" der,
    beklerken pencere canlı kalır (kaydırma çubukları, düğmeler çalışmaya devam eder).
    """
 
    KARE_ARALIGI_MS = 20      # Her 20 ms'de bir güncelle = saniyede 50 kare
    GECIS_MS = 300            # Klip başlarken mevcut pozdan/yüzden klibin ilk karesine yumuşak geçiş süresi
    DONGU_BEKLEME_MS = 400    # Döngülü klipte, son karede bekleme (Yüz Atölyesi'ndeki gibi)
 
    def __init__(self, simulator: KediSimulatoru, yuz_ekrani: Optional[YuzEkrani] = None):
        """Oynatıcıyı çubuklara ve (varsa) yüz ekranına bağlar. Başlangıçta hiçbir klip oynamaz."""
        self._sim = simulator
        self._yuz_ekrani = yuz_ekrani
        self._klip: Optional[Klip] = None
        self._dongu = False
        self._bitti_geri_cagri: Optional[Callable[[], None]] = None
        self._after_id: Optional[str] = None
        self._baslangic_zamani = 0.0
        self._baslangic_poz: Dict[str, float] = {}
        self._baslangic_yuz: Dict = dict(YUZ_VARSAYILAN)
        self._gecis_ms = self.GECIS_MS   # Şu an oynayan klibin giriş geçişi süresi
        self._son_yuz: Dict = dict(YUZ_VARSAYILAN)   # Ekranda en son gösterilen yüz
 
    @property
    def calisiyor(self) -> bool:
        """Şu anda bir klip oynuyor mu?"""
        return self._klip is not None
 
    def oynat(self, klip: Klip, dongu: Optional[bool] = None,
              bitti: Optional[Callable[[], None]] = None,
              gecis_ms: Optional[float] = None) -> None:
        """Klibi baştan oynatır. Önceki klip varsa kesilir. 'bitti' klip bitince çağrılır.
 
        gecis_ms: Klibe girerken yumuşak geçişin süresi (verilmezse GECIS_MS = 300 ms).
        """
        self.durdur()
        self._gecis_ms = self.GECIS_MS if gecis_ms is None else gecis_ms
        self._klip = klip
        self._dongu = klip.dongu if dongu is None else dongu
        self._bitti_geri_cagri = bitti
        self._baslangic_zamani = time.monotonic()
        # Şu anki poz ve yüz: yumuşak geçişin başlangıç noktası (ani sıçrama olmasın diye)
        self._baslangic_poz = self._sim.tum_degerler()
        self._baslangic_yuz = dict(self._son_yuz)
        self._kare()
 
    def durdur(self) -> None:
        """Oynatmayı durdurur; çubuklar ve yüz bulundukları yerde kalır."""
        if self._after_id is not None:
            try:
                self._sim.pencere.after_cancel(self._after_id)
            except tk.TclError:
                pass   # Pencere zaten kapanmış olabilir
            self._after_id = None
        self._klip = None
 
    def durus_goster(self, poz: Dict[str, float], yuz: Dict) -> None:
        """Animasyon oynatmadan, kediyi doğrudan verilen poz ve yüzde gösterir (sabit duruş)."""
        self.durdur()
        self._uygula(poz, yuz)
 
    def _uygula(self, poz: Dict[str, float], yuz: Dict) -> None:
        """Hesaplanan poz ve yüzü ekrana uygular: çubuklar kayar, yüz yeniden çizilir."""
        self._sim.poz_uygula(poz)
        self._son_yuz = yuz
        if self._yuz_ekrani is not None:
            # Yüz çizimi kulak ve baş dönüşü için motor değerlerine de ihtiyaç duyar
            self._yuz_ekrani.ciz({**yuz, **poz})
 
    def _kare(self) -> None:
        """Bir animasyon karesi çizer, sonra 20 ms sonrası için kendini tekrar planlar."""
        self._after_id = None
        if self._klip is None:
            return
        try:
            gecen_ms = (time.monotonic() - self._baslangic_zamani) * 1000.0
            klip = self._klip
 
            if gecen_ms < self._gecis_ms:
                # 1) Giriş geçişi: mevcut poz ve yüzden klibin ilk karesine yumuşakça git
                k = Enterpolator._yumusak(gecen_ms / self._gecis_ms)
                hedef_poz = Enterpolator.ornekle(klip, 0.0)
                poz = {ad: self._baslangic_poz.get(ad, 0.0)
                       + (hedef_poz[ad] - self._baslangic_poz.get(ad, 0.0)) * k for ad in hedef_poz}
                yuz = Enterpolator.yuz_karistir(self._baslangic_yuz, Enterpolator.yuz_ornekle(klip, 0.0), k)
            else:
                # 2) Klip zamanı: giriş geçişi bittikten sonra geçen süre
                t_ms = gecen_ms - self._gecis_ms
                if self._dongu:
                    t_ms = t_ms % (klip.sure_ms + self.DONGU_BEKLEME_MS)
                elif t_ms > klip.sure_ms:
                    self._uygula(Enterpolator.ornekle(klip, klip.sure_ms),
                                 Enterpolator.yuz_ornekle(klip, klip.sure_ms))
                    self._bitir()
                    return
                poz = Enterpolator.ornekle(klip, t_ms)
                yuz = Enterpolator.yuz_ornekle(klip, t_ms)
 
            self._uygula(poz, yuz)
            self._after_id = self._sim.pencere.after(self.KARE_ARALIGI_MS, self._kare)
        except Exception:
            # Bir karedeki beklenmeyen hata animasyon döngüsünü sessizce öldürmesin.
            logger.exception("Klip oynatılırken hata oluştu; oynatma durduruldu.")
            self._bitir()
 
    def _bitir(self) -> None:
        """Klip bitince durumu temizler ve varsa 'bitti' geri çağrısını çalıştırır."""
        geri_cagri = self._bitti_geri_cagri
        self.durdur()
        self._bitti_geri_cagri = None
        if geri_cagri is not None:
            geri_cagri()
 
 
# ----------------------------------------------------------------------------
# 4) KONTROLCÜ (dışarıdan tek giriş noktası)
# ----------------------------------------------------------------------------
 
class KediKontrolcusu:
    """Dışarıdan (ileride Kaan'ın router'ından) kullanılacak tek giriş noktası.
 
    Kedi açılışta DÜZ durur (animasyon yok). Bir duygu çağrılınca o duygunun klibi oynar:
        kontrolcu.duygu_cagir("happy")   # çubuklar da yüz de mutlu klibi oynar
    """
 
    # Duygu klibi bitince kedi ne yapsın? (Bu tek satırı değiştirerek davranışı seçebilirsin)
    #   "notr": yumuşakça düz pozuna dönüp durur  (varsayılan)
    #   "dur" : klibin son karesinde kalır
    #   "idle": bekleme (idle) animasyonuna geçer, döngüde oynar
    BITINCE_DAVRANIS = "notr"
    NOTR_GECIS_MS = 600            # Düz pozuna dönüş süresi
    VARSAYILAN_DUYGU = "idle"
 
    def __init__(self, simulator: KediSimulatoru, yuz_ekrani: Optional[YuzEkrani], klipler: Dict[str, Klip]):
        """Klipleri saklar, oynatıcıyı kurar ve kediyi düz pozda gösterir."""
        self.klipler = klipler
        self.oynatici = KlipOynatici(simulator, yuz_ekrani)
        self._notr_klip = self._notr_klip_olustur()
        self.notr_goster()
 
    def _notr_klip_olustur(self) -> Klip:
        """Düz duruşu tek karelik bir klip olarak hazırlar.
 
        Düz duruş = idle klibinin ilk karesi (Tuğra'nın tasarladığı 'normal' yüz). idle klibi yoksa
        yüz varsayılanları ve sıfır pozu kullanılır. Tek karelik klip olması sayesinde, düz pozuna
        dönüş de diğer animasyonlar gibi yumuşak geçişle yapılır.
        """
        idle = self.klip_bul(self.VARSAYILAN_DUYGU)
        if idle is not None:
            ilk = idle.kareler[0]
            poz, yuz = dict(ilk.poz), dict(ilk.yuz)
        else:
            poz = {ad: 0.0 for ad in EKLEMLER}
            poz["ear_left"] = poz["ear_right"] = 1.0
            yuz = dict(YUZ_VARSAYILAN)
        kare = Kare(t_ms=0.0, gecis="smooth", poz=poz, yuz=yuz)
        return Klip(ad="notr", duygu="notr", dongu=False, kareler=(kare,))
 
    def klip_bul(self, duygu: str) -> Optional[Klip]:
        """Duygu adına karşılık gelen klibi bulur.
 
        Önce dosya adına bakar ("happy" -> happy.json), yoksa klibin içindeki 'emotion' alanı
        eşleşen ilk klibi alır. Hiçbiri yoksa None döner.
        """
        if duygu in self.klipler:
            return self.klipler[duygu]
        for ad in sorted(self.klipler):
            if self.klipler[ad].duygu == duygu:
                return self.klipler[ad]
        return None
 
    def notr_goster(self) -> None:
        """Kediyi animasyonsuz, doğrudan düz pozda gösterir (açılışta ve 'baslat' çağrısında)."""
        kare = self._notr_klip.kareler[0]
        self.oynatici.durus_goster(kare.poz, kare.yuz)
 
    def notr_don(self) -> None:
        """Kediyi mevcut pozundan yumuşakça düz pozuna götürür ve orada durdurur."""
        self.oynatici.oynat(self._notr_klip, gecis_ms=self.NOTR_GECIS_MS)
 
    def _bitince_ne_yapilacak(self, klip: Klip) -> Optional[Callable[[], None]]:
        """BITINCE_DAVRANIS ayarına göre, klip bitince çalışacak fonksiyonu seçer (yoksa None)."""
        if klip.dongu:
            return None   # Döngülü klip zaten bitmez
        if self.BITINCE_DAVRANIS == "notr":
            return self.notr_don
        if self.BITINCE_DAVRANIS == "idle":
            idle = self.klip_bul(self.VARSAYILAN_DUYGU)
            if idle is not None and klip is not idle:
                return self._idle_baslat
        return None
 
    def duygu_cagir(self, duygu: str) -> bool:
        """Verilen duyguyu oynatır (çubuklar ve yüz birlikte). Çalıştırabildiyse True döndürür.
 
        Klibi olmayan bir duygu gelirse sistem durmaz: kedi düz pozuna döner ve False döner
        (sözleşmedeki 'hata kuralı': bilinmeyen duygu sistemi asla çökertmez).
        """
        klip = self.klip_bul(duygu)
        if klip is None:
            logger.warning("'%s' duygusu için klip yok; kedi düz pozuna dönüyor.", duygu)
            self.notr_don()
            return False
        self.oynatici.oynat(klip, bitti=self._bitince_ne_yapilacak(klip))
        return True
 
    def klip_oynat(self, ad: str, dongu: Optional[bool] = None,
                   bitti: Optional[Callable[[], None]] = None) -> bool:
        """Dosya adıyla verilen klibi oynatır (listeden seçim için). Bulunamazsa False döner."""
        klip = self.klipler.get(ad)
        if klip is None:
            logger.warning("'%s' adlı klip bulunamadı.", ad)
            return False
        self.oynatici.oynat(klip, dongu=dongu, bitti=bitti)
        return True
 
    def _idle_baslat(self) -> None:
        """Bekleme (idle) klibini döngüde oynatır."""
        idle = self.klip_bul(self.VARSAYILAN_DUYGU)
        if idle is not None:
            self.oynatici.oynat(idle, dongu=True)
 
    def baslat(self) -> None:
        """Program açılınca kediyi düz pozda bırakır (animasyon yok, bir duygu çağrılmasını bekler)."""
        self.notr_goster()
 
    def durdur(self) -> None:
        """Oynatmayı durdurur."""
        self.oynatici.durdur()
 
 
# ----------------------------------------------------------------------------
# 5) KONTROL PANELİ
# ----------------------------------------------------------------------------
 
class KlipPaneli:
    """Duygu butonları + istenen klibi seçip oynatma kontrolleri (Oynat, Durdur, Döngü)."""
 
    def __init__(self, ust: tk.Misc, kontrolcu: KediKontrolcusu):
        """Paneli oluşturur. Duygu butonları sadece klibi bulunan duygular için çıkar."""
        self._kontrolcu = kontrolcu
 
        cerceve = ttk.Frame(ust)
        cerceve.pack(padx=12, pady=8, fill="x")
 
        # --- Duygu butonları: kontrolcu.duygu_cagir(...) çağırır ---
        ttk.Label(cerceve, text="Duygu çağır:").grid(row=0, column=0, columnspan=4, sticky="w")
        sutun = 0
        for duygu, etiket in DUYGU_ETIKETLERI.items():
            if kontrolcu.klip_bul(duygu) is None:
                continue
            ttk.Button(cerceve, text=etiket, command=lambda d=duygu: self._duygu_cagir(d)
                       ).grid(row=1 + sutun // 4, column=sutun % 4, padx=2, pady=2, sticky="we")
            sutun += 1
        # Kediyi istenen anda düz pozuna döndüren düğme
        ttk.Button(cerceve, text="Düz dur", command=self._notr_don
                   ).grid(row=1 + sutun // 4, column=sutun % 4, padx=2, pady=2, sticky="we")
        sutun += 1
 
        # --- Klip seçici ---
        satir = 1 + (sutun + 3) // 4 + 1
        ttk.Label(cerceve, text="Klip seç:").grid(row=satir, column=0, columnspan=4, sticky="w", pady=(10, 0))
        self._secim = tk.StringVar()
        self._kutu = ttk.Combobox(cerceve, textvariable=self._secim, state="readonly",
                                  values=list(kontrolcu.klipler), width=26)
        self._kutu.grid(row=satir + 1, column=0, columnspan=4, sticky="we", pady=(0, 4))
        self._kutu.bind("<<ComboboxSelected>>", self._secim_degisti)
 
        self._dongu = tk.BooleanVar(value=False)
        ttk.Button(cerceve, text="▶ Oynat", command=self._oynat).grid(row=satir + 2, column=0, columnspan=2, sticky="we")
        ttk.Button(cerceve, text="■ Durdur", command=self._durdur).grid(row=satir + 2, column=2, sticky="we")
        ttk.Checkbutton(cerceve, text="Döngü", variable=self._dongu).grid(row=satir + 2, column=3)
 
        self._durum = ttk.Label(cerceve, text="")
        self._durum.grid(row=satir + 3, column=0, columnspan=4, sticky="w", pady=(6, 0))
 
        if kontrolcu.klipler:
            self._kutu.current(0)
            self._secim_degisti()
        else:
            self._durum.config(text=f"Klip bulunamadı. JSON dosyalarını şuraya koy: {KLIP_KLASORU}")
 
    def _duygu_cagir(self, duygu: str) -> None:
        """Duygu butonu: duyguyu çağırır (çubuklar ve yüz birlikte oynar)."""
        self._kontrolcu.duygu_cagir(duygu)
        self._durum.config(text=f"Duygu çağrıldı: {DUYGU_ETIKETLERI.get(duygu, duygu)}")
 
    def _notr_don(self) -> None:
        """Düz dur düğmesi: kediyi düz pozuna götürür."""
        self._kontrolcu.notr_don()
        self._durum.config(text="Düz duruyor.")
 
    def _secili_klip(self) -> Optional[Klip]:
        """Listede seçili olan klibi döndürür; seçim yoksa None."""
        return self._kontrolcu.klipler.get(self._secim.get())
 
    def _secim_degisti(self, _olay=None) -> None:
        """Yeni klip seçilince Döngü kutusunu klibin kendi ayarına getirir ve bilgi satırını günceller."""
        klip = self._secili_klip()
        if klip is None:
            return
        self._dongu.set(klip.dongu)
        self._durum.config(text=f"{klip.duygu} · {len(klip.kareler)} kare · {klip.sure_ms / 1000:.1f} sn")
 
    def _oynat(self) -> None:
        """Oynat düğmesi: seçili klibi çalar."""
        if self._secili_klip() is None:
            self._durum.config(text="Önce listeden bir klip seç.")
            return
        self._kontrolcu.klip_oynat(self._secim.get(), dongu=self._dongu.get(), bitti=self._bitti)
        self._durum.config(text=f"Oynuyor: {self._secim.get()}")
 
    def _durdur(self) -> None:
        """Durdur düğmesi: oynatmayı keser."""
        self._kontrolcu.durdur()
        self._durum.config(text="Durduruldu.")
 
    def _bitti(self) -> None:
        """Klip kendiliğinden bitince durum satırını günceller."""
        self._durum.config(text="Bitti.")
 
 
# ----------------------------------------------------------------------------
# 6) GİRİŞ NOKTASI
# ----------------------------------------------------------------------------
 
def main() -> None:
    """Klipleri yükler, pencereyi kurar, kediyi canlandırır ve kullanıcı kapatana kadar çalışır."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    klipler = KlipYukleyici.klasorden_yukle(KLIP_KLASORU)
    try:
        kok = tk.Tk()
    except tk.TclError as hata:
        # Ekran/pencere sistemi yoksa (örneğin sunucuda) program çökmek yerine açıklama yapar.
        print(f"Pencere açılamadı: {hata}")
        return
 
    sol = ttk.Frame(kok)   # Yüz ekranı + duygu butonları
    sol.grid(row=0, column=0, padx=8, pady=8, sticky="n")
    sag = ttk.Frame(kok)   # Motor çubukları
    sag.grid(row=0, column=1, padx=8, pady=8, sticky="n")
 
    yuz_ekrani = YuzEkrani(sol)
    simulator = KediSimulatoru(kok, kap=sag)
    kontrolcu = KediKontrolcusu(simulator, yuz_ekrani, klipler)
    KlipPaneli(sol, kontrolcu)
    kontrolcu.baslat()   # Kedi düz dursun; bir duygu butonuna basılınca animasyon oynar
 
    def kapat() -> None:
        """Pencere kapanırken önce animasyonu durdurur (kapanmış pencereye çizmeye çalışmasın)."""
        kontrolcu.durdur()
        kok.destroy()
 
    kok.protocol("WM_DELETE_WINDOW", kapat)
    kok.mainloop()  # Pencere kapatılana kadar burada bekler
 
 
if __name__ == "__main__":
    main()