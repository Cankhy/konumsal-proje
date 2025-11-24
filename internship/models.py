from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator  # ✅ BUNU EKLİYORUZ

User = settings.AUTH_USER_MODEL

# ✅ TC kimlik ve telefon için validator'lar (GLOBAL, en üstte olacak)
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
        validators=[tc_kimlik_validator],   # ✅ buraya
    )
    phone = models.CharField(
        "Telefon",
        max_length=11,
        validators=[phone_validator],       # ✅ buraya
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
        Application, on_delete=models.CASCADE, related_name="logs"
    )
    date = models.DateField()
    content = models.TextField("Günlük Özeti")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.application} - {self.date}"


class LogReview(models.Model):
    log = models.OneToOneField(
        InternLog, on_delete=models.CASCADE, related_name="review"
    )
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField("Puan", default=0)
    comment = models.TextField("Yorum", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Değerlendirme: {self.log} ({self.score})"
    
    from django.contrib.auth.models import User

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
        return f"{self.intern.username} - {self.date}"
    tc_kimlik_validator = RegexValidator(
    regex=r'^\d{11}$',
    message='TC Kimlik numarası 11 haneli, sadece rakam olmalıdır.'
)


class InternApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('approved', 'Onaylandı'),
        ('rejected', 'Reddedildi'),
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

    status = models.CharField(
        "Durum",
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
    )
    created_at = models.DateTimeField("Başvuru Tarihi", auto_now_add=True)

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
    summary = models.TextField("Günlük Özeti")
    created_at = models.DateTimeField(auto_now_add=True)

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


