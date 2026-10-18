from django.contrib import admin

from .models import Scheme, Benefit, RequiredDocument, ApplyStep

# Register your models here.

class BenefitInline(admin.TabularInline):
    model = Benefit  #which model you want to add or edit
    extra = 1 # display one extra field , allow to add a new record

class RequiredDocumentInline(admin.TabularInline):
    model = RequiredDocument
    extra = 1

class ApplyStepInline(admin.TabularInline):
    model = ApplyStep
    extra = 1


@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    """Register the Scheme model in Django Admin and customize it using SchemeAdmin."""
    list_display = ("name", "level", "state", "status", "last_updated")
    list_filter = ("status", "level")
    search_fields = ("name", "ministry")
    prepopulated_fields = {"slug": ("name",)} # after type the name, slug automatically suggests
    inlines = [BenefitInline, RequiredDocumentInline, ApplyStepInline]