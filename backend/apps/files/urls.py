from django.urls import path

from . import views

app_name = "files"

urlpatterns = [
    path("", views.file_list, name="list"),
    path("upload/", views.upload_file, name="upload"),
    path("<uuid:file_id>/deactivate/", views.deactivate_file, name="deactivate"),
]