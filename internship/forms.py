from django import forms
from .models import InternApplication, DailyLog, Review, Application, InternLog


class InternApplicationForm(forms.ModelForm):
    """Stajyer başvuru formu (yeni InternApplication modeli)"""

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
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
            "tc_no": forms.TextInput(attrs={"class": "form-input"}),
            "phone": forms.TextInput(attrs={"class": "form-input"}),
            "email": forms.EmailInput(attrs={"class": "form-input"}),
            "school": forms.TextInput(attrs={"class": "form-input"}),
            "department": forms.TextInput(attrs={"class": "form-input"}),
            "grade": forms.TextInput(attrs={"class": "form-input"}),
            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "end_date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
        }


class ApplicationSearchForm(forms.Form):
    """TC + Telefon ile başvuru sorgulama formu (InternApplication için)"""

    tc_no = forms.CharField(
        label="TC Kimlik No",
        max_length=11,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    phone = forms.CharField(
        label="Telefon",
        max_length=11,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )


class DailyLogForm(forms.ModelForm):
    """Stajyer günlük girişi formu (InternApplication'a bağlı DailyLog)"""

    class Meta:
        model = DailyLog
        fields = ["date", "summary"]
        widgets = {
            "date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "summary": forms.Textarea(
                attrs={"class": "form-textarea", "rows": 4}
            ),
        }


class ReviewForm(forms.ModelForm):
    """Personel değerlendirme formu (DailyLog için Review)"""

    class Meta:
        model = Review
        fields = ["score", "comment"]
        widgets = {
            "score": forms.NumberInput(
                attrs={"class": "form-input", "min": 0, "max": 100}
            ),
            "comment": forms.Textarea(
                attrs={"class": "form-textarea", "rows": 3}
            ),
        }


class ApplicationForm(forms.ModelForm):
    """
    Eski Application modeli için başvuru formu
    (eski HTML ekranları ve eski DRF endpoint'leri bozulmasın diye).
    """

    class Meta:
        model = Application
        fields = [
            "first_name",
            "last_name",
            "tc_kimlik",
            "phone",
            "email",
            "school",
            "department",
            "notes",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
            "tc_kimlik": forms.TextInput(attrs={"class": "form-input"}),
            "phone": forms.TextInput(attrs={"class": "form-input"}),
            "email": forms.EmailInput(attrs={"class": "form-input"}),
            "school": forms.TextInput(attrs={"class": "form-input"}),
            "department": forms.TextInput(attrs={"class": "form-input"}),
            "notes": forms.Textarea(
                attrs={"class": "form-textarea", "rows": 4}
            ),
        }


class InternLogForm(forms.ModelForm):
    """
    Eski Application tablosuna bağlı InternLog modeli için form.
    Eski 3.3 günlük ekranı ve eski API'ler bunu bekliyor.
    """

    class Meta:
        model = InternLog
        fields = ["application", "date", "content"]
        widgets = {
            "application": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(
                attrs={"type": "date", "class": "form-input"}
            ),
            "content": forms.Textarea(
                attrs={"class": "form-textarea", "rows": 4}
            ),
        }


# Eski kodda kullanılan isimle uyum için alias:
ApplicationQueryForm = ApplicationSearchForm
