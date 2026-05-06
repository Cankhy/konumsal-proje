# konumsal-proje

Konumsal Bilgi Sistemleri staj ve personel modüllerini içeren Django tabanlı proje.

## Bu turda yapılanlar

- Personel paneli, stajyer paneli, başvuru, sorgulama, günlük, belge ve mesajlaşma ekranları daha okunur bir görsel sisteme taşındı.
- Giriş ekranları, şifre değiştirme ekranları ve başvuru başarılı ekranı yeni tasarım diliyle eşitlendi.
- Mobil görünüm; özellikle tablo, form ve mesaj alanlarında sıkılaştırıldı.
- Dosya seçimi geri bildirimi eklendi.
- Production hazırlığı için `render.yaml`, `Procfile`, `build.sh` ve ortam değişkeni destekleri eklendi.

## Yerelde çalıştırma

```powershell
$env:PYTHONPATH = (Resolve-Path '.\venv\Lib\site-packages').Path
py -3 manage.py migrate
py -3 manage.py runserver
```

Tailwind çıktısını yeniden üretmek için:

```powershell
npx tailwindcss -i .\static\css\input.css -o .\static\css\output.css
```

## Render ile canlı yayın

Projede sürekli açık kalabilecek bir Render kurulum dosyası hazırlandı:

- `render.yaml`
- `Procfile`
- `build.sh`

Canlıya almak için:

1. Bu projeyi bir GitHub reposuna push et.
2. Render üzerinde `Blueprint` veya `New Web Service` ile repoyu bağla.
3. `render.yaml` içindeki servis ve PostgreSQL veritabanı otomatik kurulacak şekilde ilerle.
4. Render alan adın belli olduktan sonra gerekirse `ALLOWED_HOSTS` ve `CSRF_TRUSTED_ORIGINS` değerlerini güncelle.

Not:

- Render `starter` planı sürekli açık kalır; free benzeri uyku moduna düşen servis istemiyorsan düşük ücretli sürekli çalışan plan kullanmalısın.
- SQLite yerine canlıda PostgreSQL kullanımı için ayarlar hazırlandı.

## Eksik kalan dış adım

Bu çalışma alanında GitHub remote tanımlı değil ve `gh` CLI kurulu değil. Bu yüzden repo push ve canlı servise bağlama adımı kod tarafında hazır olsa da doğrudan tamamlanamadı.
