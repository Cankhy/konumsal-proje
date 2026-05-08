from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from website.models import (
    AboutPage,
    ContactInfo,
    ManagedPage,
    ManagedPageSection,
    Project,
    Service,
)


def attach_static_file(instance, field_name, static_path, upload_name):
    field = getattr(instance, field_name)
    if field:
        return

    source = Path(settings.BASE_DIR) / "static" / static_path
    if not source.exists():
        return

    with source.open("rb") as handle:
        field.save(upload_name, File(handle), save=False)


class Command(BaseCommand):
    help = "Konumsal site icin admin yonetilebilir baslangic iceriklerini olusturur."

    def handle(self, *args, **options):
        service_rows = [
            {
                "title": "Coğrafi Bilgi Sistemleri",
                "slug": "cografi-bilgi-sistemleri",
                "short": "Harita tabanlı verilerle kurum süreçlerini akıllı hale getirir.",
                "url": "/hizmetler/cografi-bilgi-sistemleri/",
                "image": "images/solution-cbs.jpg",
            },
            {
                "title": "Kurumsal Kaynak Planlama",
                "slug": "kurumsal-kaynak-planlama",
                "short": "Kurum içi süreçleri tek merkezden planlayan ERP çözümleri.",
                "url": "/hizmetler/kurumsal-kaynak-planlama/",
                "image": "images/solution-erp.jpg",
            },
            {
                "title": "Siber Güvenlik Sistemleri",
                "slug": "siber-guvenlik-sistemleri",
                "short": "Veri, ağ ve uygulama güvenliğini bütüncül biçimde koruyan çözümler.",
                "url": "/hizmetler/siber-guvenlik-sistemleri/",
                "image": "images/solution-siber.jpg",
            },
            {
                "title": "Üniversite Yönetim Sistemi",
                "slug": "universite-yonetim-sistemi",
                "short": "Akademik ve idari süreçleri dijitalleştiren bütünleşik yönetim yapısı.",
                "url": "/hizmetler/universite-yonetim-sistemi/",
                "image": "images/solution-universite.jpg",
            },
            {
                "title": "Veri Sayısallaştırma",
                "slug": "veri-sayisallastirma",
                "short": "Arşiv, evrak ve saha verilerini kullanılabilir dijital kayıtlara dönüştürür.",
                "url": "/hizmetler/veri-sayisallastirma/",
                "image": "images/solution-veri.jpg",
            },
            {
                "title": "Mobil Uygulamalar",
                "slug": "mobil-uygulamalar",
                "short": "Saha ve vatandaş etkileşimi için hızlı, güvenli mobil uygulamalar.",
                "url": "/hizmetler/mobil-uygulamalar/",
                "image": "images/solution-mobil.jpg",
            },
            {
                "title": "Elektronik Doküman Yönetim Sistemi",
                "slug": "elektronik-dokuman-yonetim-sistemi",
                "short": "Belge akışını, onay süreçlerini ve kurumsal arşivi düzenler.",
                "url": "/hizmetler/elektronik-dokuman-yonetim-sistemi/",
                "image": "images/solution-edys.jpg",
            },
            {
                "title": "Görev Yönetim Sistemi",
                "slug": "gorev-yonetim-sistemi",
                "short": "Ekip görevlerini, takip adımlarını ve raporlamayı tek yerde toplar.",
                "url": "/hizmetler/gorev-yonetim-sistemi/",
                "image": "images/solution-gorev.jpg",
            },
        ]

        for index, row in enumerate(service_rows, start=1):
            service, _ = Service.objects.update_or_create(
                slug=row["slug"],
                defaults={
                    "title": row["title"],
                    "short_description": row["short"],
                    "description": row["short"],
                    "detail_url": row["url"],
                    "order": index,
                    "is_active": True,
                },
            )
            attach_static_file(service, "image", row["image"], f"{row['slug']}.jpg")
            service.save()

        project_rows = [
            {
                "title": "Orman Bilgi Sistemi",
                "slug": "orman-bilgi-sistemi",
                "client": "Kamu Kurumu",
                "summary": "Orman varlıklarının dijital takibi ve kurumsal süreç yönetimi.",
                "url": "/projeler/orman-bilgi-sistemi/",
                "image": "images/orman.png",
            },
            {
                "title": "Milli Emlak Otomasyon Sistemi",
                "slug": "milli-emlak-otomasyon-sistemi",
                "client": "Kamu Kurumu",
                "summary": "Taşınmaz yönetimi, başvuru ve süreç takibi için otomasyon altyapısı.",
                "url": "/projeler/milli-emlak-otomasyon-sistemi/",
                "image": "images/meop.png",
            },
            {
                "title": "Hava Emisyon Yönetim Portalı",
                "slug": "hava-emisyon-yonetim-hey-portali",
                "client": "Kamu Kurumu",
                "summary": "Hava emisyon süreçlerini izleyen, raporlayan ve yöneten portal.",
                "url": "/projeler/hava-emisyon-yonetim-hey-portali/",
                "image": "images/hey.png",
            },
        ]

        for index, row in enumerate(project_rows, start=1):
            project, _ = Project.objects.update_or_create(
                slug=row["slug"],
                defaults={
                    "title": row["title"],
                    "client": row["client"],
                    "summary": row["summary"],
                    "description": row["summary"],
                    "detail_url": row["url"],
                    "order": index,
                    "is_active": True,
                    "is_featured": True,
                },
            )
            attach_static_file(project, "image", row["image"], f"{row['slug']}.png")
            project.save()

        AboutPage.objects.update_or_create(
            pk=1,
            defaults={
                "title": "Hakkımızda",
                "hero_title": "Konumsal Bilgi Sistemleri",
                "hero_subtitle": "Kurumların dijital dönüşüm, harita tabanlı yönetim ve yazılım ihtiyaçlarına profesyonel çözümler sunuyoruz.",
                "content": (
                    "Konumsal Bilgi Sistemleri; coğrafi bilgi sistemleri, kurumsal yazılımlar, "
                    "veri yönetimi, mobil uygulamalar ve güvenlik alanlarında kurumlara uçtan uca "
                    "çözüm geliştiren bir teknoloji firmasıdır.\n\n"
                    "Hedefimiz; karmaşık süreçleri sade, ölçülebilir ve güvenilir dijital sistemlere "
                    "dönüştürerek kurumların karar alma gücünü artırmaktır."
                ),
            },
        )

        ContactInfo.objects.update_or_create(
            pk=1,
            defaults={
                "company_name": "Konumsal Bilgi Sistemleri",
                "address": "Cyberpark Tepe Binası No:19-31 Bilkent / ANKARA",
                "phone": "(0312) 266 39 39",
                "email": "bilgi@konumsal.com.tr",
            },
        )

        page_rows = [
            ("/hizmetler/cografi-bilgi-sistemleri/", "cbs", "Coğrafi Bilgi Sistemleri", "Hizmet", "images/cbs/section1.jpg"),
            ("/hizmetler/kurumsal-kaynak-planlama/", "erp", "Kurumsal Kaynak Planlama", "Hizmet", "images/erp/hero.jpg"),
            ("/hizmetler/siber-guvenlik-sistemleri/", "siber", "Siber Güvenlik Sistemleri", "Hizmet", "images/siber/section1.jpg"),
            ("/hizmetler/universite-yonetim-sistemi/", "universite", "Üniversite Yönetim Sistemi", "Hizmet", "images/uys/hero.jpg"),
            ("/hizmetler/veri-sayisallastirma/", "veri", "Veri Sayısallaştırma", "Hizmet", "images/veri/hero.jpg"),
            ("/hizmetler/mobil-uygulamalar/", "mobil", "Mobil Uygulamalar", "Hizmet", "images/mobil/hero.jpg"),
            ("/hizmetler/elektronik-dokuman-yonetim-sistemi/", "edys", "Elektronik Doküman Yönetim Sistemi", "Hizmet", "images/edys/hero.jpg"),
            ("/hizmetler/gorev-yonetim-sistemi/", "gorev", "Görev Yönetim Sistemi", "Hizmet", "images/gorev/hero.jpg"),
            ("/projeler/orman-bilgi-sistemi/", "orman", "Orman Bilgi Sistemi", "Proje", "images/proje-orman-hero.jpg"),
            ("/projeler/milli-emlak-otomasyon-sistemi/", "meop", "Milli Emlak Otomasyon Sistemi", "Proje", "images/proje-meop-hero.png"),
            ("/projeler/hava-emisyon-yonetim-hey-portali/", "hey", "Hava Emisyon Yönetim Portalı", "Proje", "images/proje-hey-hero.avif"),
        ]

        for index, (path, slug, title, eyebrow, image) in enumerate(page_rows, start=1):
            page, _ = ManagedPage.objects.update_or_create(
                slug=slug,
                defaults={
                    "path": path,
                    "title": title,
                    "page_type": "project" if eyebrow == "Proje" else "service",
                    "eyebrow": eyebrow,
                    "summary": f"{title} için kurumsal ihtiyaçlara göre ölçeklenebilir, güvenilir ve yönetilebilir çözüm yapısı.",
                    "body": (
                        f"{title}, kurumların operasyonel süreçlerini daha düzenli, takip edilebilir "
                        "ve raporlanabilir hale getirmek için tasarlanmıştır.\n\n"
                        "Bu içerik admin panelindeki Yönetilebilir Sayfalar bölümünden değiştirilebilir; "
                        "başlık, açıklama, görsel, bölüm içerikleri ve butonlar aynı ekrandan güncellenebilir."
                    ),
                    "primary_button_text": "İletişime Geç",
                    "primary_button_url": "/iletisim/",
                    "order": index,
                    "is_active": True,
                },
            )
            attach_static_file(page, "hero_image", image, f"{slug}-hero{Path(image).suffix}")
            page.save()
            ManagedPageSection.objects.get_or_create(
                page=page,
                title="Kurumsal Kullanım",
                defaults={
                    "content": "Sistem, kurumun mevcut iş akışına göre yapılandırılır ve ihtiyaç oldukça genişletilebilir.",
                    "order": 1,
                    "is_active": True,
                },
            )
            ManagedPageSection.objects.get_or_create(
                page=page,
                title="Yönetilebilir İçerik",
                defaults={
                    "content": "Bu sayfanın bölümleri, görselleri ve metinleri Django admin panelinden hızlıca güncellenebilir.",
                    "order": 2,
                    "is_active": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("Site icerikleri admin icin hazirlandi."))
