# Krallar Ligi Sıralaması

TFF Fantezi Lig "Krallar" ligi (47061) için 1. ve 2. maç haftaları **hariç** sıralama ve
her takımın hangi hafta hangi jokeri kullandığını gösteren sayfa. Her gün 23:59 TSİ'de, Salı
günleri ayrıca 10:00 TSİ'de GitHub Actions ile güncellenir ve GitHub Pages'te yayınlanır. Maç haftası
sürerken son haftanın puanı geçicidir; sayfada "MH.. devam ediyor" yazar.

**Puan** = her takımın kendi maç haftası geçmişinden MH3..son hafta puanlarının toplamı.

**Sıra değişimi** (▲/▼) = bir önceki maç haftasının sonundaki sıralamaya göre kaç sıra
yükselip düştüğü. Önceki sıra cache'teki haftalardan aynı kuralla (MH3+ toplam, eşitlikte o
haftanın puanı) hesaplanır; sitenin kendi sıra değişimi MH1-2'yi de saydığı için kullanılmaz.
MH3'te karşılaştırılacak hafta olmadığından gösterilmez.

## Kurulum

1. Repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `TFF_EMAIL`: tfffantezilig.com e-postası
   - `TFF_PASSWORD`: şifre
2. Repo → **Settings → Pages → Source: GitHub Actions**.
3. **Actions → "Sıralamayı güncelle" → Run workflow** ile ilk çalıştırmayı elle yap.

## Yerelde çalıştırma

```bash
uv sync
uv run pytest -q
TFF_EMAIL=... TFF_PASSWORD=... uv run python -m krallar   # site/index.html üretir
```

## Jokerler

Joker kodları `krallar/compute.py` içindeki `CHIPS` tablosunda (beşi de gerçek veride
doğrulandı). Log'da "bilinmeyen joker kodu" uyarısı çıkarsa tabloyu güncelleyin.

Takım haftaları `data/history-cache.json` içinde saklanır. Bir hafta ancak fikstürde bitti
olarak işaretlenip bütün puan ve bonusları eklendiğinde cache'e yazılır ve bir daha çekilmez;
devam eden haftanın puanları her çalıştırmada yeniden çekilir (hafta sürerken API `live: false`
ile yarım puan döndürüyor, bu yüzden `live` alanına güvenilmez).
Her çalıştırma takım başına sitedeki lig puanını, bizim puanı ve aradaki farkı log'a yazar.
Yerelde giriş bilgileri proje kökündeki `.env` dosyasından okunur (commit edilmez).
