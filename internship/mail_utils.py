from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse


def _build_absolute_url(route_name):
    return f"{settings.APP_BASE_URL}{reverse(route_name)}"


def send_intern_credentials_email(application, username, password):
    if not getattr(application, "email", None):
        return False, "Başvuruda e-posta adresi bulunmuyor."

    if (
        settings.EMAIL_BACKEND.endswith("smtp.EmailBackend")
        and not settings.EMAIL_HOST_USER
    ):
        return False, "EMAIL_HOST_USER tanımlı değil."

    login_url = _build_absolute_url("website:intern_login")

    send_mail(
        subject="Konumsal Bilgi Sistemleri | Stajyer Paneli Giriş Bilgileri",
        message=(
            f"Sayın {application.first_name} {application.last_name},\n\n"
            "Konumsal Bilgi Sistemleri staj başvurunuz değerlendirilmiş ve stajyer paneli erişiminiz oluşturulmuştur.\n\n"
            "Sisteme giriş için bilgileriniz aşağıda yer almaktadır:\n"
            f"Kullanıcı Adı: {username}\n"
            f"Geçici Şifre: {password}\n"
            f"Stajyer Giriş Adresi: {login_url}\n\n"
            "Güvenlik gereği, ilk girişinizin ardından şifrenizi değiştirmeniz zorunludur. "
            "Şifre değişikliği tamamlanmadan stajyer panelindeki diğer ekranlara erişim sağlanamaz.\n\n"
            "Destek veya erişim sorunu yaşamanız halinde bizimle iletişime geçebilirsiniz:\n"
            "E-posta: bilgi@konumsal.com.tr\n"
            "Telefon: (0312) 266 39 39\n\n"
            "Bilgilerinize sunar, başarılı bir staj dönemi dileriz.\n\n"
            "Konumsal Bilgi Sistemleri"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[application.email],
        fail_silently=False,
    )
    return True, None


def send_personnel_credentials_email(profile, username, password):
    if not getattr(profile, "email", None):
        return False, "Personel kaydında e-posta adresi bulunmuyor."

    if (
        settings.EMAIL_BACKEND.endswith("smtp.EmailBackend")
        and not settings.EMAIL_HOST_USER
    ):
        return False, "EMAIL_HOST_USER tanımlı değil."

    login_url = _build_absolute_url("website:login_select")

    send_mail(
        subject="Konumsal Bilgi Sistemleri | Personel Hesap Bilgileri",
        message=(
            f"Sayın {profile.first_name} {profile.last_name},\n\n"
            "Personel paneli hesabınız oluşturulmuştur.\n\n"
            "Sisteme giriş için bilgileriniz aşağıda yer almaktadır:\n"
            f"Kullanıcı Adı: {username}\n"
            f"Geçici Şifre: {password}\n"
            f"Giriş Adresi: {login_url}\n\n"
            "Güvenlik gereği ilk girişinizin ardından şifrenizi güncellemeniz tavsiye edilir.\n\n"
            "Konumsal Bilgi Sistemleri"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[profile.email],
        fail_silently=False,
    )
    return True, None
