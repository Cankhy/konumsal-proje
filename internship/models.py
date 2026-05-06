from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils import timezone

User = settings.AUTH_USER_MODEL  # ForeignKey'lerde bunu kullanıyoruz


# TC kimlik ve telefon için validator'lar
tc_kimlik_validator = RegexValidator(
    regex=r"^\d{11}$",
    message="TC Kimlik numarası 11 haneli ve sadece rakamlardan oluşmalıdır.",
)

phone_validator = RegexValidator(
    regex=r"^\d{10,11}$",
    message="Telefon numarası 10-11 haneli olmalıdır.",
)


class Application(models.Model):
    first_name = models.CharField("Ad", max_length=50)
    last_name = models.CharField("Soyad", max_length=50)
    tc_kimlik = models.CharField(
        "TC Kimlik No",
        max_length=11,
        validators=[tc_kimlik_validator],
    )
    phone = models.CharField(
        "Telefon",
        max_length=11,
        validators=[phone_validator],
    )
    email = models.EmailField("E-posta", blank=True, null=True)
    school = models.CharField("Okul", max_length=150)
    department = models.CharField("Bölüm", max_length=150, blank=True)
    notes = models.TextField("Açıklama / Not", blank=True)

    class Status(models.TextChoices):
        PENDING = "PENDING", "İncelemede"
        APPROVED = "APPROVED", "Onaylandı"
        REJECTED = "REJECTED", "Reddedildi"

    status = models.CharField(
        "Durum",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tc_kimlik", "phone")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.tc_kimlik}"


class InternLog(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="logs",
    )
    date = models.DateField()
    content = models.TextField("Günlük Özeti")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application} - {self.date}"


class LogReview(models.Model):
    log = models.OneToOneField(
        InternLog,
        on_delete=models.CASCADE,
        related_name="review",
    )
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField("Puan", default=0)
    comment = models.TextField("Yorum", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Değerlendirme: {self.log} ({self.score})"


class Log(models.Model):
    intern = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="intern_logs",
    )
    date = models.DateField(auto_now_add=True)
    content = models.TextField()

    score = models.PositiveSmallIntegerField(null=True, blank=True)
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_logs",
    )

    def __str__(self):
        # User modelinde username alanı olduğunu varsayıyoruz
        return f"{self.intern} - {self.date}"


class InternApplication(models.Model):
    STATUS_CHOICES = [
        ("pending", "Beklemede"),
        ("approved", "Onaylandı"),
        ("rejected", "Reddedildi"),
    ]

    first_name = models.CharField("Ad", max_length=30)
    last_name = models.CharField("Soyad", max_length=30)
    tc_no = models.CharField(
        "TC Kimlik No",
        max_length=11,
        unique=True,
        validators=[tc_kimlik_validator],
    )
    phone = models.CharField("Telefon", max_length=15)
    email = models.EmailField("E-posta", blank=True)
    school = models.CharField("Okul", max_length=100)
    department = models.CharField("Bölüm", max_length=100)
    grade = models.CharField("Sınıf", max_length=20, blank=True)
    start_date = models.DateField("Başlangıç Tarihi", null=True, blank=True)
    end_date = models.DateField("Bitiş Tarihi", null=True, blank=True)
    cv_file = models.FileField("CV", upload_to="intern_cvs/", null=True, blank=True)

    status = models.CharField(
        "Durum",
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending",
    )
    created_at = models.DateTimeField("Başvuru Tarihi", auto_now_add=True)

    # ✅ Otomatik hesap alanları
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="intern_application",
        verbose_name="Oluşturulan Kullanıcı",
    )
    account_created_at = models.DateTimeField("Hesap Oluşturulma", null=True, blank=True)
    credentials_sent = models.BooleanField("Bilgiler iletildi", default=False)
    must_change_password = models.BooleanField("İlk girişte şifre değişimi zorunlu", default=False)
    supervisor = models.ForeignKey(
        "PersonnelProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="intern_applications",
        verbose_name="Sorumlu Personel",
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.tc_no}"


class DailyLog(models.Model):
    application = models.ForeignKey(
        InternApplication,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="Staj Başvurusu",
    )
    date = models.DateField("Gün")
    task_focus = models.CharField("Odak Görev", max_length=120, blank=True)
    summary = models.TextField("Günlük Özeti")
    tomorrow_plan = models.TextField("Yarınki Plan", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        unique_together = ("application", "date")

    def __str__(self):
        return f"{self.application.tc_no} - {self.date}"


class Review(models.Model):
    log = models.ForeignKey(
        DailyLog,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Günlük",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Değerlendiren Personel",
    )
    score = models.PositiveSmallIntegerField("Puan", default=0)
    comment = models.TextField("Yorum", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.log} - {self.score}"


class PersonnelProfile(models.Model):
    first_name = models.CharField("Ad", max_length=50)
    last_name = models.CharField("Soyad", max_length=50)
    email = models.EmailField("E-posta", blank=True)
    phone = models.CharField("Telefon", max_length=15, blank=True)
    title = models.CharField("Görev / Ünvan", max_length=80, blank=True)
    is_active = models.BooleanField("Aktif", default=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="personnel_profile",
        verbose_name="Oluşturulan Kullanıcı",
    )
    account_created_at = models.DateTimeField("Hesap Oluşturulma", null=True, blank=True)

    class Meta:
        ordering = ["first_name", "last_name"]
        verbose_name = "Personel Hesabı"
        verbose_name_plural = "Personel Hesapları"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Announcement(models.Model):
    class Target(models.TextChoices):
        ALL = "ALL", "Tüm kullanıcılar"
        INTERN = "INTERN", "Stajyerler"
        STAFF = "STAFF", "Personel"

    title = models.CharField("Başlık", max_length=150)
    message = models.TextField("Mesaj")
    target = models.CharField(
        "Hedef Kitle",
        max_length=10,
        choices=Target.choices,
        default=Target.ALL,
    )
    is_active = models.BooleanField("Aktif", default=True)
    start_date = models.DateField("Yayın Başlangıç Tarihi", null=True, blank=True)
    end_date = models.DateField("Yayın Bitiş Tarihi", null=True, blank=True)
    created_at = models.DateTimeField("Oluşturulma", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Duyuru"
        verbose_name_plural = "Duyurular"

    def __str__(self):
        return self.title

    def is_visible(self):
        if not self.is_active:
            return False
        today = timezone.now().date()
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True


class ConversationMessage(models.Model):
    application = models.ForeignKey(
        InternApplication,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Stajyer Eşleşmesi",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="internship_messages",
        verbose_name="Gönderen",
    )
    message = models.TextField("Mesaj", blank=True)
    attachment = models.FileField("Ek / Görsel", upload_to="intern_messages/", null=True, blank=True)
    created_at = models.DateTimeField("Gönderim Zamanı", auto_now_add=True)
    read_at = models.DateTimeField("Okunma Zamanı", null=True, blank=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Staj Mesajı"
        verbose_name_plural = "Staj Mesajları"

    def __str__(self):
        return f"{self.application} - {self.sender} - {self.created_at:%d.%m.%Y %H:%M}"

    def is_image(self):
        if not self.attachment:
            return False
        return self.attachment.name.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))
