# Krallar Ligi Sıralaması

TFF Fantezi Lig "Krallar" ligi (47061) için MH1-2 hariç sıralama ve joker tablosu üreten,
GitHub Actions ile güncellenip GitHub Pages'te yayınlanan küçük bir Python projesi.
Hesaplama kuralları, zamanlama, kurulum ve cache mantığı için önce `README.md`'yi oku;
burada tekrarlanmıyor.

## Çalışma kuralları

- Çalışmaya başlamadan önce `git pull` yap: bot her gün (ve Salı sabahı) `main`'e
  "Sıralama güncellendi" commit'i atıyor (`data/` ve `site/`).
- Ortam: `uv sync`, testler `uv run pytest -q`. Workflow deploy'dan önce testleri çalıştırır;
  testler kırılırsa sayfa güncellenmez.
- Yerelde çalıştırma: `uv run python -m krallar` → `site/index.html` üretir. Giriş bilgileri
  proje kökündeki `.env` dosyasından okunur; `.env` asla commit edilmez.
- Commit mesajları Türkçe: kısa bir başlık, gerekirse altında madde madde açıklama.
- `tests/fixtures/` içindeki veriler anonimleştirilmiştir; gerçek takım/kullanıcı adı ekleme.
- Sayfadaki metinler ve kullanıcıya dönük mesajlar (log, hata mesajları) Türkçe.

## Kod nerede

- `krallar/client.py`: tfffantezilig.com için salt okunur API istemcisi (giriş, sıralama, takım haftaları).
- `krallar/compute.py`: ağ erişimi olmayan saf hesaplamalar; `EXCLUDED_UNTIL_GW` ve joker
  kodlarının `CHIPS` tablosu burada.
- `krallar/render.py`: HTML sayfasını üretir (telefonda kartlar, geniş ekranda tablo).
- `krallar/__main__.py`: her şeyi birleştirir; son haftayı bulur, cache'i günceller, sayfayı yazar.
- `data/history-cache.json`: bitmiş haftaların takım puanları ve jokerleri.
- `site/index.html`: üretilen sayfa; elle düzenleme, `render.py`'yi değiştir.

## Kararlar ve dikkat edilecekler

- **MH1-2 hariç:** puan MH3'ten son haftaya kadar takımın kendi haftalık puanlarının toplamı.
  MH1-2'de kullanılan jokerler harcanmış sayılmaz.
- **Eşitlik:** toplam puan eşitse son maç haftası puanı yüksek olan önde; ikisi de eşitse
  aynı sırayı paylaşırlar (takım adına göre dizilir).
- **`live` alanına güvenme:** hafta sürerken API `live: false` ile yarım puan döndürüyor.
  Bir hafta ancak fikstürde bitti olarak işaretlenip bütün puan ve bonusları eklenince
  cache'e yazılır; devam eden hafta her çalıştırmada yeniden çekilir.
- **Sıra değişimi (▲/▼):** sitenin kendi sıra değişimi MH1-2'yi de saydığı için kullanılmaz;
  önceki sıra cache'ten aynı kuralla hesaplanır. MH3'te gösterilmez.
- **Güncelleme saati:** sayfa Türkiye saatini yazar, küçük bir script ziyaretçinin saat
  dilimine çevirir.
