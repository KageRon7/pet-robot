#include <Arduino.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include "animasyon_tanimlari.h" // Anahtar, Yuz, Poz yapıları
#include "gomulu_klipler.h"      // Derleme sırasında gömülen JSON klipler

// 1 yapılırsa seri monitöre fps yazar. Gerçek bağlantıda 0 kalmalı,
// aksi halde seri porttaki JSON haberleşmesi bozulur.
#define FPS_YAZ 0

const uint32_t SPI_HIZ = 40000000; // Ekran SPI hızı (40 MHz)

// ---------------- Güvenlik ve iletişim ----------------
unsigned long sonMesajZamani = 0; // Son geçerli komutun geldiği an
bool sigortaDevredeMi = false;    // true: komut alındı, zaman aşımı izleniyor
String gelenSatir = "";           // Seri porttan biriken ham mesaj

// ---------------- Servo ve hareket ----------------
const int NUM_SERVOS = 5;
const int pins[NUM_SERVOS] = {13, 12, 14, 27, 26};

// Servo başına fiziksel açı sınırları (derece)
const int minAci[NUM_SERVOS] = {45, 0, 80, 60, 30};
const int maxAci[NUM_SERVOS] = {135, 180, 135, 150, 120};

// Nötr (başlangıç) açıları
const int idleAci[NUM_SERVOS] = {90, 90, 90, 132, 48};

const unsigned long IDLE_RETURN_MS = 800; // Nötre dönüş süresi
const unsigned long UPDATE_INTERVAL = 10; // Servo güncelleme periyodu
const unsigned long GECIS_MS = 250;       // Klipler arası yumuşak geçiş süresi

// ---------------- Nefes ve göz kırpma ayarları ----------------
const float NORMAL_BPM = 14;             // Normal nefes hızı (dk başına)
const float UYKU_BPM = 8;                // Uyku sırasındaki nefes hızı
const float NEFES_SERVO_DERECE = 1.5;    // Nefesle baş eğiminin genliği (derece)
const int NEFES_PIKSEL = 3;              // Nefesle yüzün genliği (piksel)
const unsigned long KIRPMA_MS = 180;     // Tek göz kırpma süresi
const unsigned long KIRPMA_MIN = 2000;   // İki kırpma arası en az süre
const unsigned long KIRPMA_MAX = 6000;   // İki kırpma arası en fazla süre
const unsigned long UYKU_SURE_MS = 3000; // Mesaj gelmezse uykuya dalma süresi

float nefesBpm = NORMAL_BPM; // Anlık nefes hızı (hedefe yavaşça yaklaşır)
float nefesFaz = 0;          // Sinüs fazı (0 - 2π)
float nefesDeger = 0;        // Nefes çıktısı, -1 ile +1 arası
int nefesPx = 0;             // Nefesin piksel karşılığı
float klipBpm = 0;           // Klipte breath_bpm tanımlıysa değeri
unsigned long sonNefesZamani = 0;
unsigned long sonNefesServo = 0;
bool kirpiyor = false;
float kirpmaDeger = 0; // 0 = göz açık, 1 = göz tam kapalı
unsigned long kirpmaBaslangic = 0;
unsigned long sonrakiKirpma = 0;
int sleepyKlipNo = -1; // "sleepy" klibinin indeksi
int aktifKlipNo = -1;  // Çalan klibin indeksi

Servo servos[NUM_SERVOS];
float startVal[NUM_SERVOS];   // Hareket başlangıç açıları
float targetVal[NUM_SERVOS];  // Hareket hedef açıları
float currentVal[NUM_SERVOS]; // Servoların anlık açıları

unsigned long moveStart = 0;
unsigned long moveDuration = 0;
bool moving = false; // Doğrusal servo hareketi sürüyor mu
unsigned long lastUpdate = 0;

bool poseAnimasyonuAktif = false; // Servolar klipteki pose'a göre mi sürülüyor
unsigned long sonPoseGuncelleme = 0;

float gecisAcilar[NUM_SERVOS]; // Klip başlarken servoların o anki açıları
unsigned long gecisZamani = 0;

int sonUs[NUM_SERVOS]; // Son yazılan darbe genişliği (tekrar yazmayı önler)

// ---------------- Ekran ----------------
#define TFT_CS 5
#define TFT_DC 2
#define TFT_RST 4

Adafruit_ILI9341 tft(TFT_CS, TFT_DC, TFT_RST);

const int EKRAN_W = 320;
const int EKRAN_H = 240;

// Ekran BLOK_W x BLOK_H piksellik bloklara bölünür.
// Küçük blok = daha az gereksiz gönderim, ama blok başına daha fazla yük.
// Değerler ekran boyutunu tam bölmelidir.
const int BLOK_W = 40;
const int BLOK_H = 40;
static_assert(EKRAN_W % BLOK_W == 0, "BLOK_W ekran genisligini bolmeli");
static_assert(EKRAN_H % BLOK_H == 0, "BLOK_H ekran yuksekligini bolmeli");

const int BLOK_SUTUN = EKRAN_W / BLOK_W;
const int BLOK_SATIR = EKRAN_H / BLOK_H;
const int BLOK_TOPLAM = BLOK_SUTUN * BLOK_SATIR;

GFXcanvas16 canvas(BLOK_W, BLOK_H); // Tek blok için bellek tamponu
int blokNo = 0;                     // Sıradaki çizilecek blok
int blokX = 0;                      // Aktif bloğun ekrandaki sol üst X
int blokY = 0;                      // Aktif bloğun ekrandaki sol üst Y

// Her bloğun son gönderilen içeriğinin özeti (değişmeyeni göndermemek için)
uint32_t blokOzet[BLOK_TOPLAM];

// fps ölçüm sayaçları
unsigned long fpsSay = 0;
unsigned long blokGonderilen = 0;
unsigned long fpsZaman = 0;

