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


class HomeSlide(models.Model):
    title = models.CharField("Slider Başlığı", max_length=160)
    subtitle = models.TextField("Açıklama", blank=True)
    image = models.FileField("Görsel", upload_to="home/slides/")
    button_text = models.CharField("Buton Yazısı", max_length=40, default="DETAYLAR")
    button_url = models.CharField(
        "Buton Linki",
        max_length=220,
        blank=True,
        help_text="Örn: /hizmetler/siber-guvenlik-sistemleri/",
    )
    second_button_text = models.CharField("İkinci Buton Yazısı", max_length=50, blank=True)
    second_button_url = models.CharField("İkinci Buton Linki", max_length=220, blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Yayında mı?", default=True)
    updated_at = models.DateTimeField("Son güncelleme", auto_now=True)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Ana Sayfa Slider"
        verbose_name_plural = "Ana Sayfa Slider"

    def __str__(self):
        return self.title


class HomeServiceCard(models.Model):
    title = models.CharField("Kart Başlığı", max_length=150)
    description = models.CharField("Kısa Açıklama", max_length=255, blank=True)
    image = models.FileField("Görsel", upload_to="home/service_cards/")
    link_url = models.CharField(
        "Link",
        max_length=220,
        blank=True,
        help_text="Örn: /hizmetler/cografi-bilgi-sistemleri/",
    )
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Yayında mı?", default=True)
    updated_at = models.DateTimeField("Son güncelleme", auto_now=True)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Ana Sayfa Hizmet Kartı"
        verbose_name_plural = "Ana Sayfa Hizmet Kartları"

    def __str__(self):
        return self.title


class ManagedPage(models.Model):
    PAGE_TYPES = (
        ("page", "Sayfa"),
        ("service", "Hizmet Detay"),
        ("project", "Proje Detay"),
    )

    title = models.CharField("Başlık", max_length=180)
    slug = models.SlugField("URL Anahtarı", unique=True)
    path = models.CharField(
        "Sayfa Yolu",
        max_length=220,
        unique=True,
        help_text="Örn: /hakkimizda/ veya /hizmetler/siber-guvenlik-sistemleri/",
    )
    page_type = models.CharField("Sayfa Türü", max_length=20, choices=PAGE_TYPES, default="page")
    eyebrow = models.CharField("Küçük Üst Başlık", max_length=80, blank=True)
    summary = models.TextField("Kısa Açıklama", blank=True)
    hero_image = models.FileField("Üst Görsel", upload_to="pages/hero/", blank=True)
    body = models.TextField("Ana İçerik", blank=True)
    primary_button_text = models.CharField("Ana Buton Yazısı", max_length=50, blank=True)
    primary_button_url = models.CharField("Ana Buton Linki", max_length=220, blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Yayında mı?", default=True)
    updated_at = models.DateTimeField("Son güncelleme", auto_now=True)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Yönetilebilir Sayfa"
        verbose_name_plural = "Yönetilebilir Sayfalar"

    def __str__(self):
        return self.title


class ManagedPageSection(models.Model):
    page = models.ForeignKey(
        ManagedPage,
        verbose_name="Sayfa",
        related_name="sections",
        on_delete=models.CASCADE,
    )
    title = models.CharField("Bölüm Başlığı", max_length=160)
    content = models.TextField("Bölüm İçeriği", blank=True)
    image = models.FileField("Bölüm Görseli", upload_to="pages/sections/", blank=True)
    button_text = models.CharField("Buton Yazısı", max_length=50, blank=True)
    button_url = models.CharField("Buton Linki", max_length=220, blank=True)
    order = models.PositiveIntegerField("Sıra", default=0)
    is_active = models.BooleanField("Yayında mı?", default=True)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Sayfa Bölümü"
        verbose_name_plural = "Sayfa Bölümleri"

    def __str__(self):
        return f"{self.page} - {self.title}"


class Service(models.Model):
    title = models.CharField("Hizmet Adı", max_length=150)
    slug = models.SlugField("URL", unique=True)
    short_description = models.CharField("Kısa Açıklama", max_length=255)
    description = models.TextField("Detay Açıklama", blank=True)
    image = models.FileField("Kart Görseli", upload_to="services/", blank=True)
    detail_url = models.CharField(
        "Detay Linki",
        max_length=220,
        blank=True,
        help_text="Örn: /hizmetler/cografi-bilgi-sistemleri/",
    )
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
    image = models.FileField("Kart Görseli", upload_to="projects/", blank=True)
    detail_url = models.CharField(
        "Detay Linki",
        max_length=220,
        blank=True,
        help_text="Örn: /projeler/orman-bilgi-sistemi/",
    )
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
