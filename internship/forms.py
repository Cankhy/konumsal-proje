from django import forms
from django.core.exceptions import ValidationError

from .file_security import DOCUMENT_RULES, PDF_RULE, allowed_accept_value, validate_uploaded_file
from .models import (
    Application,
    DailyLog,
    FormErrorLog,
    InternApplication,
    InternDocument,
    InternLog,
    PersonnelTask,
    PersonnelTaskComment,
    Review,
)


GRADE_CHOICES = [
    ("", "Sınıf seçin"),
    ("1. Sınıf", "1. Sınıf"),
    ("2. Sınıf", "2. Sınıf"),
    ("3. Sınıf", "3. Sınıf"),
    ("4. Sınıf", "4. Sınıf"),
    ("Mezun", "Mezun"),
]

DAILY_TASK_CHOICES = [
    ("", "Bugünkü odak görevi seçin"),
    ("Oryantasyon ve kurum tanıma", "Oryantasyon ve kurum tanıma"),
    ("Temel araç kurulumu", "Temel araç kurulumu"),
    ("Kod okuma ve dokümantasyon", "Kod okuma ve dokümantasyon"),
    ("Küçük geliştirme görevi", "Küçük geliştirme görevi"),
    ("Test ve hata kontrolü", "Test ve hata kontrolü"),
    ("Raporlama ve sunum hazırlığı", "Raporlama ve sunum hazırlığı"),
]


def log_form_errors(form_name, path, payload, errors):
    FormErrorLog.objects.create(
        form_name=form_name,
        path=path,
        payload=payload,
        errors=errors,
    )


class InternApplicationForm(forms.ModelForm):
    class Meta:
        model = InternApplication
        fields = [
            "first_name",
            "last_name",
            "tc_no",
            "phone",
            "email",
            "school",
            "department",
            "grade",
            "start_date",
            "end_date",
            "cv_file",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Adınızı yazın"}),
            "last_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Soyadınızı yazın"}),
            "tc_no": forms.TextInput(attrs={"class": "form-input", "placeholder": "11 haneli TC Kimlik No"}),
            "phone": forms.TextInput(attrs={"class": "form-input", "placeholder": "Telefon numaranız"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": "ornek@mail.com"}),
            "school": forms.HiddenInput(attrs={"data-education-school": "true"}),
            "department": forms.HiddenInput(attrs={"data-education-department": "true"}),
            "grade": forms.Select(attrs={"class": "form-select"}, choices=GRADE_CHOICES),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "cv_file": forms.ClearableFileInput(
                attrs={"class": "form-input", "accept": allowed_accept_value(PDF_RULE)}
            ),
        }

    def clean_first_name(self):
        return (self.cleaned_data["first_name"] or "").strip().title()

    def clean_last_name(self):
        return (self.cleaned_data["last_name"] or "").strip().title()

    def clean_tc_no(self):
        tc_no = "".join(ch for ch in (self.cleaned_data.get("tc_no") or "") if ch.isdigit())
        if len(tc_no) != 11:
            raise ValidationError("TC Kimlik numarası 11 haneli olmalıdır.")

        existing = InternApplication.objects.filter(tc_no=tc_no).first()
        if existing:
            status_labels = {
                "pending": "inceleme aşamasında",
                "approved": "onaylanmış",
                "rejected": "değerlendirilmiş",
            }
            status_text = status_labels.get(existing.status, "kayıtlı")
            raise ValidationError(
                f"Bu TC Kimlik numarası ile daha önce {status_text} bir başvuru bulunmaktadır. "
                "Durumu sorgulama ekranından kontrol edebilirsiniz."
            )
        return tc_no

    def clean_phone(self):
        phone = "".join(ch for ch in (self.cleaned_data.get("phone") or "") if ch.isdigit())
        if len(phone) not in (10, 11):
            raise ValidationError("Telefon numarası 10 veya 11 haneli olmalıdır.")
        return phone

    def clean_cv_file(self):
        cv_file = self.cleaned_data.get("cv_file")
        validate_uploaded_file(cv_file, PDF_RULE)
        return cv_file

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Bitiş tarihi, başlangıç tarihinden önce olamaz.")
        return cleaned_data


class ApplicationSearchForm(forms.Form):
    tc_no = forms.CharField(
        label="TC Kimlik No",
        max_length=11,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "11 haneli TC Kimlik No"}),
    )
    phone = forms.CharField(
        label="Telefon",
        max_length=11,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Başvurudaki telefon"}),
    )

    def clean_tc_no(self):
        tc_no = "".join(ch for ch in (self.cleaned_data.get("tc_no") or "") if ch.isdigit())
        if len(tc_no) != 11:
            raise ValidationError("TC Kimlik numarası 11 haneli olmalıdır.")
        return tc_no

    def clean_phone(self):
        phone = "".join(ch for ch in (self.cleaned_data.get("phone") or "") if ch.isdigit())
        if len(phone) not in (10, 11):
            raise ValidationError("Telefon numarası 10 veya 11 haneli olmalıdır.")
        return phone