uint16_t cZemin, cCizgi, cIris, cPembe, cGozyasi, cBeyaz, cKirmizi;

// ---------------- Klip ----------------
const int MAX_KEY = 64; // Bir klipteki en fazla anahtar kare
Anahtar keys[MAX_KEY];

int keySayisi = 0;
unsigned long klipSuresi = 1;
unsigned long klipBaslangic = 0;
unsigned long sonKareZamani = 0;

const unsigned long KARE_ARALIGI = 33; // ~30 fps

bool kareCiziliyor = false; // true: kare blok blok çiziliyor

int idleKlipNo = -1;
bool idleOynuyor = false; // Çalan klip döngüsel (idle/sleepy) mi

// ---------------- Yumuşak yüz durumu ----------------
const int AGIZ_SEKIL = 6; // Ağız şekli sayısı
const int AGIZ_N = 101;   // Ağız çizgisinin nokta sayısı

// Ara değer hesabı için tüm yüz parametreleri float olarak tutulur
struct YuzR
{
  float kapali; // Göz kapalılığı (0-1)
  float eye_open, eye_size, pupil, sparkle;
  float look_x, look_y;
  float brow_left, brow_right, brow_height;
  float mouth_open, tears;
  float blush, anger;
  float mw[AGIZ_SEKIL]; // Ağız şekillerinin ağırlıkları
};

YuzR kareR;  // Ekrana çizilen güncel yüz
YuzR gecisR; // Geçiş başındaki yüz
bool ilkYukleme = true;

float agizYv[AGIZ_N]; // Ağız eğrisinin her noktadaki yüksekliği
float agizHW = 0;     // Ağzın yarı genişliği

const float agizYari[AGIZ_SEKIL] = {40, 50, 50, 50, 50, 30}; // Şekil başına yarı genişlik

// =========================================================================
// Servo hareketi
// =========================================================================

// Açıyı sınırlayıp mikrosaniyeye çevirir ve servoya yazar
void servoYaz(int i, float aci)
{
  // Baş eğimi (servo 2) nefesle hafifçe oynar
  if (i == 2)
    aci += nefesDeger * NEFES_SERVO_DERECE;

  aci = constrain(aci, (float)minAci[i], (float)maxAci[i]);

  // 0-180 derece -> 500-2400 us
  int us = 500 + (int)(aci * (2400 - 500) / 180.0f);

  if (us == sonUs[i])
    return;

  sonUs[i] = us;
  servos[i].writeMicroseconds(us);
}

// Mevcut açılardan hedef açılara ms sürede doğrusal hareket başlatır
void hareketBaslat(const float target[], unsigned long ms)
{
  for (int i = 0; i < NUM_SERVOS; i++)
  {
    startVal[i] = currentVal[i];
    targetVal[i] = target[i];
  }

  moveStart = millis();
  moveDuration = ms;
  moving = true;
}

// Zamanlayıcıları ayırır, servoları bağlar ve nötr konuma getirir
void motorlariBaslat()
{
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    servos[i].attach(pins[i], 500, 2400);

    currentVal[i] = idleAci[i];
    startVal[i] = idleAci[i];
    targetVal[i] = idleAci[i];

    servoYaz(i, idleAci[i]);
  }
}

// hareketBaslat ile başlayan hareketi zamana göre ilerletir
void servoGuncelle()
{
  if (!moving)
    return;

  unsigned long now = millis();

  if (now - lastUpdate < UPDATE_INTERVAL)
    return;

  lastUpdate = now;

  // t: hareketin ilerleme oranı (0-1)
  float t = (moveDuration == 0)
                ? 1.0f
                : (float)(now - moveStart) / moveDuration;

  if (t >= 1.0f)
  {
    t = 1.0f;
    moving = false;
  }

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    currentVal[i] = startVal[i] +
                    (targetVal[i] - startVal[i]) * t;

    servoYaz(i, currentVal[i]);
  }
}

// =========================================================================
// Nefes ve göz kırpma katmanı
// Seri porttan bağımsız, yalnızca millis() ile çalışır ve her durumda aktiftir.
// =========================================================================

void nefesGuncelle()
{
  unsigned long now = millis();

  // Geçen süre (sn); uzun duraksamalarda sıçrama olmasın diye sınırlı
  float dt = (now - sonNefesZamani) / 1000.0f;
  sonNefesZamani = now;
  if (dt > 0.1f)
    dt = 0.1f;

  // Hedef hız: klipte breath_bpm varsa o, uykudaysa UYKU_BPM, yoksa normal
  float hedef = NORMAL_BPM;
  if (klipBpm > 0)
    hedef = klipBpm;
  else if (aktifKlipNo == sleepyKlipNo)
    hedef = UYKU_BPM;

  // Hız hedefe yavaşça yaklaşır
  nefesBpm += (hedef - nefesBpm) * min(1.0f, dt * 1.5f);

  // Faz ilerletilir (2π = 6.2832), çıktı sinüs dalgasıdır
  nefesFaz += 6.2832f * (nefesBpm / 60.0f) * dt;
  if (nefesFaz > 6.2832f)
    nefesFaz -= 6.2832f;

  nefesDeger = sinf(nefesFaz);

  // Kırpma zamanı geldiyse göz kırpmayı başlat
  if (!kirpiyor && now >= sonrakiKirpma)
  {
    kirpiyor = true;
    kirpmaBaslangic = now;
  }

  if (kirpiyor)
  {
    unsigned long g = now - kirpmaBaslangic;

    if (g >= KIRPMA_MS)
    {
      // Kırpma bitti, sonraki kırpmayı rastgele bir süreye ayarla
      kirpiyor = false;
      kirpmaDeger = 0;
      sonrakiKirpma = now + random((long)KIRPMA_MIN, (long)KIRPMA_MAX + 1);
    }
    else
    {
      // Üçgen dalga: ilk yarıda kapanır, ikinci yarıda açılır
      float u = (float)g / KIRPMA_MS;
      kirpmaDeger = (u < 0.5f) ? u * 2 : (1 - u) * 2;
    }
  }

  // Servo hareketsizken de baş nefes alsın (20 ms'de bir yazılır)
  if (now - sonNefesServo >= 20)
  {
    sonNefesServo = now;
    servoYaz(2, currentVal[2]);
  }
}

