from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.auditlog.services import log_event
from apps.tenants.permissions import user_can_manage_tenant

from .forms import FileUploadForm
from .models import FileAsset


def _get_tenant(request):
    return getattr(request, "tenant", None)


@login_required
def file_list(request):
    tenant = _get_tenant(request)
    if tenant is None:
        return HttpResponseForbidden("No tenant selected.")

    files = FileAsset.objects.filter(
        tenant=tenant,
        is_active=True,
    ).select_related("uploaded_by")

    return render(request, "files/file_list.html", {
        "files": files,
    })


@login_required
def upload_file(request):
    tenant = _get_tenant(request)
    if tenant is None:
        return HttpResponseForbidden("No tenant selected.")

    if not user_can_manage_tenant(request.user, tenant):
        return HttpResponseForbidden("You do not have access to upload files.")

    if request.method == "POST":
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_asset = form.save(commit=False)
            file_asset.tenant = tenant
            file_asset.uploaded_by = request.user
            file_asset.save()

            log_event(
                tenant=tenant,
                actor=request.user,
                request=request,
                action="create",
                message=f"File uploaded: {file_asset.title}",
                object_type="FileAsset",
                object_id=file_asset.id,
                meta={
                    "file_id": str(file_asset.id),
                    "title": file_asset.title,
                    "category": file_asset.category,
                    "filename": file_asset.file.name,
                },
            )

            messages.success(request, "File uploaded successfully.")
            return redirect("files:list")
    else:
        form = FileUploadForm()

    return render(request, "files/file_upload.html", {
        "form": form,
    })


@login_required
def deactivate_file(request, file_id):
    tenant = _get_tenant(request)
    if tenant is None:
        return HttpResponseForbidden("No tenant selected.")

    if not user_can_manage_tenant(request.user, tenant):
        return HttpResponseForbidden("You do not have access to deactivate files.")

    file_asset = get_object_or_404(FileAsset, id=file_id, tenant=tenant)

    if request.method == "POST":
        file_asset.is_active = False
        file_asset.save(update_fields=["is_active"])

        log_event(
            tenant=tenant,
            actor=request.user,
            request=request,
            action="update",
            message=f"File deactivated: {file_asset.title}",
            object_type="FileAsset",
            object_id=file_asset.id,
            meta={
                "file_id": str(file_asset.id),
                "title": file_asset.title,
                "category": file_asset.category,
            },
        )

        messages.success(request, "File deactivated.")
        return redirect("files:list")

    return HttpResponseForbidden("Invalid request method.")