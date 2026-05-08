from django.db.models import Q

from internship.models import Announcement, ConversationMessage, InternApplication, PersonnelProfile


def panel_context(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {
            "panel_unread_messages": 0,
            "panel_recent_messages": [],
            "panel_notifications": [],
            "panel_notification_count": 0,
        }

    is_personnel = user.groups.filter(name="Personel").exists()
    is_intern = user.groups.filter(name="Stajyer").exists()
    messages_qs = ConversationMessage.objects.none()
    panel_avatar_url = ""

    if is_personnel:
        personnel = PersonnelProfile.objects.filter(user=user, is_active=True).first()
        if personnel:
            if personnel.profile_avatar:
                panel_avatar_url = personnel.profile_avatar.url
            messages_qs = ConversationMessage.objects.select_related("sender", "application").filter(
                application__supervisor=personnel,
                deleted_at__isnull=True,
            )
    elif is_intern:
        application = InternApplication.objects.filter(user=user).first()
        if application:
            if application.profile_avatar:
                panel_avatar_url = application.profile_avatar.url
            messages_qs = ConversationMessage.objects.select_related("sender", "application").filter(
                application=application,
                deleted_at__isnull=True,
            )

    unread_messages = messages_qs.filter(read_at__isnull=True).exclude(sender=user).count()
    recent_messages = messages_qs.exclude(sender=user).order_by("-created_at")[:5]

    target_filter = Q(target=Announcement.Target.ALL)
    if is_personnel:
        target_filter |= Q(target=Announcement.Target.STAFF)
    elif is_intern:
        target_filter |= Q(target=Announcement.Target.INTERN)
    notifications = Announcement.objects.filter(target_filter, is_active=True).order_by("-created_at")[:5]

    return {
        "panel_unread_messages": unread_messages,
        "panel_recent_messages": recent_messages,
        "panel_notifications": notifications,
        "panel_notification_count": unread_messages + notifications.count(),
        "panel_avatar_url": panel_avatar_url,
    }
