# Konumsal Proje

Konumsal Bilgi Sistemleri için geliştirilen bu proje, kurumsal web sitesi ile stajyer ve personel süreçlerini bir araya getiren Django tabanlı bir web uygulamasıdır.

Projede öne çıkan ana alanlar:

- kurumsal web sayfaları
- staj başvuru ve başvuru sorgulama akışı
- stajyer paneli
- personel paneli
- günlük, belge ve mesajlaşma ekranları
- yönetim ve içerik düzenleme altyapısı

## Kullanılan Teknolojiler

### Backend

- Python
- Django
- Django REST Framework
- SimpleJWT

### Frontend

- HTML
- CSS
- Tailwind CSS
- JavaScript
- Django Template Language

### Veritabanı ve Ortam

- SQLite3
- PostgreSQL desteği
- `.env` tabanlı ortam değişkeni yönetimi

### Deploy

- Gunicorn
- WhiteNoise
- Render
- GitHub

## Projede Yapılan Başlıca Düzenlemeler

- stajyer ve personel paneli arayüzlerinin sadeleştirilmesi
- başvuru, günlük, belge ve mesajlaşma ekranlarının düzenlenmesi
- giriş akışlarının toparlanması
- oturum ve host yönlendirme problemlerinin düzeltilmesi
- hukuk sayfalarının eklenmesi ve düzenlenmesi
- production ayarlarının güçlendirilmesi
- güvenlik ve şifre akışlarında iyileştirmeler

## Önemli Dosyalar

- `core/settings.py`
- `core/middleware.py`
- `internship/views.py`
- `internship/admin.py`
- `internship/mail_utils.py`
- `website/views.py`
- `website/urls.py`
- `website/templates/website/legal_page.html`
- `website/templates/internship/conversation.html`
- `static/internship/css/panel_dashboard.css`

## Yerelde Çalıştırma

```powershell
cd C:\Users\Abidin CAN\konumsal-proje\konumsal-proje
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py runserver
```

Uygulama varsayılan olarak şu adreste açılır:

```text
http://127.0.0.1:8000/
```

## Tailwind Derleme

```powershell
npx tailwindcss -i .\static\css\input.css -o .\static\css\output.css
```

## Deploy Notu

Proje production ortamı için yapılandırılmıştır. `render.yaml`, `Procfile`, `build.sh` ve ortam değişkenleri üzerinden dağıtım yapılabilir.

Özellikle dikkat edilmesi gereken değişkenler:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `APP_BASE_URL`
- `CANONICAL_HOST`

## Repo

GitHub deposu:

- [konumsal-proje](https://github.com/Cankhy/konumsal-proje)
