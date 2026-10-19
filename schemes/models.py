from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

from .rule_spec import (
    FIELD_SPECS, ALLOWED_OPERATORS, OPERATORS, CHOICE, NUMBER, BOOLEAN
)

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

    # name of the scheme, example : student scholership yojana
    name = models.CharField(max_length=255)
    # correspoding slug to scheme name, like student-scholership-yojana
    slug = models.SlugField(max_length=255, unique=True)
    # corresponding ministry or department of the scheme
    ministry = models.CharField(max_length=255, blank=True)
    level = models.CharField(max_length=10, choices=Level.choices,
                             default=Level.CENTRAL)  # default level: CENTRAL

    state = models.CharField(
        max_length=100,
        blank=True,
        help_text="Only for state-level schemes. Leave blank for central schemes.",
    )

    short_description = models.TextField(
        blank=True)  # short introduction to scheme
    eligibility_text = models.TextField(
        blank=True,
        help_text="Original eligibility text exactly as on the source page.",
    )
    # page URL from where information has been taken
    source_url = models.URLField(blank=True)

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
    # very first time when record is created
    created_at = models.DateTimeField(auto_now_add=True)
    # after saved , what is the latest update date-time
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Default scheme rendering order Alphabetic order."""
        ordering = ["name"]

    def __str__(self):
        return self.name


class Benefit(models.Model):
    """
    Stores a benefit provided by a government scheme.

    A scheme can have multiple benefits, such as financial assistance,
    subsidies, or insurance coverage.

    Each benefit is linked to a Scheme through a foreign key.
    If the associated scheme is deleted, its benefits are also deleted.
    """
    scheme = models.ForeignKey(
        Scheme,
        on_delete=models.CASCADE,
        related_name="benefits",
    )
    description = models.TextField()

    def __str__(self):
        """Return the scheme name and the first 50 characters of the benefit."""
        return f"{self.scheme.name}: {self.description[:50]}"


class RequiredDocument(models.Model):
    """
    Stores a document required to apply for a government scheme.

    Each document belongs to a specific scheme and includes its name
    and optional notes providing additional information.

    Multiple documents can be associated with the same scheme.
    """
    scheme = models.ForeignKey(
        Scheme,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    name = models.CharField(max_length=255)  # document name
    # additional information about document
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        """Return the scheme name and the required document name."""
        return f"{self.scheme.name}: {self.name}"


class ApplyStep(models.Model):
    """
    Stores an individual instruction in the application process
    for a government scheme.

    Each step belongs to a specific scheme and has a sequence number
    that determines its position in the application process.

    Multiple steps can be associated with the same scheme.
    """
    scheme = models.ForeignKey(
        Scheme,
        on_delete=models.CASCADE,
        related_name="apply_steps",
    )
    order = models.PositiveBigIntegerField(default=1)  # step sequence number
    instruction = models.TextField()  # For user: what to do

    class Meta:
        ordering = ["scheme", "order"]

    def __str__(self):
        return f"{self.scheme.name}: step {self.order}"


class EligibilityRule(models.Model):
    """
    Stores a single eligibility condition for a government scheme.

    Each rule consists of a field, an operator, and a value.
    For example: age >= 18 or occupation in ["farmer", "labourer"].

    The JSONField allows values of different data types, such as
    numbers, strings, lists, and booleans. However, the field itself
    does not validate whether a value is appropriate for a specific
    field. This is handled by the model's clean() method.

    Multiple rules can belong to the same scheme. Rules are ordered
    by scheme and field, and a database constraint prevents duplicate
    combinations of scheme, field, and operator.
    """
    scheme = models.ForeignKey(  # eligibility rule must be connected to a scheme
        Scheme,
        on_delete=models.CASCADE,
        related_name="rules"
    )
    field = models.CharField(
        max_length=50,
        choices=[(key, spec["label"]) for key, spec in FIELD_SPECS.items()],
    )
    operator = models.CharField(
        max_length=10,
        choices=list(OPERATORS.items()),
    )
    value = models.JSONField(
        help_text='JSON format: 18, "farmer", ["farmer", "labourer"], true',
    )
    source_text = models.TextField(
        blank=True,
        help_text="The sentence from the source page this rule was taken from.",
    )
    created_at = models.DateTimeField(auto_now_add=True)  # first time enrty
    updated_at = models.DateTimeField(auto_now=True)  # latest update

    class Meta:
        ordering = ["scheme", "field"]
        constraints = [    # avoid duplicate rule addition in the same scheme
            models.UniqueConstraint(
                fields=["scheme", "field", "operator"],
                name="unique_rule_per_scheme_field_operator",
            )
        ]

    def __str__(self):
        return f"{self.scheme.name}: {self.field} {self.operator} {self.value}"

    def clean(self):
        """
        Validates the eligibility rule against the rule specification.

        Checks whether the field exists, whether the operator is allowed
        for the field type, and whether the value has the expected type.

        For 'in' and 'not_in' operators, the value must be a non-empty list.

        Boolean values require a separate type check because Python's bool
        type is a subclass of int. Without this check, True and False could
        incorrectly be accepted as numeric values.

        Raises ValidationError when a validation rule is violated.
        """
        spec = FIELD_SPECS.get(self.field)
        if spec is None or self.value is None:
            return

        field_type = spec["type"]
        if self.operator not in ALLOWED_OPERATORS[field_type]:
            raise ValidationError(
                f"Operator {self.operator} is not allowed for {field_type} field '{self.field}'."
            )

        if self.operator in ("in", "not_in"):
            if not isinstance(self.value, list) or not self.value:
                raise ValidationError(
                    "For 'in' / 'not_in', value must be a non-empty list.")
        elif field_type == NUMBER:
            if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
                raise ValidationError("Value must be a number for this field.")
        elif field_type == BOOLEAN:
            if not isinstance(self.value, bool):
                raise ValidationError(
                    "Value must be true or false for this field.")
        elif field_type == CHOICE:
            if not isinstance(self.value, str):
                raise ValidationError(
                    'Value must be text in quotes, e.g. "farmer".')


class RuleVersion(models.Model):
    """
    Stores a versioned snapshot of a scheme's eligibility rules.

    Each version preserves the rules as they existed at a particular
    point in time, supporting historical review, auditing, and rollback.

    The rules_snapshot JSONField stores a copy of the scheme's rules.
    Changes to the current EligibilityRule records do not automatically
    update previously created snapshots.

    Each scheme has its own version numbering, and a database constraint
    prevents duplicate version numbers for the same scheme.

    Verification details record who verified a version and when.
    Creating a snapshot does not automatically verify it.
    """
    scheme = models.ForeignKey(
        Scheme, on_delete=models.CASCADE,
        related_name="rule_versions",
    )
    version_number = models.PositiveIntegerField()  # version 1 , version 2 like that
    rules_snapshot = models.JSONField()
    # whats changed in versions. short reason
    change_note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """
        Defines the default ordering and database constraints for versions.

        Versions are ordered by scheme and then by descending version number,
        so higher-numbered versions appear first within each scheme.

        A unique constraint ensures that a scheme cannot have two versions
        with the same version number.
        """
        ordering = ["scheme", "-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["scheme", "version_number"],
                name="unique_version_per_scheme",
            )
        ]

    def __str__(self):
        return f"{self.scheme.name} v{self.version_number}"

    @classmethod
    def create_snapshot(cls, scheme, user=None, note=""):
        """
        Creates a new version containing a snapshot of a scheme's current rules.

        Finds the latest version number for the scheme, assigns the next
        sequential number, and copies the current rules into a JSON snapshot.

        Args:
            scheme: The scheme whose current eligibility rules will be captured.
            user: The optional user who created the snapshot.
            note: An optional note explaining the reason for the change.

        Returns:
            The newly created RuleVersion instance.

        Note:
            This method does not verify the snapshot or implement rollback.
            Concurrent calls require additional handling to avoid version-number
            conflicts.
        """
        last = cls.objects.filter(scheme=scheme).order_by(
            "-version_number").first()
        next_number = last.version_number + 1 if last else 1
        snapshot = [
            {
                "field": rule.field,
                "operator": rule.operator,
                "value": rule.value,
                "source_text": rule.source_text,
            }
            for rule in scheme.rules.all()
        ]
        return cls.objects.create(
            scheme=scheme,
            version_number=next_number,
            rules_snapshot=snapshot,
            change_note=note,
            created_by=user,
        )
