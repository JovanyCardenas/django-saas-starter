from django.shortcuts import render


def custom_403(request, exception=None):
    return render(request, "403.html", status=403)


def custom_404(request, exception):
    return render(request, "404.html", status=404)