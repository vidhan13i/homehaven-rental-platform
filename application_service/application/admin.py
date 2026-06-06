from django.contrib import admin
from application.models import Application, Applicant, Document


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0


class ApplicationInline(admin.TabularInline):
    model = Application
    extra = 0
    fields = ['unit_ID', 'building_ID', 'application_status', 'submitted_at_date']
    readonly_fields = ['submitted_at_date']


@admin.register(Applicant)
class ApplicantAdmin(admin.ModelAdmin):
    list_display = ['id', 'profile_ID', 'employer', 'job_title', 'credit_score', 'income', 'has_rented_before']
    list_filter = ['has_rented_before', 'marital_status']
    search_fields = ['employer', 'job_title']
    inlines = [ApplicationInline, DocumentInline]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'unit_ID', 'building_ID', 'applicant_ID', 'application_status', 'submitted_at_date']
    list_filter = ['application_status']
    list_editable = ['application_status']
    date_hierarchy = 'submitted_at_date'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'applicant_ID', 'file_field', 'created_at']
    list_filter = ['created_at']
