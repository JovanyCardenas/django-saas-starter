from django.urls import path
from . import views

app_name = "tenants"

urlpatterns = [
    path("choose/", views.choose_tenant, name="choose"),
    path("clear/", views.clear_tenant, name="clear"),
]