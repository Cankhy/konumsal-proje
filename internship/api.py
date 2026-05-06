import json

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import ApplicationForm, InternLogForm, InternApplicationForm
from .models import (
    Application,
    InternLog,
    LogReview,
    InternApplication,
    DailyLog,
    Review,
)


# ============================================================
# LEGACY API v1 (Application / InternLog tabanlı)
# Şu fonksiyonlar şu anda urls.py'de tanımlı DEĞİL.
# İstersen ileride tamamen silebilirsin, şimdilik kalsın.
# ============================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def apply_api_view(request):
    """
    POST /staj/api/apply/  (ESKİ: Application modeli için)
    """
    form = ApplicationForm(request.data)
    if form.is_valid():
        app = form.save()
        return Response(
            {"message": "Başvuru alındı", "id": app.id},
            status=status.HTTP_201_CREATED,
        )
    return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([AllowAny])
def application_detail_api_view(request, tc_kimlik, phone):
    """
    GET /staj/api/requests/{tc_kimlik}/{telefon}/ (ESKİ: Application modeli için)
    """
    try:
        app = Application.objects.get(tc_kimlik=tc_kimlik, phone=phone)
    except Application.DoesNotExist:
        return Response(
            {"detail": "Kayıt bulunamadı"},
            status=status.HTTP_404_NOT_FOUND,
        )

    data = {
        "first_name": app.first_name,
        "last_name": app.last_name,
        "status": app.status,
        "school": app.school,
        "department": app.department,
        "created_at": app.created_at,
    }
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def log_create_api_view(request):
    """
    POST /staj/api/logs/  (ESKİ: InternLog modeli için)
    """
    form = InternLogForm(request.data)
    if form.is_valid():
        log = form.save(commit=False)
        log.created_by = request.user
        log.save()
        return Response(
            {"message": "Günlük kaydedildi", "id": log.id},
            status=201,
        )
    return Response(form.errors, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def review_create_api_view(request):
    """
    POST /staj/api/reviews/
    Beklenen payload: {"log": log_id, "score": 80, "comment": "..."}
    (ESKİ: InternLog + LogReview modeli için)
    """
    log_id = request.data.get("log")
    score = request.data.get("score")
    comment = request.data.get("comment", "")

    try:
        log = InternLog.objects.get(id=log_id)
    except InternLog.DoesNotExist:
        return Response({"detail": "Log bulunamadı"}, status=404)

    review, created = LogReview.objects.update_or_create(
        log=log,
        defaults={
            "reviewer": request.user,
            "score": score,
            "comment": comment,
        },
    )
    return Response({"message": "Değerlendirme kaydedildi"})


# ============================================================
# JWT Login API (aktif, urls.py'de tanımlı)
# ============================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def jwt_login_view(request):
    """
    POST /staj/api/login/
    Body: {"username": "...", "password": "..."}
    """
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(username=username, password=password)
    if not user:
        return Response({"detail": "Geçersiz kimlik bilgisi"}, status=400)

    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
    )


# ============================================================
# YENİ API v2 (InternApplication tabanlı JSON API)
# urls.py'de aktif olan uçlar bunlar.
# ============================================================

@require_http_methods(["POST"])
def apply_api(request):
    """
    POST /staj/api/apply/

    Body (JSON):
    {
        "first_name": "...",
        "last_name": "...",
        "tc_no": "...",
        "phone": "...",
        "email": "...",
        "school": "...",
        "department": "...",
        "grade": "...",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD"
    }
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid_json"}, status=400)

    form = InternApplicationForm(payload)
    if form.is_valid():
        app = form.save()
        return JsonResponse(
            {
                "id": app.id,
                "status": app.status,
                "first_name": app.first_name,
                "last_name": app.last_name,
                "tc_no": app.tc_no,
                "phone": app.phone,
            },
            status=201,
        )

    # Form hatalarını JSON dönder
    return JsonResponse({"errors": form.errors}, status=400)


@require_http_methods(["GET"])
def requests_api(request, tc_no, phone):
    """
    GET /staj/api/requests/<tc_no>/<phone>/

    InternApplication üzerinden başvuru durum sorgulama.
    """
    try:
        app = InternApplication.objects.get(tc_no=tc_no, phone=phone)
    except InternApplication.DoesNotExist:
        return JsonResponse({"error": "not_found"}, status=404)

    return JsonResponse(
        {
            "status": app.status,
            "first_name": app.first_name,
            "last_name": app.last_name,
            "school": app.school,
            "department": app.department,
        }
    )
