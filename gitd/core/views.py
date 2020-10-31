import hmac
from hashlib import sha1
from ipaddress import ip_address, ip_network

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.utils.encoding import force_bytes
from django.utils.translation import gettext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import requests


@require_POST
@csrf_exempt
def github(request):
    # Verify if request came from GitHub
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    client_ip_address = ip_address(forwarded_for)
    allow_list = requests.get("https://api.github.com/meta").json()["hooks"]

    for valid_ip in allow_list:
        if client_ip_address in ip_network(valid_ip):
            break
    else:
        return HttpResponseForbidden(gettext("Permission denied."))

    # Verify the request signature
    header_signature = request.META.get("HTTP_X_HUB_SIGNATURE")
    if header_signature is None:
        return HttpResponseForbidden(gettext("Permission denied."))

    sha_name, signature = header_signature.split("=")
    if sha_name != "sha1":
        return HttpResponseServerError(gettext("Operation not supported."), status=501)

    mac = hmac.new(force_bytes(settings.GITHUB_WEBHOOK_KEY), msg=force_bytes(request.body), digestmod=sha1)
    if not hmac.compare_digest(force_bytes(mac.hexdigest()), force_bytes(signature)):
        return HttpResponseForbidden(gettext("Permission denied."))

    # If request reached this point we are in a good shape
    # Process the GitHub events
    event = request.META.get("HTTP_X_GITHUB_EVENT", "ping")

    if event == "ping":
        return HttpResponse("pong")
    elif event == "push":
        # Deploy some code for example
        return HttpResponse(gettext("OK"))

    # In case we receive an event that's not ping or push
    return HttpResponse(status=204)