// Açıları sınırlara kırpıp ms sürede hedefe gider
void hedefAcilaraGit(int hedefAcilar[5], int sure_ms)
{
  float target[NUM_SERVOS];

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    target[i] = constrain(
        hedefAcilar[i],
        minAci[i],
        maxAci[i]);
  }

  hareketBaslat(target, sure_ms);
}

// Tüm servoları nötr açılara döndürür
void notrPozisyonaDon()
{
  float target[NUM_SERVOS];

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    target[i] = idleAci[i];
  }

  hareketBaslat(target, IDLE_RETURN_MS);
}

// =========================================================================
// Çizim yardımcıları
// Koordinatlar ekran koordinatıdır; aktif bloğun sol üstü (blokX, blokY)
// çıkarılarak tampona çizilir. Bloğun dışında kalan şekiller hiç çizilmez,
// böylece aynı yüz her blok için tekrar çizilse de maliyet düşük kalır.
// =========================================================================

// Sınır kutusu aktif bloğun tamamen dışındaysa true döner (x1, y1 dahil)
inline bool blokDisinda(int x0, int y0, int x1, int y1)
{
  return x1 < blokX || x0 >= blokX + BLOK_W ||
         y1 < blokY || y0 >= blokY + BLOK_H;
}

void daireCiz(int x, int y, int r, uint16_t renk)
{
  if (blokDisinda(x - r, y - r, x + r, y + r))
    return;

  canvas.fillCircle(x - blokX, y - blokY, r, renk);
}

void cizgiCiz(int x0, int y0, int x1, int y1, uint16_t renk)
{
  if (blokDisinda(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))
    return;

  canvas.drawLine(x0 - blokX, y0 - blokY, x1 - blokX, y1 - blokY, renk);
}

void kutuCiz(int x, int y, int w, int h, uint16_t renk)
{
  if (blokDisinda(x, y, x + w - 1, y + h - 1))
    return;

  canvas.fillRect(x - blokX, y - blokY, w, h, renk);
}

void yuvarlakKutuCiz(int x, int y, int w, int h, int r, uint16_t renk)
{
  if (blokDisinda(x, y, x + w - 1, y + h - 1))
    return;

  canvas.fillRoundRect(x - blokX, y - blokY, w, h, r, renk);
}

void yatayCiz(int x, int y, int w, uint16_t renk)
{
  if (blokDisinda(x, y, x + w - 1, y))
    return;

  canvas.drawFastHLine(x - blokX, y - blokY, w, renk);
}

void dikeyCiz(int x, int y, int h, uint16_t renk)
{
  if (blokDisinda(x, y, x, y + h - 1))
    return;

  canvas.drawFastVLine(x - blokX, y - blokY, h, renk);
}

// İki RGB565 rengi t oranında karıştırır (0 = a, 1 = b)
uint16_t karistir(uint16_t a, uint16_t b, float t)
{
  t = constrain(t, 0.0f, 1.0f);

  // RGB565 kanallarını ayır (5-6-5 bit)
  int ar = (a >> 11) & 31;
  int ag = (a >> 5) & 63;
  int ab = a & 31;

  int br = (b >> 11) & 31;
  int bg = (b >> 5) & 63;
  int bb = b & 31;

  int r = ar + (int)((br - ar) * t);
  int g = ag + (int)((bg - ag) * t);
  int bl = ab + (int)((bb - ab) * t);

  return (r << 11) | (g << 5) | bl;
}

// JSON'daki ağız adını şekil numarasına çevirir (bilinmeyen = 0, düz)
int agizNo(const char *s)
{
  if (strcmp(s, "smile") == 0)
    return 1;

  if (strcmp(s, "frown") == 0)
    return 2;

  if (strcmp(s, "wavy") == 0)
    return 3;

  if (strcmp(s, "zigzag") == 0)
    return 4;

  if (strcmp(s, "y") == 0)
    return 5;

  return 0;
}

// JSON'daki ease adını numaraya çevirir (bilinmeyen = 0, smooth)
int easeNo(const char *s)
{
  if (strcmp(s, "stop") == 0)
    return 1;

  if (strcmp(s, "bounce") == 0)
    return 2;

  if (strcmp(s, "linear") == 0)
    return 3;

  if (strcmp(s, "snap") == 0)
    return 4;

  return 0;
}

// =========================================================================
// JSON klip yükleme
// =========================================================================

