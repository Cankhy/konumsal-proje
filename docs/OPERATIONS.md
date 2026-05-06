# Operasyon ve Yayın Planı

## Ortam Değişkenleri

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`

## Loglama

- Uygulama logları: `logs/application.log`
- Hata logları: `logs/errors.log`
- Form doğrulama hataları: admin üzerinden `FormErrorLog` kayıtlarında izlenebilir

## Yedekleme Planı

### Veritabanı

- SQLite kullanılıyorsa günlük `db.sqlite3` kopyası alınmalı.
- PostgreSQL kullanılıyorsa günlük `pg_dump` ile yedek alınmalı.
- Yedekler en az 7 günlük döngüyle saklanmalı.

### Medya Dosyaları

- `media/` klasörü günlük veya en az haftalık yedeklenmeli.
- CV, belge ve mesaj ekleri aynı politikaya dahil edilmeli.

## Geri Dönüş Planı

1. Son çalışan commit etiketi belirlenir.
2. Veritabanı yedeği geri yüklenir.
3. `media/` klasörü geri alınır.
4. Uygulama bir önceki kararlı sürüme döndürülür.
5. `manage.py check` ve temel giriş akışları test edilir.

## Canlıya Çıkış Kontrol Listesi

1. `python manage.py migrate`
2. `python manage.py collectstatic --noinput`
3. Yönetici, personel ve stajyer giriş testleri
4. Belge yükleme ve mesaj dosya sınırı testleri
5. 404/500 sayfalarının görünürlük testi
6. Log dosyası yazım testi
