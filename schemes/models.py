from django.db import models

# Create your models here.

class Scheme(models.Model):
    """
    LEVEL:
        Scheme is at central-level or state-level.

    Scheme review statuses:
        DRAFT:
            Data has been added, but review is pending.

        VERIFIED:
            Information has been reviewed and verified.

        REVIEW_NEEDED:
            Changes have been detected, so the scheme needs to be
            reviewed again.
    """

    class Level(models.TextChoices):
        CENTRAL = "central", "Central"  # in database: central, for visibility: Central
        STATE = "state", "State"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        VERIFIED = "verified", "Verified"
        REVIEW_NEEDED = "review_needed", "Review needed"

    name = models.CharField(max_length=255)  # name of the scheme, example : student scholership yojana
    slug = models.SlugField(max_length=255, unique=True)  # correspoding slug to scheme name, like student-scholership-yojana
    ministry = models.CharField(max_length=255, blank=True)  # corresponding ministry or department of the scheme
    level = models.CharField(max_length=10, choices=Level.choices, default=Level.CENTRAL)  # default level: CENTRAL

    state = models.CharField(
        max_length=100,
        blank=True,
        help_text="Only for state-level schemes. Leave blank for central schemes.",
    )

    short_description = models.TextField(blank=True)  # short introduction to scheme
    eligibility_text = models.TextField(
        blank=True, 
        help_text="Original eligibility text exactly as on the source page.",
    )
    source_url = models.URLField(blank=True)  # page URL from where information has been taken

    last_updated = models.DateField(
        null=True,
        blank=True, 
        help_text="When the source data was last checked.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices, 
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)  # very first time when record is created
    updated_at = models.DateTimeField(auto_now=True)  # after saved , what is the latest update date-time

    class Meta:
        """Default scheme rendering order Alphabetic order."""
        ordering = ["name"]

    def __str__(self):
        return self.name



class Benefit(models.Model):
    scheme = models.ForeignKey(
        Scheme,
        on_delete=models.CASCADE,
        related_name="benefits",
    )
    description = models.TextField()

    def __str__(self):
        return f"{self.scheme.name}: {self.description[:50]}"



class RequiredDocument(models.Model):
    scheme = models.ForeignKey(
        Scheme,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    name = models.CharField(max_length=255) #document name
    notes = models.CharField(max_length=255, blank=True) # additional information about document

    def __str__(self):
        return f"{self.scheme.name}: {self.name}"


class ApplyStep(models.Model):
    scheme = models.ForeignKey(
        Scheme,
        on_delete=models.CASCADE,
        related_name="apply_steps",
    )
    order = models.PositiveBigIntegerField(default=1) #step sequence number
    instruction = models.TextField() # For user: what to do

    class Meta:
        ordering = ["scheme", "order"]

    def __str__(self):
        return f"{self.scheme.name}: step {self.order}"