// JSON metnini ayrıştırıp keys[] dizisine doldurur; başarısızsa false döner
bool klipYukle(const char *json)
{
  JsonDocument doc;

  DeserializationError err = deserializeJson(doc, json);

  if (err)
    return false;

  int n = 0;

  klipBpm = 0;

  JsonArray ks = doc["keys"].as<JsonArray>();

  for (JsonObject k : ks)
  {
    if (n >= MAX_KEY)
      break;

    Anahtar &a = keys[n];

    a.t = k["t_ms"] | 0;
    a.ease = easeNo(k["ease"] | "smooth");

    JsonObject f = k["face"];

    // Nefes hızı yalnızca ilk anahtardan okunur
    if (n == 0)
      klipBpm = f["breath_bpm"] | 0.0f;

    Yuz &y = a.yuz;

    y.gozKapali =
        strcmp(f["eye_shape"] | "round", "closed") == 0;

    y.eye_open = f["eye_open"] | 0.9f;
    y.eye_size = f["eye_size"] | 1.0f;
    y.pupil = f["pupil"] | 0.9f;
    y.sparkle = f["sparkle"] | 0.8f;

    y.look_x = f["look_x"] | 0.0f;
    y.look_y = f["look_y"] | 0.0f;

    y.brow_left = f["brow_left"] | 0.0f;
    y.brow_right = f["brow_right"] | 0.0f;
    y.brow_height = f["brow_height"] | 0.0f;

    y.mouth = agizNo(f["mouth"] | "flat");

    y.mouth_open = f["mouth_open"] | 0.0f;
    y.tears = f["tears"] | 0.0f;

    y.blush = f["blush"] | false;
    y.anger_mark = f["anger_mark"] | false;

    JsonObject p = k["pose"].as<JsonObject>();

    a.poseVar = !p.isNull(); // Bu anahtarda pose tanımlı mı

    a.pose.body_yaw = p["body_yaw"] | 0.0f;
    a.pose.head_pan = p["head_pan"] | 0.0f;
    a.pose.head_tilt = p["head_tilt"] | 0.0f;

    a.pose.ear_left = p["ear_left"] | 1.0f;
    a.pose.ear_right = p["ear_right"] | 1.0f;

    n++;
  }

  if (n == 0)
    return false;

  keySayisi = n;

  // Klip süresi: duration_ms ile son anahtar zamanından büyük olan
  unsigned long sure = doc["duration_ms"] | 0;

  klipSuresi =
      (sure > keys[n - 1].t)
          ? sure
          : keys[n - 1].t;

  if (klipSuresi == 0)
    klipSuresi = 1;

  return true;
}

// =========================================================================
// Ara değer (interpolasyon) hesapları
// =========================================================================

// a'dan b'ye doğrusal ara değer (u: 0-1)
float ara(float a, float b, float u)
{
  return a + (b - a) * u;
}

// u (0-1) değerine ease eğrisini uygular
float easeUygula(int e, float u)
{
  // stop: başta hızlı, sonda yavaşlar
  if (e == 1)
    return 1 - (1 - u) * (1 - u);

  // bounce: hedefe çarpıp zıplar
  if (e == 2)
  {
    if (u < 0.3636f)
      return 7.5625f * u * u;

    if (u < 0.7273f)
    {
      u -= 0.5455f;
      return 7.5625f * u * u + 0.75f;
    }

    if (u < 0.9091f)
    {
      u -= 0.8182f;
      return 7.5625f * u * u + 0.9375f;
    }

    u -= 0.9545f;

    return 7.5625f * u * u + 0.984375f;
  }

  // linear
  if (e == 3)
    return u;

  // snap: anında hedefe atlar
  if (e == 4)
    return 1;

  // varsayılan: smoothstep
  return u * u * (3 - 2 * u);
}

// Yuz yapısını ara değer hesabına uygun YuzR'ye çevirir
YuzR yuzdenR(const Yuz &y)
{
  YuzR r;

  r.kapali = y.gozKapali ? 1.0f : 0.0f;

  r.eye_open = y.eye_open;
  r.eye_size = y.eye_size;
  r.pupil = y.pupil;
  r.sparkle = y.sparkle;

  r.look_x = y.look_x;
  r.look_y = y.look_y;

  r.brow_left = y.brow_left;
  r.brow_right = y.brow_right;
  r.brow_height = y.brow_height;

  r.mouth_open = y.mouth_open;
  r.tears = y.tears;

  r.blush = y.blush ? 1.0f : 0.0f;
  r.anger = y.anger_mark ? 1.0f : 0.0f;

  // Seçili ağız şeklinin ağırlığı 1, diğerleri 0
  for (int k = 0; k < AGIZ_SEKIL; k++)
    r.mw[k] = 0;

  int m = y.mouth;

  if (m < 0 || m >= AGIZ_SEKIL)
    m = 0;

  r.mw[m] = 1.0f;

  return r;
}

// İki yüz durumu arasında u oranında ara değer üretir
YuzR yuzRAra(const YuzR &a, const YuzR &b, float u)
{
  YuzR r;

  r.kapali = ara(a.kapali, b.kapali, u);

  r.eye_open = ara(a.eye_open, b.eye_open, u);
  r.eye_size = ara(a.eye_size, b.eye_size, u);
  r.pupil = ara(a.pupil, b.pupil, u);
  r.sparkle = ara(a.sparkle, b.sparkle, u);

  r.look_x = ara(a.look_x, b.look_x, u);
  r.look_y = ara(a.look_y, b.look_y, u);

  r.brow_left = ara(a.brow_left, b.brow_left, u);
  r.brow_right = ara(a.brow_right, b.brow_right, u);
  r.brow_height = ara(a.brow_height, b.brow_height, u);

  r.mouth_open = ara(a.mouth_open, b.mouth_open, u);
  r.tears = ara(a.tears, b.tears, u);

  r.blush = ara(a.blush, b.blush, u);
  r.anger = ara(a.anger, b.anger, u);

  for (int k = 0; k < AGIZ_SEKIL; k++)
    r.mw[k] = ara(a.mw[k], b.mw[k], u);

  return r;
}

// İki pose arasında u oranında ara değer üretir
Poz pozAra(const Poz &a, const Poz &b, float u)
{
  Poz r;

  r.body_yaw = ara(a.body_yaw, b.body_yaw, u);
  r.head_pan = ara(a.head_pan, b.head_pan, u);
  r.head_tilt = ara(a.head_tilt, b.head_tilt, u);

  r.ear_left = ara(a.ear_left, b.ear_left, u);
  r.ear_right = ara(a.ear_right, b.ear_right, u);

  return r;
}

// =========================================================================
// Ağız şekilleri
// =========================================================================

