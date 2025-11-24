from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken

from .models import Application, InternLog, LogReview
from .forms import ApplicationForm, InternLogForm


@api_view(["POST"])
@permission_classes([AllowAny])
def apply_api_view(request):
    """
    POST /staj/api/apply/
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
    GET /staj/api/requests/{tc_kimlik}/{telefon}/
    """
    try:
        app = Application.objects.get(tc_kimlik=tc_kimlik, phone=phone)
    except Application.DoesNotExist:
        return Response({"detail": "Kayıt bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

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
    POST /staj/api/logs/
    """
    form = InternLogForm(request.data)
    if form.is_valid():
        log = form.save(commit=False)
        log.created_by = request.user
        log.save()
        return Response({"message": "Günlük kaydedildi", "id": log.id}, status=201)
    return Response(form.errors, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def review_create_api_view(request):
    """
    POST /staj/api/reviews/
    Beklenen payload: {"log": log_id, "score": 80, "comment": "..."}
    Sadece personel/admin mantığını daha sonra role ile kısıtlayabilirsin.
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
        defaults={"reviewer": request.user, "score": score, "comment": comment},
    )
    return Response({"message": "Değerlendirme kaydedildi"})


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
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import InternApplication, DailyLog, Review

@require_http_methods(["POST"])
def apply_api(request):
    # POST /staj/api/apply
    data = json.loads(request.body)
    # burada data içinden alanları çekip InternApplication oluşturursun
    return JsonResponse({"ok": True})


@require_http_methods(["GET"])
def requests_api(request, tc_no, phone):
    # GET /staj/api/requests/<tc_no>/<phone>/
    try:
        app = InternApplication.objects.get(tc_no=tc_no, phone=phone)
        return JsonResponse({
            "status": app.status,
            "first_name": app.first_name,
            "last_name": app.last_name,
        })
    except InternApplication.DoesNotExist:
        return JsonResponse({"error": "not_found"}, status=404)
