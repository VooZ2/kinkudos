from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.shortcuts import redirect

from .models import ChildProfile


def current_child(request):
    child_id = request.session.get("child_id")
    if not child_id:
        return None
    try:
        return ChildProfile.objects.get(pk=child_id, is_active=True)
    except ChildProfile.DoesNotExist:
        request.session.flush()
        return None


def parent_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        return view(request, *args, **kwargs)

    return wrapped


def child_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        child = current_child(request)
        if child is None:
            return redirect("child_select")
        request.child = child
        if (
            not child.theme_selected
            and request.resolver_match
            and request.resolver_match.url_name != "child_theme_onboarding"
        ):
            return redirect("child_theme_onboarding")
        return view(request, *args, **kwargs)

    return wrapped


def child_object_or_404(request, queryset, **lookup):
    child = current_child(request)
    if child is None:
        raise Http404
    return queryset.get(child=child, **lookup)