- **Lig kuralı, jokerler sezonda bir kez:** oyunda menajer kartları (jokerler) devre arasından
  sonra (MH17'den itibaren) yenilenir, ama Krallar Ligi'nde sezon başında karar verildi: her takım
  her jokeri **sezon boyunca yalnızca bir kez** kullanabilir. MH1-2'deki kullanım sayılmadığı için
  o joker sonra bir kez daha kullanılabilir. Sayfa MH3+ ikinci kullanımı "kural dışı" rozetiyle
  işaretler (`render.py`, `_badge_states`; turuncu, kesik çerçeve, sonunda "!"). Puana bir yaptırım
  yok; yaptırım ileride konuşulabilir.
- **Lig kuralı, menajer kartı satın almak yasak:** oyunda kartlar App Store / Google Play üzerinden
  ücretle alınabiliyor; Krallar Ligi'nde satın almak yasak. Oyun her jokeri her yarıda (MH1-16,
  MH17-34) bir kez bedava verir ve bedava hakkı kullanılmadan satın alınamaz; yani **aynı yarıda aynı
  jokerin ikinci kullanımı satın alınmış karttır**. Sayfa bunları "kural dışı" gösterir, ayrı bir
  "satın alındı" rozeti yok. **İstisna (kullanıcı kararı, değiştirme):** MH1-2'deki kullanım ligde
  sayılmadığı için MH1-2 + MH3-16 kullanımında MH3-16'daki kullanım ilk geçerli kullanım kabul edilir
  ve normal gösterilir. Öneride kart satın almayı asla önerme.
- **Bilinmeyen joker kodu** uyarısı log'da çıkarsa `CHIPS` tablosunu güncelle.
- **Denendi ve kaldırıldı:** "Haftanın hareketleri" bölümü (her hafta için en çok yükselen/düşen
  listesi). Yerine sadece güncel hafta için "En çok yükselen / düşen" kutuları kaldı.

## Takvim ve milli aralar