// Verilen şeklin x konumundaki yüksekliğini döner (x: merkezden piksel)
float agizYuksekligi(int sekil, float x, int derinlik)
{
  // smile: yukarı bakan parabol
  if (sekil == 1)
    return derinlik / 2.0f - (x * x) * derinlik / 2500.0f;

  // frown: aşağı bakan parabol
  if (sekil == 2)
    return -derinlik / 2.0f + (x * x) * derinlik / 2500.0f;

  // wavy: sinüs dalgası
  if (sekil == 3)
    return 8 * sinf(x * 0.15f);

  // zigzag: üçgen dalga
  if (sekil == 4)
  {
    float d = fmodf(x + 50, 20);
    return fabsf(d - 10) - 5;
  }

  // y: iki küçük parabol (kedi ağzı)
  if (sekil == 5)
  {
    float lx = (x < 0) ? x + 15 : x - 15;
    return 6 - (lx * lx * 12) / 225.0f;
  }

  // flat
  return 0;
}

// Şekil ağırlıklarına göre ağız eğrisini (agizYv) önceden hesaplar
void agizHazirla()
{
  // Yarı genişlik: şekillerin genişliklerinin ağırlıklı ortalaması
  float hw = 0;

  for (int k = 0; k < AGIZ_SEKIL; k++)
    hw += kareR.mw[k] * agizYari[k];

  agizHW = hw;

  // Ağız açıklığı arttıkça eğrinin derinliği artar
  int derinlik =
      10 + (int)(40 * constrain(kareR.mouth_open, 0.0f, 1.2f));

  for (int j = 0; j < AGIZ_N; j++)
  {
    // xn: -1 ile +1 arası normalize konum
    float xn = (j - AGIZ_N / 2) / (float)(AGIZ_N / 2);

    float y = 0;

    // Her şeklin yüksekliği ağırlığıyla toplanır
    for (int k = 0; k < AGIZ_SEKIL; k++)
    {
      if (kareR.mw[k] > 0.001f)
      {
        y += kareR.mw[k] *
             agizYuksekligi(k, xn * agizYari[k], derinlik);
      }
    }

    agizYv[j] = y;
  }
}

// =========================================================================
// Klipteki pose'a göre servo sürme
// =========================================================================

void servoPoseGuncelle()
{
  if (!poseAnimasyonuAktif || keySayisi == 0)
    return;

  unsigned long now = millis();

  if (now - sonPoseGuncelleme < UPDATE_INTERVAL)
    return;

  sonPoseGuncelleme = now;

  // Klip içindeki zaman; idle/sleepy klipleri döngüde çalar
  unsigned long t = now - klipBaslangic;

  if (idleOynuyor && klipSuresi > 0)
  {
    t %= klipSuresi;
  }

  Poz p;

  if (t <= keys[0].t)
  {
    p = keys[0].pose; // İlk anahtardan önce
  }
  else if (t >= keys[keySayisi - 1].t)
  {
    p = keys[keySayisi - 1].pose; // Son anahtardan sonra
  }
  else
  {
    // t'yi kapsayan anahtar çiftini bul
    int i = 0;

    while (i < keySayisi - 2 && keys[i + 1].t <= t)
    {
      i++;
    }

    unsigned long fark =
        keys[i + 1].t - keys[i].t;

    float u = (fark == 0)
                  ? 1.0f
                  : (float)(t - keys[i].t) / fark;

    u = easeUygula(keys[i + 1].ease, u);

    p = pozAra(
        keys[i].pose,
        keys[i + 1].pose,
        u);
  }

  // Pose değerlerini servo açılarına çevir
  float acilar[NUM_SERVOS];

  acilar[0] = 90.0f + p.body_yaw;
  acilar[1] = 90.0f + p.head_pan;
  acilar[2] = 90.0f + p.head_tilt;

  // Kulaklar: 0 = nötr, 1 = tam açık
  acilar[3] =
      idleAci[3] +
      p.ear_left * (maxAci[3] - idleAci[3]);

  acilar[4] =
      idleAci[4] -
      p.ear_right * (idleAci[4] - minAci[4]);

  // Klip başındaki yumuşak geçiş ağırlığı (0 = eski açı, 1 = yeni açı)
  float w = 1.0f;
  unsigned long g = now - gecisZamani;

  if (g < GECIS_MS)
  {
    w = (float)g / GECIS_MS;
    w = w * w * (3 - 2 * w);
  }

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    float a = constrain(
        acilar[i],
        (float)minAci[i],
        (float)maxAci[i]);

    if (w < 1.0f)
      a = gecisAcilar[i] + (a - gecisAcilar[i]) * w;

    currentVal[i] = a;

    servoYaz(i, a);
  }

  moving = false; // Pose animasyonu varken doğrusal hareket devre dışı
}

// =========================================================================
// Yüz çizimi
// =========================================================================

// Kaş çizer. aci: eğim (derece), icYon: +1 sol göz, -1 sağ göz
void kasCiz(int cx, int y, float aci, int icYon)
{
  float yar = 30; // Kaşın yarı uzunluğu

  float dy = sin(aci * 0.0174533f) * yar; // Derece -> radyan

  int icX = cx + icYon * (int)yar;
  int disX = cx - icYon * (int)yar;

  int icY = y - (int)dy;
  int disY = y + (int)dy;

  // 5 piksel kalınlık için kaydırılmış çizgiler
  for (int t = -2; t <= 2; t++)
  {
    cizgiCiz(
        disX,
        disY + t,
        icX,
        icY + t,
        cCizgi);
  }
}

