from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    head = models.OneToOneField(
        User, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='headed_department'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('hr_admin',   'HR Admin'),
        ('dept_head',  'Department Head'),
        ('employee',   'Employee'),
    ]

    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    emp_id     = models.CharField(max_length=20, unique=True)
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name='members')
    is_approved = models.BooleanField(default=False)
    joined_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.emp_id})"

    # ── Convenience helpers ──────────────────────────────────────────────
    @property
    def is_hr_admin(self):
        return self.role == 'hr_admin'

    @property
    def is_dept_head(self):
        return self.role == 'dept_head'

    @property
    def is_employee(self):
        return self.role == 'employee'

    @property
    def can_manage(self):
        """True if the user can add/edit/delete resources."""
        return self.role in ('hr_admin', 'dept_head')


class Resource(models.Model):
    TYPE_CHOICES = [
        ('link',     'External Link'),
        ('doc',      'Document'),
        ('video',    'Video'),
        ('tool',     'Tool / App'),
        ('other',    'Other'),
    ]

    title       = models.CharField(max_length=200)
    url         = models.URLField()
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='link')
    department  = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='resources')
    added_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='resources')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    tags        = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")

    def __str__(self):
        return self.title

    def tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    class Meta:
        ordering = ['-created_at']