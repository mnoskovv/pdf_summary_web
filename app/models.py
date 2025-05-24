from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django_prometheus.models import ExportModelOperationsMixin

from app.utils.models.BaseModel import BaseModel

class OpenaiSettings(ExportModelOperationsMixin('openai_settings'), BaseModel):
    model = models.CharField(max_length=64)
    temperature = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    max_retries = models.PositiveIntegerField(default=0)

    summary_prompt = models.TextField(max_length=10000, blank=True)

    class Meta:
        verbose_name = "settings"
        verbose_name_plural = "settings"

    def __str__(self):
        return self.title

    @property
    def title(self):
        return f"{self.model}".strip()


class Log(BaseModel):
    model = models.CharField(max_length=64)
    temperature = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    max_retries = models.PositiveIntegerField(default=0)

    messages = models.JSONField(default=dict)
    result = models.JSONField(default=dict)

    is_successful = models.BooleanField(default=False)
    is_retried = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    @property
    def title(self):
        return ""

class Document(ExportModelOperationsMixin('document'), BaseModel):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    file = models.FileField(upload_to='pdfs/')
    summary = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.UPLOADED
    )

    def filename(self):
        return self.file.name.split('/')[-1]

    def __str__(self):
        return f"{self.filename()} - {self.status}"

class DocumentChunk(BaseModel):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    text = models.TextField()


class Message(ExportModelOperationsMixin('messsage'), BaseModel):
    class Role(models.TextChoices):
        USER = "user"
        ASSISTANT = "assistant"

    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