// Hazırlanan agizYv eğrisini noktalar halinde çizer
void agizCiz()
{
  int cx = 160;
  int cy = 190 + nefesPx;

  for (int j = 0; j < AGIZ_N; j++)
  {
    float xn = (j - AGIZ_N / 2) / (float)(AGIZ_N / 2);

    daireCiz(
        cx + (int)roundf(xn * agizHW),
        cy + (int)roundf(agizYv[j]),
        2,
        cCizgi);
  }

  // "y" şeklinde ağzın üstündeki dikey çizgi
  int bh = (int)(16 * kareR.mw[5]);

  if (bh > 0)
    kutuCiz(cx - 1, cy - bh, 3, bh, cCizgi);
}

// Verilen yüz durumunu (gözler, kaş, ağız, efektler) tampona çizer
void yuzCiz(const YuzR &y)
{
  int gozY = 100 + nefesPx;

  int gozX[2] = {100, 220};

  int w = (int)(70 * y.eye_size);

  // Göz yüksekliği (kırpma dahil) ve kaş konumu için kırpmasız yükseklik
  int h = max(
      5,
      (int)(70 * y.eye_size * y.eye_open * (1.0f - y.kapali)));

  int hKas = max(
      5,
      (int)(70 * y.eye_size * y.eye_open));

  // Yanaklar (gözlerin altında pembe daire)
  if (y.blush > 0.02f)
  {
    uint16_t cYanak = karistir(cZemin, cPembe, y.blush);

    for (int k = 0; k < 2; k++)
    {
      daireCiz(
          gozX[k],
          gozY + 62,
          14,
          cYanak);
    }
  }

  for (int k = 0; k < 2; k++)
  {
    int cx = gozX[k];

    // Göz yuvası
    yuvarlakKutuCiz(
        cx - w / 2,
        gozY - h / 2,
        w,
        h,
        min(w, h) / 2,
        cCizgi);

    // Göz bebeği yarıçapı; göz kapanırken küçülür
    int r = (int)(min(w, h) / 2 * 0.5f * y.pupil);

    float acikOran = constrain((h - 8) / 16.0f, 0.0f, 1.0f);
    r = (int)(r * acikOran);

    if (r >= 2)
    {
      // Bebeğin gözün içinde kayabileceği en fazla mesafe
      int dx = max(
          0,
          (int)((w / 2 - r) * 0.8f));

      int dy = max(
          0,
          h / 2 - r);

      int ix = cx + (int)(y.look_x * dx);
      int iy = gozY + (int)(y.look_y * dy);

      daireCiz(ix, iy, r, cIris);

      // Bebekteki ışık parıltısı
      if (y.sparkle > 0.3f)
      {
        daireCiz(
            ix - r / 3,
            iy - r / 3,
            max(2, (int)(r * 0.3f * y.sparkle)),
            cBeyaz);
      }
    }
  }

  // Kaşlar gözün üstünde, brow_height ile yükselir
  int kasY =
      gozY - hKas / 2 - 14 - (int)(y.brow_height * 40);

  kasCiz(gozX[0], kasY, y.brow_left, 1);
  kasCiz(gozX[1], kasY, y.brow_right, -1);

  agizCiz();

  // Gözyaşları
  if (y.tears > 0)
  {
    for (int k = 0; k < 2; k++)
    {
      daireCiz(
          gozX[k],
          gozY + hKas / 2 + 6 + (int)(y.tears * 40),
          5 + (int)(y.tears * 4),
          cGozyasi);
    }
  }

  // Sağ üstteki öfke işareti (artı biçimli)
  if (y.anger > 0.02f)
  {
    uint16_t cOfke = karistir(cZemin, cKirmizi, y.anger);

    for (int t = -1; t <= 1; t++)
    {
      yatayCiz(255, 40 + t, 20, cOfke);
      dikeyCiz(265 + t, 30, 20, cOfke);
    }
  }
}

// =========================================================================
// Klip oynatma
// =========================================================================

// no'ya ait klibi yükleyip oynatır. poseOynasin=false ise servolar sürülmez.
bool klipOynat(int no, bool poseOynasin = true)
{
  if (!klipYukle(klipler[no].json))
    return false;

  // İlk açılışta yüz doğrudan ilk anahtardan başlar
  if (ilkYukleme)
  {
    kareR = yuzdenR(keys[0].yuz);
    ilkYukleme = false;
  }

  // Yumuşak geçiş için mevcut yüz ve servo açıları saklanır
  gecisR = kareR;

  for (int i = 0; i < NUM_SERVOS; i++)
  {
    gecisAcilar[i] = currentVal[i];
  }

  gecisZamani = millis();

  klipBaslangic = millis();

  aktifKlipNo = no;
  idleOynuyor = (no == idleKlipNo || no == sleepyKlipNo);

  kareCiziliyor = false;
  sonKareZamani = 0;

  poseAnimasyonuAktif = poseOynasin;
  sonPoseGuncelleme = 0;

  if (poseOynasin)
    moving = false;

  return true;
}

// UTF-8'de 2 baytlık Türkçe harfi ASCII karşılığına çevirir, tanımazsa 0 döner
char turkceHarf(unsigned char c, unsigned char d)
{
  if (c == 0xC3)
  {
    if (d == 0xA7 || d == 0x87)
      return 'c'; // ç Ç
    if (d == 0xB6 || d == 0x96)
      return 'o'; // ö Ö
    if (d == 0xBC || d == 0x9C)
      return 'u'; // ü Ü
  }
  else if (c == 0xC4)
  {
    if (d == 0x9F || d == 0x9E)
      return 'g'; // ğ Ğ
    if (d == 0xB1 || d == 0xB0)
      return 'i'; // ı İ
  }
  else if (c == 0xC5)
  {
    if (d == 0x9F || d == 0x9E)
      return 's'; // ş Ş
  }

  return 0;
}

