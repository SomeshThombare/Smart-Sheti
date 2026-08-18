from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required


ROLE_ADMIN = "admin"
ROLE_FARMER = "farmer"


def index(request: HttpRequest) -> HttpResponse:
    context = {
        "title": "Smart Sheti - Digital Farming Platform",
        "is_authenticated": request.user.is_authenticated,
        "user_type": getattr(request.user, "user_type", None) if request.user.is_authenticated else None,
    }
    return render(request, "index.html", context)


@login_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    if getattr(request.user, "user_type", None) != ROLE_ADMIN:
        return HttpResponseForbidden("Only admin can access admin dashboard.")

    context = {
        "title": "Admin Dashboard - Smart Sheti",
        "page_title": "Admin Dashboard",
        "user_name": request.user.get_full_name() or request.user.username,
        "is_admin": True,
        "is_farmer": False,
    }
    return render(request, "dashboard/admin_dashboard.html", context)


@login_required
def farmer_dashboard(request: HttpRequest) -> HttpResponse:
    if getattr(request.user, "user_type", None) != ROLE_FARMER:
        return HttpResponseForbidden("Only farmer can access farmer dashboard.")

    context = {
        "title": "Farmer Dashboard - Smart Sheti",
        "page_title": "Farmer Dashboard",
        "user_name": request.user.get_full_name() or request.user.username,
        "is_admin": False,
        "is_farmer": True,
    }
    return render(request, "dashboard/farmer_dashboard.html", context)


@login_required
def dashboard_redirect(request: HttpRequest) -> HttpResponse:
    user_type = getattr(request.user, "user_type", None)

    if user_type == ROLE_ADMIN:
        return redirect("admin-dashboard")
    elif user_type == ROLE_FARMER:
        return redirect("farmer-dashboard")

    return redirect("index")