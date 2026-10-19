from django.contrib import admin

from .models import Scheme, Benefit, RequiredDocument, ApplyStep, RuleVersion, EligibilityRule


class BenefitInline(admin.TabularInline):
    """Allow benefits to be added or edited directly on the Scheme admin page."""
    model = Benefit  # which model you want to add or edit
    extra = 1  # display one extra field , allow to add a new record


class RequiredDocumentInline(admin.TabularInline):
    """Allow required documents to be managed within the Scheme admin page."""
    model = RequiredDocument
    extra = 1


class ApplyStepInline(admin.TabularInline):
    """Allow application steps to be managed within the Scheme admin page."""
    model = ApplyStep
    extra = 1


class EligibilityRuleInline(admin.TabularInline):
    """Allow eligibility rules to be added or edited within the Scheme admin page."""
    model = EligibilityRule
    extra = 1


@admin.action(description="Save a snapshot of current rules")
def save_rules_snapshot(modeladmin, request, queryset):
    """
    Create a versioned snapshot of the eligibility rules for selected schemes.

    Args:
        modeladmin: The ModelAdmin instance managing the selected schemes.
        request: The current HTTP request, used to identify the logged-in user.
        queryset: The schemes selected by the administrator.

    Saves the current rules for each selected scheme and displays a
    confirmation message indicating how many schemes were processed.

    Note:
        Saving a snapshot does not automatically verify or approve the rules.
    """
    for scheme in queryset:
        RuleVersion.create_snapshot(
            scheme, user=request.user, note="Manual snapshot from admin")
    modeladmin.message_user(request, f"Snapshot saved for {queryset.count()} scheme(s).")


@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    """
    Configure the Django Admin interface for managing government schemes.

    Displays important scheme details, provides filtering and searching,
    automatically suggests slugs from scheme names, and allows administrators
    to manage benefits, required documents, application steps, and eligibility
    rules directly from the scheme page.

    Also provides a custom action to save versioned snapshots of eligibility
    rules for selected schemes.
    """
    list_display = ("name", "level", "state", "status", "last_updated")
    list_filter = ("status", "level")
    search_fields = ("name", "ministry")
    # after type the name, slug automatically suggests
    prepopulated_fields = {"slug": ("name",)}
    inlines = [BenefitInline, RequiredDocumentInline,
               ApplyStepInline, EligibilityRuleInline,]
    actions = [save_rules_snapshot]
