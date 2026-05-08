from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.http import HttpResponseRedirect


class CanonicalHostRedirectMiddleware:
    """
    Keep local development on a single hostname so session cookies remain valid.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self._maybe_redirect(request)
        if response is not None:
            return response
        return self.get_response(request)

    def _maybe_redirect(self, request):
        if request.method not in {"GET", "HEAD"}:
            return None

        canonical_host = getattr(settings, "CANONICAL_HOST", "").strip()
        if not canonical_host:
            return None

        current_host = request.get_host()
        current_hostname = current_host.split(":", 1)[0].lower()
        canonical_hostname = canonical_host.split(":", 1)[0].lower()
        local_aliases = {"127.0.0.1", "localhost"}

        if current_hostname not in local_aliases or canonical_hostname not in local_aliases:
            return None

        if current_host.lower() == canonical_host.lower():
            return None

        parsed = urlsplit(request.build_absolute_uri())
        redirect_url = urlunsplit(
            (request.scheme, canonical_host, parsed.path, parsed.query, parsed.fragment)
        )
        return HttpResponseRedirect(redirect_url)