class DailyLogForm(forms.ModelForm):
    def __init__(self, *args, task_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if task_choices:
            self.fields["task_focus"].widget.choices = task_choices
            self.fields["task_focus"].choices = task_choices

    class Meta:
        model = DailyLog
        fields = ["date", "task_focus", "summary", "tomorrow_plan"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "task_focus": forms.Select(attrs={"class": "form-select"}, choices=DAILY_TASK_CHOICES),
            "summary": forms.Textarea(
                attrs={"class": "form-textarea", "rows": 4, "placeholder": "Bugün yaptığınız çalışmaları yazın"}
            ),
            "tomorrow_plan": forms.Textarea(
                attrs={"class": "form-textarea", "rows": 3, "placeholder": "Yarın hangi işi tamamlamayı planlıyorsunuz?"}
            ),
        }

    def clean_summary(self):
        summary = (self.cleaned_data.get("summary") or "").strip()
        if len(summary) < 20:
            raise ValidationError("Günlük özeti en az 20 karakter olmalıdır.")
        return summary


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["score", "comment"]
        widgets = {
            "score": forms.NumberInput(attrs={"class": "form-input", "min": 0, "max": 100}),
            "comment": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
        }


class PersonnelTaskForm(forms.ModelForm):
    class Meta:
        model = PersonnelTask
        fields = ["title", "details", "task_date", "due_date", "priority"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Bugün şu modülü incele, şu düzeltmeyi yap gibi kısa görev başlığı",
                }
            ),
            "details": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "rows": 4,
                    "placeholder": "Görev detayını, beklediğiniz çıktıyı ve teslim notunu yazın",
                }
            ),
            "task_date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "due_date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned = super().clean()
        task_date = cleaned.get("task_date")
        due_date = cleaned.get("due_date")
        if task_date and due_date and due_date < task_date:
            raise ValidationError("Teslim tarihi görev gününden önce olamaz.")
        return cleaned


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = PersonnelTaskComment
        fields = ["comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={"class": "form-textarea", "rows": 3, "placeholder": "Görev için kısa not veya geri bildirim yazın"}
            )
        }


class InternDocumentUploadForm(forms.ModelForm):
    class Meta:
        model = InternDocument
        fields = ["category", "file"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-input"}),
        }

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        category = self.cleaned_data.get("category") or self.data.get("category")
        if category not in DOCUMENT_RULES:
            raise ValidationError("Geçersiz belge türü seçildi.")
        validate_uploaded_file(uploaded_file, DOCUMENT_RULES[category])
        return uploaded_file


class DocumentReviewForm(forms.ModelForm):
    class Meta:
        model = InternDocument
        fields = ["status", "personnel_note", "reupload_requested"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "personnel_note": forms.Textarea(
                attrs={"class": "form-textarea", "rows": 3, "placeholder": "Belge ile ilgili not yazın"}
            ),
            "reupload_requested": forms.CheckboxInput(attrs={"class": "h-4 w-4 rounded border-slate-300"}),
        }


class ApplicationBulkActionForm(forms.Form):
    action = forms.ChoiceField(
        choices=(
            ("approve", "Seçilileri Onayla"),
            ("reject", "Seçilileri Reddet"),
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-textarea", "rows": 2, "placeholder": "Toplu işlem notu veya red nedeni"}
        ),
    )
    application_ids = forms.CharField(required=False, widget=forms.HiddenInput())


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["first_name", "last_name", "tc_kimlik", "phone", "email", "school", "department", "notes"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Adınızı yazın"}),
            "last_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Soyadınızı yazın"}),
            "tc_kimlik": forms.TextInput(attrs={"class": "form-input", "placeholder": "11 haneli TC Kimlik No"}),
            "phone": forms.TextInput(attrs={"class": "form-input", "placeholder": "Telefon numaranız"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": "ornek@mail.com"}),
            "school": forms.TextInput(attrs={"class": "form-input", "placeholder": "Okul adınız"}),
            "department": forms.TextInput(attrs={"class": "form-input", "placeholder": "Bölümünüz"}),
            "notes": forms.Textarea(attrs={"class": "form-textarea", "rows": 4, "placeholder": "Eklemek istediğiniz not"}),
        }


class InternLogForm(forms.ModelForm):
    class Meta:
        model = InternLog
        fields = ["application", "date", "content"]
        widgets = {
            "application": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "content": forms.Textarea(attrs={"class": "form-textarea", "rows": 4, "placeholder": "Günlük içeriğini yazın"}),
        }


ApplicationQueryForm = ApplicationSearchForm
