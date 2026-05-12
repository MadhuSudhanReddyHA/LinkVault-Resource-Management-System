from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile, Department, Resource


class Command(BaseCommand):
    help = "Seeds demo data for LinkVault showcase"

    def handle(self, *args, **kwargs):
        self.stdout.write("🌱  Seeding LinkVault demo data…")

        # ── Departments ──────────────────────────────────────────
        hr_dept,  _ = Department.objects.get_or_create(name="Human Resources",   defaults={'description': 'Manages people, policies, and culture.'})
        eng_dept, _ = Department.objects.get_or_create(name="Engineering",        defaults={'description': 'Product development and infrastructure.'})
        mkt_dept, _ = Department.objects.get_or_create(name="Marketing",          defaults={'description': 'Brand, content, and growth.'})
        fin_dept, _ = Department.objects.get_or_create(name="Finance",            defaults={'description': 'Budgets, payroll, and accounting.'})

        # ── HR Admin ─────────────────────────────────────────────
        admin_user, created = User.objects.get_or_create(
            username='admin@linkvault.com',
            defaults=dict(email='admin@linkvault.com', first_name='Alex', last_name='Rivera')
        )
        if created:
            admin_user.set_password('Admin@123')
            admin_user.save()
        UserProfile.objects.update_or_create(
            user=admin_user,
            defaults=dict(emp_id='EMP-001', role='hr_admin', department=hr_dept, is_approved=True)
        )

        # ── Dept Head (Engineering) ───────────────────────────────
        sarah, created = User.objects.get_or_create(
            username='sarah@linkvault.com',
            defaults=dict(email='sarah@linkvault.com', first_name='Sarah', last_name='Chen')
        )
        if created:
            sarah.set_password('Demo@123')
            sarah.save()
        UserProfile.objects.update_or_create(
            user=sarah,
            defaults=dict(emp_id='EMP-002', role='dept_head', department=eng_dept, is_approved=True)
        )
        eng_dept.head = sarah
        eng_dept.save()

        # ── Employee ──────────────────────────────────────────────
        john, created = User.objects.get_or_create(
            username='john@linkvault.com',
            defaults=dict(email='john@linkvault.com', first_name='John', last_name='Doe')
        )
        if created:
            john.set_password('Demo@123')
            john.save()
        UserProfile.objects.update_or_create(
            user=john,
            defaults=dict(emp_id='EMP-003', role='employee', department=eng_dept, is_approved=True)
        )

        # ── Pending user ──────────────────────────────────────────
        pending, created = User.objects.get_or_create(
            username='pending@linkvault.com',
            defaults=dict(email='pending@linkvault.com', first_name='Jamie', last_name='Park')
        )
        if created:
            pending.set_password('Demo@123')
            pending.save()
        UserProfile.objects.update_or_create(
            user=pending,
            defaults=dict(emp_id='EMP-099', role='employee', department=None, is_approved=False)
        )

        # ── Resources ─────────────────────────────────────────────
        resources = [
            dict(title="Employee Handbook 2024",      url="https://example.com/handbook",      description="Official HR policies and guidelines.", resource_type="doc",   department=hr_dept,  added_by=admin_user, tags="policy, onboarding, hr"),
            dict(title="Leave Request Portal",         url="https://example.com/leave",         description="Submit and track leave requests.",     resource_type="tool",  department=hr_dept,  added_by=admin_user, tags="leave, hr, portal"),
            dict(title="Benefits Overview",            url="https://example.com/benefits",      description="Health, dental, and vision benefits.",  resource_type="doc",   department=hr_dept,  added_by=admin_user, tags="benefits, health"),
            dict(title="GitHub Organization",          url="https://github.com",                description="Company GitHub for all repositories.", resource_type="tool",  department=eng_dept, added_by=sarah,      tags="git, code, repos"),
            dict(title="System Architecture Diagram",  url="https://example.com/arch",          description="High-level system design overview.",   resource_type="doc",   department=eng_dept, added_by=sarah,      tags="architecture, design"),
            dict(title="API Documentation",            url="https://example.com/api-docs",      description="REST API reference for all services.", resource_type="link",  department=eng_dept, added_by=john,       tags="api, docs, reference"),
            dict(title="CI/CD Pipeline Guide",         url="https://example.com/cicd",          description="Setup and manage deployment pipelines.",resource_type="doc",   department=eng_dept, added_by=sarah,      tags="devops, ci, cd"),
            dict(title="Brand Style Guide",            url="https://example.com/brand",         description="Logos, colors, fonts, and tone of voice.", resource_type="doc", department=mkt_dept, added_by=admin_user, tags="brand, design, marketing"),
            dict(title="Content Calendar Template",    url="https://example.com/content-cal",   description="Monthly content planning spreadsheet.",resource_type="doc",   department=mkt_dept, added_by=admin_user, tags="content, calendar, social"),
            dict(title="Q3 Budget Tracker",            url="https://example.com/budget",        description="Finance team quarterly budget tracker.", resource_type="tool", department=fin_dept, added_by=admin_user, tags="budget, finance, q3"),
        ]

        for r in resources:
            Resource.objects.get_or_create(title=r['title'], department=r['department'], defaults=r)

        self.stdout.write(self.style.SUCCESS("✅  Demo data seeded successfully!\n"))
        self.stdout.write("  👤  admin@linkvault.com  /  Admin@123  (HR Admin)")
        self.stdout.write("  👤  sarah@linkvault.com  /  Demo@123   (Dept Head — Engineering)")
        self.stdout.write("  👤  john@linkvault.com   /  Demo@123   (Employee — Engineering)")
        self.stdout.write("  ⏳  pending@linkvault.com — awaiting approval\n")