- 2026-27 Süper Lig: 14 Ağustos 2026 – 23 Mayıs 2027, 34 hafta (`MAX_GW = 34`).
- **Kasım 2026 milli arası:** FIFA penceresi 9–17 Kasım 2026. Son oynanan hafta MH11
  (cache'te bitmiş olarak kayıtlı); MH12 21–23 Kasım 2026'da oynanacak.
- Eylül ve Ekim araları bu sezon tek pencerede birleşti (21 Eylül – 6 Ekim 2026); Ekim'de ayrı ara yok.
- **Devre arası (TFF):** ilk yarı MH16 ile biter (18–21 Aralık 2026); ikinci yarı MH17 ile
  15–18 Ocak 2027'de başlar.
- **Sonraki milli aralar (FIFA):** 22–30 Mart 2027, 7–15 Haziran 2027 (sezon bittikten sonra).
- Milli arada workflow her gün çalışmaya devam eder ama yeni hafta olmadığı için sıralama değişmez;
  `find_latest_gameweek` oynanmamış haftalar için son haftanın tablosunu aldığından MH11'de kalır.
  Bu normaldir, hata aranmamalı. Ara bitince ilk çalıştırmada MH12 "devam ediyor" olarak görünmeli.
- Sonraki milli aralar için tarihleri FIFA/TFF takviminden kontrol et; buraya ekle.

## Fantezi lig soruları

Kullanıcı bazen kod dışında transfer ve takım önerisi (kadro, kaptan, joker zamanlaması) soruyor.

- Haberler (sakatlık, ceza, kadro, transfer) için **sporx.com**'u kullan
  (ör. WebSearch'te `allowed_domains: ["sporx.com"]`); haberin tarihini kontrol et, eskiyse söyle.
- **Önce hızlı kaynaklara bak** (kullanıcı tercihi: KAP gibi resmi kaynaklar geç güncelleniyor).
  Aramada bu sırayı izle:
  1. **Güncel/son dakika (X):** [x.com/demarkesports](https://x.com/demarkesports) ve benzeri hesaplar,
     ör. transfer gazetecileri Yağız Sabuncuoğlu (@yagosabuncuoglu), Ekrem Konur (@ekremkonur).
     X sayfaları girişsiz çoğu zaman okunamaz; o zaman WebSearch ile hesabın paylaşımlarını ara.
  2. **Haber:** sporx.com, **ntvspor.net**, **trtspor.com.tr**, **fanatik.com.tr**, **fotomac.com.tr**.
  3. **İstatistik ve kadro:** **mackolik.com** (fikstür, muhtemel/kesin 11), **sofascore.com**
     (reyting, dakika, form), **transfermarkt.com.tr** (sakatlık, kart cezası, transfer söylentileri).
  4. **Resmi (yavaş ama kesin):** kulüplerin resmi siteleri/X hesapları, **kap.org.tr**
     (halka açık kulüplerin transferleri), **tff.org** (PFDK cezaları, fikstür). Kesinleşip
     kesinleşmediğini doğrulamak için bak; resmi açıklama yoksa öneriyi bekletme.
- Hızlı kaynaklar çoğu zaman söylenti düzeyindedir: her bilginin kaynağını ve durumunu
  (söylenti / haber / resmi) belirt, birden çok kaynak aynı şeyi söylüyorsa bunu da yaz.
- **Oyuncu verisi API'den okunabilir** (`.env` girişiyle):
  `projection/stats/player-stats?league-id=1` (oyuncu, `cost` fiyat, puan, form, sahiplik, ceza/ayrılma
  durumu), `projection/stats/club-stats?league-id=1` (kulüp adları), `projection/stats/fixtures?league-id=1`
  (haftalar, maçlar, kilit saati), `fantasy-team/teams/{id}/squad` (mevcut kadro). Oyunun
  `availabilityStatus` alanı sakatlıkları göstermiyor (sadece ceza/ayrılma); sakatlığı haberden kontrol et.
  Kullanıcı API'ye geniş izin verdi ama kadroyu değiştiren (POST/PUT) istekleri ancak o an açıkça isterse at.
- Hafta tarihleri ve milli aralar için yukarıdaki "Takvim ve milli aralar" bölümüne bak.
- **Oyun kuralları:** [tfffantezilig.com/yardim](https://tfffantezilig.com/yardim). Öneri için gereken
  özet (2026-11-16'da okundu; kural sorusunda emin olmak için sayfayı tekrar kontrol et):
  - Kadro 15 (2 KL, 5 DF, 5 OS, 3 FV), bütçe 100M, aynı kulüpten en fazla 3. İlk 11'de en az
    1 KL, 3 DF, 1 FV. Yedekler otomatik girer (oynamayan ilk 11 oyuncusunun yerine, dizilim kuralına uygun).
  - Transfer sınırı ve cezası yok. Kadro haftanın ilk maçından 1 saat önce kilitlenir.
  - Kaptan x2. Kurallar sayfası yazmasa da oyunda yardımcı kaptan var (API: `viceCaptainPlayerId`);
    kaptan oynamazsa kaptanlık ona geçer (MH11'de böyle oldu).
  - Puanlar: 60 dk'ya kadar oynamak 1, 60 dk'dan fazla 2; gol KL 10, DF 6, OS 5, FV 4; asist 3;
    gol yememe (60+ dk) KL/DF 4, OS 1; her 3 kurtarış 1; penaltı kurtarma 5; penaltı kaçırma -2;
    KL/DF her 2 yenilen gol -1; sarı -1, kırmızı -3, kendi kalesine -2; maçın en iyi üç oyuncusuna
    bonus 3/2/1.
  - Jokerler: Tripleks Kaptan (kaptan x3), Dört Dörtlük Kaptan (x4), Tüm Takım Sahaya (yedekler de
    sayılır), Hücum (dizilim kuralı yok, o hafta bütçe +5M), Limitsiz Bütçe (bütçe sınırsız transfer).
    Aynı hafta tek joker; açılan joker geri alınamaz. Yenilenme kuralını sayfa yazmıyor; ligimizde
    her joker sezonda bir kez (yukarıdaki lig kuralı).
  - Haftalık toplam = oyuncu puanları (`matchPoints`) + **Nostradamus (tahmin) puanı**
    (`nostradamusPoints`; AmsterdamSpor MH10'da 4, MH11'de 8). Kurallar sayfası bundan bahsetmiyor ama
    lig sıralaması bu toplamı kullanıyor; öneride tahminleri yapmayı da hatırlat.
  - Üçüncü taraf bir kural özeti "kadroyu kaydet"e basana haftalık +1 puan diyor; MH10-11 puan
    dökümünde böyle bir satır yok (toplam = oyuncu puanları + Nostradamus). Doğrulanmadı, kural gibi sunma.
  - Ödüller (tfffantezilig.com/oduller): belirli haftalarda ödüllü mini ligler; basına göre sezon
    birincisine otomobil (resmi değil). Krallar Ligi'nin kendi ödülü/kuralı bunlardan ayrı.
  - Bütçe hakkında sayfa yalnızca 100M başlangıcı, Hücum'un "hafta özelinde" +5M'i ve Limitsiz Bütçe'yi
    yazıyor. Fiyat değişimi, satış değeri ve kartlardan sonraki hafta bütçeye dönüş yazmıyor;
    öneride bunları kesin kural gibi sunma, oyunda kontrol edilmesini söyle.
- **Kaleci ve defans seçerken o haftanın rakibine bak** (kullanıcı tercihi): gol yememe KL/DF'ye 4 puan,
  OS'ye 1 puan; her 2 yenilen gol KL/DF'ye -1. Rakibin hücumu zayıf, kendi defansı sağlam ve iç sahada
  oynayan takımların KL/DF'sini tercih et. Gol yememe olasılığını (rakibin attığı gol x kendi yediği gol,
  iç saha/deplasman) hafta hafta hesapla ve öneride göster.
- **Joker önerirken kaptan adayının maçlarını karşılaştır:** genel gerekçeyle "kullanma" deme; adayın
  önümüzdeki haftalardaki rakiplerini (rakibin yediği gol, iç saha/deplasman) karşılaştırıp en iyi haftayı öner.
- Joker önerirken lig kuralını uygula: oyun MH17'de jokerleri yenilese de takımın daha önce
  (MH3+) kullandığı jokeri tekrar önerme.
- Bu sorular kod değişikliği değildir; istenmedikçe repoda bir şey değiştirme.

## Tasarım

Sayfa önce Claude'da Design tuvallerinde tasarlandı, sonra `render.py`'ye aktarıldı. Tuvaller
özel (private); içlerinde gerçek takım adları var, repoya kopyalama.

- [Krallar Ligi Sıralaması](https://claude.ai/artifact/A6thhPPJLkXgZchjRjfCVe) (2026-11-03): ilk tasarım,
  telefon (kartlar) ve masaüstü (tablo).
- [Sıra Değişimi](https://claude.ai/artifact/9w97mJPxtFqbLqXEk7ahNT) (2026-11-07): ▲/▼ rozetleri,
  "En çok yükselen / düşen" kutuları (masaüstü tek satır, beraberlik), kaldırılan "Haftanın hareketleri"
  taslakları (başlıklarında "kaldırıldı" yazar).

Güncel görünümün kaynağı `render.py`'deki CSS'tir; tuvaller eskiyebilir (ör. "Her Salı 10:00"
yazıyorlar). Görsel dil:

- Fontlar: başlık ve rakamlar Barlow Condensed 600/700, metin Inter 400/500/600 (Google Fonts).
- Renkler: vurgu `#0B6E4F` (ilk 3 sıra, kullanılmış joker), koyu başlık şeridi `#12161C`, zemin `#F3F4F1`,
  kartlar beyaz; yükselen `#E2F1E9`/`#0B5C42`, düşen `#FCE9DB`/`#9A3B06`, ikincil metin `#5A6270`.
- Kartlar 12px köşe, hafif gölge; telefonda kartlar, 760px ve üstünde tablo.
- Joker rozetleri dört durumda: kullanıldı (dolu vurgu), MH1-2'de kullanıldı (gri, üstü çizili),
  kullanılmadı (çerçeveli), kural dışı ikinci kullanım (turuncu, kesik çerçeve, "!").