// Klip adını küçük harfli ASCII'ye çevirir: "Derın_Uyku" -> "derin_uyku"
void adiSadelestir(const char *kaynak, char *hedef, int hedefBoyut)
{
  int j = 0;

  for (int i = 0; kaynak[i] != 0 && j < hedefBoyut - 1; i++)
  {
    unsigned char c = kaynak[i];

    char yeni = turkceHarf(c, kaynak[i + 1]);

    if (yeni != 0)
      i++; // Türkçe harfin ikinci baytını atla
    else
      yeni = tolower(c);

    hedef[j++] = yeni;
  }

  hedef[j] = 0;
}

// Adı verilen klibi bulup oynatır; bulunamazsa false döner
bool klipAdiylaOynat(const char *ad)
{
  char temiz[40];
  adiSadelestir(ad, temiz, sizeof(temiz));

  for (int i = 0; i < KLIP_SAYISI; i++)
  {
    if (strcmp(klipler[i].ad, temiz) == 0)
    {
      return klipOynat(i);
    }
  }

  return false;
}

// =========================================================================
// Kare hazırlama ve blok çizimi
// =========================================================================

// Klibin o anki zamanına göre yeni yüz karesini hesaplar
void kareHazirla()
{
  unsigned long now = millis();

  unsigned long t = now - klipBaslangic;

  // Klip bitti: döngüsel klipse başa sar, değilse idle'a dön
  if (t >= klipSuresi)
  {
    if (idleOynuyor || idleKlipNo < 0)
    {
      t = t % klipSuresi;

      klipBaslangic = now - t;
    }
    else
    {
      klipOynat(idleKlipNo);
      return;
    }
  }

  YuzR hedef;

  if (t <= keys[0].t)
  {
    hedef = yuzdenR(keys[0].yuz);
  }
  else if (t >= keys[keySayisi - 1].t)
  {
    hedef = yuzdenR(keys[keySayisi - 1].yuz);
  }
  else
  {
    // t'yi kapsayan anahtar çiftini bul ve aralarında ara değer al
    int i = 0;

    while (i < keySayisi - 2 && keys[i + 1].t <= t)
    {
      i++;
    }

    unsigned long fark =
        keys[i + 1].t - keys[i].t;

    float u =
        (fark == 0)
            ? 1.0f
            : (float)(t - keys[i].t) / fark;

    hedef = yuzRAra(
        yuzdenR(keys[i].yuz),
        yuzdenR(keys[i + 1].yuz),
        easeUygula(keys[i + 1].ease, u));
  }

  // Klip başında önceki yüzden yeni yüze yumuşak geçiş
  unsigned long g = now - gecisZamani;

  if (g < GECIS_MS)
  {
    float w = (float)g / GECIS_MS;
    w = w * w * (3 - 2 * w);

    kareR = yuzRAra(gecisR, hedef, w);
  }
  else
  {
    kareR = hedef;
  }

  // Göz kırpma ve nefes her klibin üstüne biner
  kareR.kapali = max(kareR.kapali, kirpmaDeger);
  nefesPx = (int)roundf(nefesDeger * NEFES_PIKSEL);

  agizHazirla();

  blokNo = 0;

  kareCiziliyor = true;
}

// Tamponun FNV-1a özetini hesaplar (içerik değişti mi kontrolü için)
uint32_t canvasOzet()
{
  const uint32_t *p = (const uint32_t *)canvas.getBuffer();

  uint32_t h = 2166136261u;

  // Her 32 bit iki piksel içerir
  for (int i = 0; i < BLOK_W * BLOK_H / 2; i++)
  {
    h = (h ^ p[i]) * 16777619u;
  }

  return h;
}

// Bir bloğu çizer; içeriği değişmediyse ekrana göndermez
void blokCiz()
{
  blokX = (blokNo % BLOK_SUTUN) * BLOK_W;
  blokY = (blokNo / BLOK_SUTUN) * BLOK_H;

  canvas.fillScreen(cZemin);

  yuzCiz(kareR);

  uint32_t ozet = canvasOzet();

  if (ozet != blokOzet[blokNo])
  {
    blokOzet[blokNo] = ozet;

    tft.drawRGBBitmap(
        blokX,
        blokY,
        canvas.getBuffer(),
        BLOK_W,
        BLOK_H);

    blokGonderilen++;
  }

  blokNo++;

  // Son blok bitti, kare tamamlandı
  if (blokNo >= BLOK_TOPLAM)
  {
    kareCiziliyor = false;
    fpsSay++;
  }
}

// Kare aralığı dolunca yeni kare hazırlar, hazırsa bir blok çizer.
// Her çağrıda tek blok çizildiği için loop() uzun süre bloke olmaz.
void klipGuncelle()
{
  if (!kareCiziliyor)
  {
    if (millis() - sonKareZamani < KARE_ARALIGI)
      return;

    sonKareZamani = millis();

    kareHazirla();

    return;
  }

  blokCiz();
}

// Ekranı başlatır, renkleri hazırlar, idle/sleepy klip indekslerini bulur
void ekranBaslat()
{
  tft.begin(SPI_HIZ);

  tft.setRotation(1);

  cZemin = tft.color565(0xFB, 0xF8, 0xF3);
  cCizgi = tft.color565(0x2B, 0x2A, 0x33);
  cIris = tft.color565(0x6B, 0x4A, 0x3A);
  cPembe = tft.color565(0xF0, 0x9A, 0xA6);
  cGozyasi = tft.color565(0x5D, 0xAD, 0xE2);
  cBeyaz = tft.color565(255, 255, 255);
  cKirmizi = tft.color565(220, 40, 40);

  tft.fillScreen(cZemin);

  for (int i = 0; i < KLIP_SAYISI; i++)
  {
    if (strcmp(klipler[i].ad, "idle") == 0)
    {
      idleKlipNo = i;
    }

    if (strcmp(klipler[i].ad, "sleepy") == 0)
    {
      sleepyKlipNo = i;
    }
  }

  if (idleKlipNo >= 0)
  {
    klipOynat(idleKlipNo);
  }
}

