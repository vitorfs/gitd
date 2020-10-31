import hmac
import json
from hashlib import sha256
from ipaddress import ip_address, ip_network

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseServerError
from django.utils.encoding import force_bytes
from django.utils.translation import gettext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import requests

from gitd.core.exceptions import GitHubException
from gitd.core.handlers import github_handler


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
        return HttpResponseForbidden(gettext("Permission denied."), content_type="text/plain")

    # Retrieve the delivery ID
    delivery_id = request.META.get("HTTP_X_GITHUB_DELIVERY")
    if delivery_id is None:
        return HttpResponseForbidden(gettext("Permission denied."), content_type="text/plain")

    # Verify the request signature
    header_signature = request.META.get("HTTP_X_HUB_SIGNATURE_256")
    if header_signature is None:
        return HttpResponseForbidden(gettext("Permission denied."), content_type="text/plain")

    sha_name, signature = header_signature.split("=")
    if sha_name != "sha256":
        return HttpResponseServerError(gettext("Operation not supported."), status=501, content_type="text/plain")

    mac = hmac.new(force_bytes(settings.GITHUB_WEBHOOK_KEY), msg=force_bytes(request.body), digestmod=sha256)
    if not hmac.compare_digest(force_bytes(mac.hexdigest()), force_bytes(signature)):
        return HttpResponseForbidden(gettext("Permission denied."), content_type="text/plain")

    # If request reached this point we are in a good shape
    # Process the GitHub events
    event = request.META.get("HTTP_X_GITHUB_EVENT", "ping")

    data = json.loads(request.body)

    try:
        response = github_handler(data, event, delivery_id)
        return HttpResponse(response, content_type="text/plain")
    except GitHubException as err:
        return HttpResponseBadRequest(f"[{err.code}] {err.message}", content_type="text/plain")
