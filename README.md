# Krallar Ligi Sıralaması

TFF Fantezi Lig "Krallar" ligi (47061) için 1. ve 2. maç haftaları **hariç** sıralama ve
her takımın hangi hafta hangi jokeri kullandığını gösteren sayfa. Her Salı 10:00 TSİ'de
GitHub Actions ile güncellenir ve GitHub Pages'te yayınlanır.

**Puan** = her takımın kendi maç haftası geçmişinden MH3..son hafta puanlarının toplamı.

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

Takım haftaları `data/history-cache.json` içinde saklanır, biten haftalar tekrar çekilmez.
Her çalıştırma takım başına sitedeki lig puanını, bizim puanı ve aradaki farkı log'a yazar.
Yerelde giriş bilgileri proje kökündeki `.env` dosyasından okunur (commit edilmez).
