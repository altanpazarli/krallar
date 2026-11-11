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
- Diğer kaynaklar, ne arandığına göre:
  - **Resmi (en güvenilir):** kulüplerin resmi siteleri/X hesapları (sakatlık, kadro),
    **kap.org.tr** (halka açık kulüplerin kesinleşen transferleri), **tff.org** (PFDK cezaları, fikstür).
  - **İstatistik ve kadro:** **mackolik.com** (fikstür, muhtemel/kesin 11), **sofascore.com**
    (reyting, dakika, form), **transfermarkt.com.tr** (sakatlık, kart cezası, transfer söylentileri).
  - **Haber:** **ntvspor.net**, **trtspor.com.tr** (genelde doğrulanmış); **fanatik.com.tr**,
    **fotomac.com.tr** (transferde hızlı ama çoğu söylenti, temkinli aktar).
  - **Güncel/son dakika (X):** [x.com/demarkesports](https://x.com/demarkesports) ve benzeri hesaplar,
    ör. transfer gazetecileri Yağız Sabuncuoğlu (@yagosabuncuoglu), Ekrem Konur (@ekremkonur).
    X sayfaları girişsiz çoğu zaman okunamaz; o zaman WebSearch ile hesabın paylaşımlarını ara.
    Bunlar söylenti düzeyindedir: kaynağı belirt, resmi açıklamayla karıştırma.
- Önerirken önceliği şöyle ver: resmi açıklama > doğrulanmış haber > söylenti; hangisi olduğunu söyle.
- Hafta tarihleri ve milli aralar için yukarıdaki "Takvim ve milli aralar" bölümüne bak.
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
- Joker rozetleri üç durumda: kullanıldı (dolu vurgu), MH1-2'de kullanıldı (gri, üstü çizili),
  kullanılmadı (çerçeveli).
