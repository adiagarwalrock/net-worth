"""
Household and Family management models.
"""
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Household(models.Model):
    """
    Represents a household/family group that can track combined net worth.

    Attributes:
        name: Name of the household (e.g., "Smith Family")
        created_by: User who created this household
        description: Optional description
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    name = models.CharField(
        max_length=200,
        help_text="Name of the household (e.g., 'Smith Family')"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_households',
        help_text="User who created this household"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description of the household"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Household"
        verbose_name_plural = "Households"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_total_net_worth(self):
        """
        Calculate combined net worth for all household members.

        Returns:
            Decimal: Total household net worth in creator's home currency
        """
        from networth.services import NetWorthService
        return NetWorthService.calculate_household_net_worth(self)

    def get_members_count(self):
        """
        Get the number of members in this household.

        Returns:
            int: Number of members
        """
        return self.members.count()

    def is_owner(self, user):
        """
        Check if user is the owner of this household.

        Args:
            user: User object

        Returns:
            bool: True if user is owner
        """
        try:
            member = self.members.get(user=user)
            return member.role == HouseholdMember.OWNER
        except HouseholdMember.DoesNotExist:
            return False

    def can_user_manage(self, user):
        """
        Check if user can manage (add/remove members) this household.

        Args:
            user: User object

        Returns:
            bool: True if user can manage
        """
        return self.is_owner(user)


class HouseholdMember(models.Model):
    """
    Represents a user's membership in a household with specific role and permissions.

    Attributes:
        household: The household this membership belongs to
        user: The user who is a member
        role: Member's role (OWNER, MEMBER, VIEWER)
        can_view_details: Whether member can see detailed financial info
        joined_at: When the user joined this household
    """
    OWNER = 'OWNER'
    MEMBER = 'MEMBER'
    VIEWER = 'VIEWER'

    ROLE_CHOICES = [
        (OWNER, 'Owner'),
        (MEMBER, 'Member'),
        (VIEWER, 'Viewer'),
    ]

    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name='members',
        help_text="The household this membership belongs to"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='household_memberships',
        help_text="The user who is a member"
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=MEMBER,
        help_text="Member's role in the household"
    )
    can_view_details = models.BooleanField(
        default=True,
        help_text="Whether member can see detailed financial information"
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Household Member"
        verbose_name_plural = "Household Members"
        unique_together = ['household', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.username} - {self.household.name} ({self.get_role_display()})"

    def clean(self):
        """
        Validate that each household has at least one owner.
        """
        super().clean()

        # If removing the last owner, raise error
        if self.role != self.OWNER and self.pk:
            owners_count = HouseholdMember.objects.filter(
                household=self.household,
                role=self.OWNER
            ).exclude(pk=self.pk).count()

            if owners_count == 0:
                raise ValidationError(
                    "Cannot change role: Household must have at least one owner."
                )

    def save(self, *args, **kwargs):
        """
        Override save to run validation.
        """
        self.full_clean()
        super().save(*args, **kwargs)


class HouseholdInvitation(models.Model):
    """
    Represents an invitation to join a household.

    Attributes:
        household: The household to which user is invited
        email: Email address of invitee
        invited_by: User who sent the invitation
        role: Proposed role for the invitee
        status: Invitation status (PENDING, ACCEPTED, DECLINED, EXPIRED)
        created_at: When invitation was sent
        expires_at: When invitation expires
    """
    PENDING = 'PENDING'
    ACCEPTED = 'ACCEPTED'
    DECLINED = 'DECLINED'
    EXPIRED = 'EXPIRED'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (DECLINED, 'Declined'),
        (EXPIRED, 'Expired'),
    ]

    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name='invitations',
        help_text="The household to which user is invited"
    )
    email = models.EmailField(
        help_text="Email address of invitee"
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        help_text="User who sent the invitation"
    )
    role = models.CharField(
        max_length=10,
        choices=HouseholdMember.ROLE_CHOICES,
        default=HouseholdMember.MEMBER,
        help_text="Proposed role for the invitee"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=PENDING,
        help_text="Invitation status"
    )
    token = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique invitation token"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="When invitation expires"
    )

    class Meta:
        verbose_name = "Household Invitation"
        verbose_name_plural = "Household Invitations"
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation to {self.email} for {self.household.name}"

    def is_valid(self):
        """
        Check if invitation is still valid.

        Returns:
            bool: True if invitation is pending and not expired
        """
        from django.utils import timezone
        return (
            self.status == self.PENDING and
            self.expires_at > timezone.now()
        )
