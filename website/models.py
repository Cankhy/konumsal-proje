from django.db import models


class AboutPage(models.Model):
    title = models.CharField("Başlık", max_length=150, default="Hakkımızda")
    hero_title = models.CharField(
        "Üst Başlık", max_length=200, blank=True,
        help_text="Sayfanın üst kısmında görünen büyük başlık."
    )
    hero_subtitle = models.CharField(
        "Alt Başlık", max_length=255, blank=True,
        help_text="Başlığın altında kısa açıklama."
    )
    content = models.TextField("İçerik")
    last_updated = models.DateTimeField("Son güncelleme", auto_now=True)

    class Meta:
        verbose_name = "Hakkımızda Sayfası"
        verbose_name_plural = "Hakkımızda Sayfası"

    def __str__(self):
        return self.title


class Service(models.Model):
    title = models.CharField("Hizmet Adı", max_length=150)
    slug = models.SlugField("URL", unique=True)
    short_description = models.CharField("Kısa Açıklama", max_length=255)
    description = models.TextField("Detay Açıklama", blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Yayında mı?", default=True)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Hizmet"
        verbose_name_plural = "Hizmetler"

    def __str__(self):
        return self.title


class Project(models.Model):
    title = models.CharField("Proje Adı", max_length=150)
    slug = models.SlugField("URL", unique=True)
    client = models.CharField("Müşteri / Kurum", max_length=150, blank=True)
    summary = models.CharField("Kısa Özet", max_length=255)
    description = models.TextField("Detay Açıklama", blank=True)
    start_date = models.DateField("Başlangıç Tarihi", null=True, blank=True)
    end_date = models.DateField("Bitiş Tarihi", null=True, blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Yayında mı?", default=True)
    is_featured = models.BooleanField("Anasayfada Göster", default=False)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Proje"
        verbose_name_plural = "Projeler"

    def __str__(self):
        return self.title


class ContactInfo(models.Model):
    company_name = models.CharField("Firma Adı", max_length=200)
    address = models.TextField("Adres")
    phone = models.CharField("Telefon", max_length=50, blank=True)
    email = models.EmailField("E-posta", blank=True)
    map_iframe = models.TextField(
        "Harita (iframe)", blank=True,
        help_text="Google Maps embed kodu (opsiyonel)."
    )
    updated_at = models.DateTimeField("Son güncelleme", auto_now=True)

    class Meta:
        verbose_name = "İletişim Bilgisi"
        verbose_name_plural = "İletişim Bilgileri"

    def __str__(self):
        return self.company_name
