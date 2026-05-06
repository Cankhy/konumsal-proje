from django.conf import settings
from django.core.mail import send_mail


def send_intern_credentials_email(application, username, password):
    if not getattr(application, "email", None):
        return False, "Başvuruda e-posta adresi bulunmuyor."

    if (
        settings.EMAIL_BACKEND.endswith("smtp.EmailBackend")
        and not settings.EMAIL_HOST_USER
    ):
        return False, "EMAIL_HOST_USER tanımlı değil."

    send_mail(
        subject="Konumsal Bilgi Sistemleri | Stajyer Paneli Giriş Bilgileri",
        message=(
            f"Sayın {application.first_name} {application.last_name},\n\n"
            "Konumsal Bilgi Sistemleri staj başvurunuz değerlendirilmiş ve stajyer paneli erişiminiz oluşturulmuştur.\n\n"
            "Sisteme giriş için bilgileriniz aşağıda yer almaktadır:\n"
            f"Kullanıcı Adı: {username}\n"
            f"Geçici Şifre: {password}\n"
            "Stajyer Giriş Adresi: http://127.0.0.1:8000/stajyer-giris/\n\n"
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
