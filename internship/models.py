from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


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
    tc_kimlik = models.CharField("TC Kimlik No", max_length=11, validators=[tc_kimlik_validator])
    phone = models.CharField("Telefon", max_length=11, validators=[phone_validator])
    email = models.EmailField("E-posta", blank=True, null=True)
    school = models.CharField("Okul", max_length=150)
    department = models.CharField("Bölüm", max_length=150, blank=True)
    notes = models.TextField("Açıklama / Not", blank=True)

    class Status(models.TextChoices):
        PENDING = "PENDING", "İncelemede"
        APPROVED = "APPROVED", "Onaylandı"
        REJECTED = "REJECTED", "Reddedildi"

    status = models.CharField("Durum", max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tc_kimlik", "phone")
        ordering = ["-created_at"]
        verbose_name = "Eski Başvuru"
        verbose_name_plural = "Eski Başvurular"

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.tc_kimlik}"


class InternLog(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="logs")
    date = models.DateField()
    content = models.TextField("Günlük Özeti")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Eski Staj Günlüğü"
        verbose_name_plural = "Eski Staj Günlükleri"

    def __str__(self):
        return f"{self.application} - {self.date}"


class LogReview(models.Model):
    log = models.OneToOneField(InternLog, on_delete=models.CASCADE, related_name="review")
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField("Puan", default=0)
    comment = models.TextField("Yorum", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Eski Günlük Değerlendirmesi"
        verbose_name_plural = "Eski Günlük Değerlendirmeleri"

    def __str__(self):
        return f"Değerlendirme: {self.log} ({self.score})"


class Log(models.Model):
    intern = models.ForeignKey(User, on_delete=models.CASCADE, related_name="intern_logs")
    date = models.DateField(auto_now_add=True)
    content = models.TextField()
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_logs")

    class Meta:
        ordering = ["-date"]
        verbose_name = "Günlük Kaydı"
        verbose_name_plural = "Günlük Kayıtları"

    def __str__(self):
        return f"{self.intern} - {self.date}"


class PersonnelProfile(models.Model):
    first_name = models.CharField("Ad", max_length=50)
    last_name = models.CharField("Soyad", max_length=50)
    email = models.EmailField("E-posta", blank=True)
    phone = models.CharField("Telefon", max_length=15, blank=True)
    identity_number = models.CharField("TC Kimlik No", max_length=11, blank=True)
    title = models.CharField("Görev / Ünvan", max_length=80, blank=True)
    profile_avatar = models.FileField("Profil Fotoğrafı", upload_to="profile_avatars/personnel/", blank=True)
    leave_entitlement_days = models.DecimalField("İzin Hakkı (Gün)", max_digits=5, decimal_places=1, default=56)
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


class InternApplication(models.Model):
    STATUS_CHOICES = [
        ("pending", "Beklemede"),
        ("approved", "Onaylandı"),
        ("rejected", "Reddedildi"),
    ]

    first_name = models.CharField("Ad", max_length=30)
    last_name = models.CharField("Soyad", max_length=30)
    tc_no = models.CharField("TC Kimlik No", max_length=11, unique=True, validators=[tc_kimlik_validator])
    phone = models.CharField("Telefon", max_length=15)
    email = models.EmailField("E-posta", blank=True)
    school = models.CharField("Okul", max_length=100)
    department = models.CharField("Bölüm", max_length=100)
    grade = models.CharField("Sınıf", max_length=20, blank=True)
    start_date = models.DateField("Başlangıç Tarihi", null=True, blank=True)
    end_date = models.DateField("Bitiş Tarihi", null=True, blank=True)
    cv_file = models.FileField("CV", upload_to="intern_cvs/", null=True, blank=True)
    profile_avatar = models.FileField("Profil Fotoğrafı", upload_to="profile_avatars/interns/", blank=True)
    status = models.CharField("Durum", max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField("Başvuru Tarihi", auto_now_add=True)
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
    rejection_reason = models.TextField("Red Nedeni", blank=True)
    status_updated_at = models.DateTimeField("Durum Güncelleme", auto_now=True)
    supervisor = models.ForeignKey(
        PersonnelProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="intern_applications",
        verbose_name="Sorumlu Personel",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Staj Başvurusu"
        verbose_name_plural = "Staj Başvuruları"

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
        verbose_name = "Staj Günlüğü"
        verbose_name_plural = "Staj Günlükleri"

    def __str__(self):
        return f"{self.application.tc_no} - {self.date}"


class PersonnelTask(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Düşük"
        MEDIUM = "medium", "Orta"
        HIGH = "high", "Yüksek"

    application = models.ForeignKey(
        InternApplication,
        on_delete=models.CASCADE,
        related_name="personnel_tasks",
        verbose_name="Stajyer Eşleşmesi",
    )
    personnel = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.CASCADE,
        related_name="assigned_tasks",
        verbose_name="Görevi Veren Personel",
    )
    title = models.CharField("Görev Başlığı", max_length=140)
    details = models.TextField("Görev Açıklaması", blank=True)
    task_date = models.DateField("Görev Günü", default=timezone.localdate)
    due_date = models.DateField("Teslim Tarihi", null=True, blank=True)
    priority = models.CharField("Öncelik", max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    is_active = models.BooleanField("Aktif", default=True)
    is_completed = models.BooleanField("Tamamlandı", default=False)
    completed_at = models.DateTimeField("Tamamlanma", null=True, blank=True)
    created_at = models.DateTimeField("Oluşturulma", auto_now_add=True)

    class Meta:
        ordering = ["task_date", "-created_at"]
        verbose_name = "Personel Görevi"
        verbose_name_plural = "Personel Görevleri"

    def __str__(self):
        return f"{self.application} - {self.title}"


class PersonnelTaskComment(models.Model):
    task = models.ForeignKey(PersonnelTask, on_delete=models.CASCADE, related_name="comments", verbose_name="Görev")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="task_comments", verbose_name="Yazan")
    comment = models.TextField("Yorum")
    created_at = models.DateTimeField("Oluşturulma", auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Görev Yorumu"
        verbose_name_plural = "Görev Yorumları"

    def __str__(self):
        return f"{self.task} - {self.author}"


class PersonnelLeaveRequest(models.Model):
    class LeaveType(models.TextChoices):
        ANNUAL = "annual", "Yıllık"
        EXCUSE = "excuse", "Mazeret"
        BIRTH = "birth", "Doğum"
        UNPAID = "unpaid", "Ücretsiz"
        HOURLY = "hourly", "Saatlik"

    class Status(models.TextChoices):
        PENDING = "pending", "Beklemede"
        APPROVED = "approved", "Onaylandı"
        REJECTED = "rejected", "Reddedildi"

    personnel = models.ForeignKey(
        PersonnelProfile,
        on_delete=models.CASCADE,
        related_name="leave_requests",
        verbose_name="Personel",
    )
    full_name = models.CharField("Ad Soyad", max_length=120)
    identity_number = models.CharField("TC Kimlik No", max_length=11, blank=True)
    job_title = models.CharField("Unvan", max_length=120, blank=True)
    leave_type = models.CharField("İzin Türü", max_length=20, choices=LeaveType.choices)
    start_date = models.DateField("Başlangıç")
    end_date = models.DateField("Bitiş")
    duration_value = models.DecimalField("Süre", max_digits=5, decimal_places=1)
    duration_unit = models.CharField("Süre Birimi", max_length=10, default="gun")
    return_date = models.DateField("Göreve Dönüş Tarihi")
    reason = models.CharField("Gerekçe", max_length=255)
    address = models.CharField("Adres", max_length=255, blank=True)
    status = models.CharField("Onay", max_length=12, choices=Status.choices, default=Status.PENDING)
    status_note = models.TextField("Durum Notu", blank=True)
    created_at = models.DateTimeField("Oluşturulma", auto_now_add=True)
    updated_at = models.DateTimeField("Güncellenme", auto_now=True)
    reviewed_at = models.DateTimeField("İncelenme", null=True, blank=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]
        verbose_name = "Personel İzin Talebi"
        verbose_name_plural = "Personel İzin Talepleri"

    def __str__(self):
        return f"{self.full_name} - {self.get_leave_type_display()} - {self.start_date:%d.%m.%Y}"


class Review(models.Model):
    log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name="reviews", verbose_name="Günlük")
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

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Günlük Değerlendirmesi"
        verbose_name_plural = "Günlük Değerlendirmeleri"

    def __str__(self):
        return f"{self.log} - {self.score}"


class Announcement(models.Model):
    class Target(models.TextChoices):
        ALL = "ALL", "Tüm kullanıcılar"
        INTERN = "INTERN", "Stajyerler"
        STAFF = "STAFF", "Personel"

    title = models.CharField("Başlık", max_length=150)
    message = models.TextField("Mesaj")
    target = models.CharField("Hedef Kitle", max_length=10, choices=Target.choices, default=Target.ALL)
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


class InternDocument(models.Model):
    class Category(models.TextChoices):
        INTERN_AGREEMENT = "intern_agreement", "Staj Sözleşmesi"
        DAILY_FORM = "daily_form", "İmzalı Günlük Formu"
        REPORT = "report", "Staj Raporu"
        PRESENTATION = "presentation", "Sunum Dosyası"

    class Status(models.TextChoices):
        PENDING = "pending", "Bekliyor"
        APPROVED = "approved", "Onaylandı"
        MISSING = "missing", "Eksik"

    application = models.ForeignKey(
        InternApplication,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Staj Başvurusu",
    )
    category = models.CharField("Belge Türü", max_length=30, choices=Category.choices)
    file = models.FileField("Belge Dosyası", upload_to="intern_documents/")
    status = models.CharField("Durum", max_length=10, choices=Status.choices, default=Status.PENDING)
    personnel_note = models.TextField("Personel Notu", blank=True)
    reupload_requested = models.BooleanField("Tekrar Yükleme İstendi", default=False)
    uploaded_at = models.DateTimeField("Yüklenme", auto_now_add=True)
    reviewed_at = models.DateTimeField("İncelenme", null=True, blank=True)

    class Meta:
        ordering = ["category", "-uploaded_at"]
        verbose_name = "Staj Belgesi"
        verbose_name_plural = "Staj Belgeleri"

    def __str__(self):
        return f"{self.application} - {self.get_category_display()}"


class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(
        InternApplication,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="Staj Başvurusu",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="application_history_entries",
        verbose_name="İşlemi Yapan",
    )
    from_status = models.CharField("Eski Durum", max_length=10, blank=True)
    to_status = models.CharField("Yeni Durum", max_length=10)
    note = models.TextField("Not", blank=True)
    created_at = models.DateTimeField("Kayıt Zamanı", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Başvuru Geçmişi"
        verbose_name_plural = "Başvuru Geçmişi"

    def __str__(self):
        return f"{self.application} - {self.to_status}"


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
    attachment_kind = models.CharField("Ek Türü", max_length=20, blank=True)
    created_at = models.DateTimeField("Gönderim Zamanı", auto_now_add=True)
    edited_at = models.DateTimeField("Düzenlenme", null=True, blank=True)
    deleted_at = models.DateTimeField("Silinme", null=True, blank=True)
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


class FormErrorLog(models.Model):
    form_name = models.CharField("Form", max_length=80)
    path = models.CharField("Yol", max_length=240)
    payload = models.JSONField("Veri", default=dict, blank=True)
    errors = models.JSONField("Hatalar", default=dict, blank=True)
    created_at = models.DateTimeField("Kayıt Zamanı", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Form Hata Kaydı"
        verbose_name_plural = "Form Hata Kayıtları"

    def __str__(self):
        return f"{self.form_name} - {self.path}"
