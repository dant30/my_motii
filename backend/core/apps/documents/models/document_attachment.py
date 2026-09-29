"""Immutable file references attached to business documents."""

from django.db import models

from apps.common.models import BaseModel


class DocumentAttachment(BaseModel):
	document = models.ForeignKey("documents.Document", on_delete=models.CASCADE, related_name="attachments")
	file_url = models.URLField(max_length=500)
	file_name = models.CharField(max_length=255, blank=True)
	content_type = models.CharField(max_length=100, blank=True)