// =========================================================================
// Seri iletişim
// =========================================================================

// {"ack":seq,"ok":true} yanıtı gönderir
void ackGonder(int seqNumarasi)
{
  StaticJsonDocument<64> doc;

  doc["ack"] = seqNumarasi;
  doc["ok"] = true;

  serializeJson(doc, Serial);

  Serial.println();
}

// {"ack":seq,"ok":false,"err":kod} hata yanıtı gönderir
void hataGonder(int seqNumarasi, const char *hataKodu)
{
  StaticJsonDocument<96> doc;

  doc["ack"] = seqNumarasi;
  doc["ok"] = false;
  doc["err"] = hataKodu;

  serializeJson(doc, Serial);

  Serial.println();
}

// =========================================================================
// Setup ve loop
// =========================================================================

void setup()
{
  Serial.begin(115200);

  sonMesajZamani = millis();

  randomSeed(esp_random()); // Göz kırpma aralıkları için rastgele tohum
  sonNefesZamani = millis();
  sonrakiKirpma = millis() + 3000; // İlk kırpma 3 sn sonra

  motorlariBaslat();

  ekranBaslat();
}

void loop()
{
  // Engellemeyen (non-blocking) görev güncellemeleri
  nefesGuncelle();

  servoGuncelle();

  servoPoseGuncelle();

  klipGuncelle();

  // Seri porttan mesaj oku: mesaj '}' karakterinde veya satır sonunda tamamlanır
  while (Serial.available() > 0)
  {
    char c = Serial.read();

    bool mesajHazir = false;

    if (c == '}')
    {
      gelenSatir += c;
      mesajHazir = true;
    }
    else if (c == '\n' || c == '\r')
    {
      mesajHazir = true;
    }
    else
    {
      gelenSatir += c;

      // Bozuk ve çok uzun mesaj belleği şişirmesin: 256 karakteri aşarsa at
      if (gelenSatir.length() > 256)
      {
        gelenSatir = "";
        hataGonder(0, "bad_json");
      }
    }

    if (mesajHazir)
    {
      gelenSatir.trim();

      if (gelenSatir.length() > 0)
      {
        StaticJsonDocument<256> doc;

        DeserializationError error =
            deserializeJson(doc, gelenSatir);

        if (error)
        {
          hataGonder(0, "bad_json");
        }
        else
        {
          int seq = doc["seq"] | 0; // Numarasız mesajda seq = 0

          const char *cmd = doc["cmd"];

          if (cmd == nullptr)
          {
            hataGonder(seq, "bad_cmd");
          }

          // ping: bağlantı canlı mı kontrolü
          else if (strcmp(cmd, "ping") == 0)
          {
            sonMesajZamani = millis();

            sigortaDevredeMi = true;

            ackGonder(seq);
          }

          // neutral: yüz idle, servolar nötr konuma
          else if (strcmp(cmd, "neutral") == 0)
          {
            sonMesajZamani = millis();

            sigortaDevredeMi = true;

            if (idleKlipNo >= 0)
            {
              klipOynat(idleKlipNo, false);
            }

            poseAnimasyonuAktif = false;

            notrPozisyonaDon();

            ackGonder(seq);
          }

          // move: {"deg":[5 açı],"ms":süre} servoları doğrudan hareket ettirir
          else if (strcmp(cmd, "move") == 0)
          {
            if (!doc.containsKey("deg") ||
                !doc.containsKey("ms"))
            {
              hataGonder(seq, "bad_cmd");
            }
            else
            {
              JsonArray degArray =
                  doc["deg"].as<JsonArray>();

              int ms = doc["ms"];

              if (degArray.size() != 5 || ms < 0)
              {
                hataGonder(seq, "out_of_range");
              }
              else
              {
                int acilar[5];

                bool sinirDisi = false;

                // Her açı kendi servosunun sınırları içinde olmalı
                for (int i = 0; i < 5; i++)
                {
                  acilar[i] = degArray[i];

                  if (acilar[i] < minAci[i] ||
                      acilar[i] > maxAci[i])
                  {
                    sinirDisi = true;
                  }
                }

                if (sinirDisi)
                {
                  hataGonder(seq, "out_of_range");
                }
                else
                {
                  sonMesajZamani = millis();

                  sigortaDevredeMi = true;

                  poseAnimasyonuAktif = false;

                  hedefAcilaraGit(acilar, ms);

                  ackGonder(seq);
                }
              }
            }
          }

          // anim: {"name":klip_adı} adıyla klip oynatır
          else if (strcmp(cmd, "anim") == 0)
          {
            const char *ad = doc["name"];

            if (ad == nullptr || !klipAdiylaOynat(ad))
            {
              hataGonder(seq, "bad_cmd");
            }
            else
            {
              sonMesajZamani = millis();

              sigortaDevredeMi = true;

              ackGonder(seq);
            }
          }

          else
          {
            hataGonder(seq, "bad_cmd");
          }
        }
      }

      gelenSatir = "";
    }
  }

#if FPS_YAZ
  // Her 2 sn'de bir fps ve gönderilen blok sayısını yazdır
  if (millis() - fpsZaman >= 2000)
  {
    Serial.printf(
        "\nfps: %.1f, gonderilen blok: %lu / %lu\n",
        fpsSay / 2.0f,
        blokGonderilen,
        fpsSay * BLOK_TOPLAM);

    fpsSay = 0;
    blokGonderilen = 0;
    fpsZaman = millis();
  }
#endif

  // Mesaj gelmezse uykuya dal: servolar nötre, yüz sleepy, nefes devam eder
  if (sigortaDevredeMi &&
      (millis() - sonMesajZamani > UYKU_SURE_MS))
  {
    if (sleepyKlipNo >= 0)
      klipOynat(sleepyKlipNo, false);

    notrPozisyonaDon();

    sigortaDevredeMi = false;
  }
}
