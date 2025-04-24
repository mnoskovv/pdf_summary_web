from django.contrib import admin
from .models import OpenaiSettings, Log, Document


@admin.register(OpenaiSettings)
class OpenaiSettingsAdmin(admin.ModelAdmin):
    list_display = ('model', 'temperature', 'max_retries', 'summary_prompt')
    
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('model', 'temperature', 'max_retries', 'is_successful', 'is_retried')
    search_fields = ('model',)
    list_filter = ('is_successful', 'is_retried')
    readonly_fields = ('messages', 'result')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'status')
    list_filter = ('status',)
    search_fields = ('file',)
