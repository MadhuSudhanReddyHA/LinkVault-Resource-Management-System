from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count

from .models import UserProfile, Department, Resource
from .forms  import RegisterForm, DepartmentForm, AssignHeadForm, ResourceForm


# ════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════

def get_profile(user):
    """Return the UserProfile; create a stub if missing (e.g. superuser)."""
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={'emp_id': f'ADMIN-{user.pk}', 'role': 'hr_admin', 'is_approved': True}
    )
    return profile


def require_approved(view_func):
    """Decorator: user must be logged in AND approved."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        profile = get_profile(request.user)
        if not profile.is_approved:
            logout(request)
            messages.error(request, "Your account is awaiting HR approval.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def require_hr(view_func):
    def wrapper(request, *args, **kwargs):
        profile = get_profile(request.user)
        if not profile.is_hr_admin:
            messages.error(request, "Access denied.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return require_approved(wrapper)


def require_manager(view_func):
    """Dept Head OR HR Admin."""
    def wrapper(request, *args, **kwargs):
        profile = get_profile(request.user)
        if not profile.can_manage:
            messages.error(request, "Access denied.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return require_approved(wrapper)


# ════════════════════════════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════════════════════════════

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        try:
            username = User.objects.get(email=email).username
        except User.DoesNotExist:
            username = email

        user = authenticate(request, username=username, password=password)
        if user:
            profile = get_profile(user)
            if not profile.is_approved:
                messages.warning(request, "Your account is pending HR approval. Please check back later.")
            else:
                login(request, user)
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, 'auth/login.html')


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        user = User.objects.create_user(
            username=d['email'],
            email=d['email'],
            password=d['password'],
            first_name=d['first_name'],
            last_name=d['last_name'],
        )
        UserProfile.objects.create(
            user=user,
            emp_id=d['emp_id'],
            role='employee',
            is_approved=False,
        )
        messages.success(request, "Registration successful! An HR Admin will review your account.")
        return redirect('login')

    return render(request, 'auth/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ════════════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════════════

@require_approved
def dashboard_view(request):
    profile = get_profile(request.user)

    if profile.is_hr_admin:
        stats = {
            'total_depts':     Department.objects.count(),
            'total_users':     UserProfile.objects.filter(is_approved=True).count(),
            'total_resources': Resource.objects.count(),
            'pending_count':   UserProfile.objects.filter(is_approved=False).count(),
        }
        recent_resources = Resource.objects.select_related('department', 'added_by').order_by('-created_at')[:6]
        dept_stats = Department.objects.annotate(
            member_count=Count('members'), resource_count=Count('resources')
        )
    else:
        dept = profile.department
        stats = {
            'total_depts':     1 if dept else 0,
            'total_users':     UserProfile.objects.filter(department=dept, is_approved=True).count() if dept else 0,
            'total_resources': Resource.objects.filter(department=dept).count() if dept else 0,
            'pending_count':   0,
        }
        recent_resources = Resource.objects.filter(department=dept).select_related('added_by').order_by('-created_at')[:6] if dept else []
        dept_stats = Department.objects.filter(pk=dept.pk).annotate(
            member_count=Count('members'), resource_count=Count('resources')
        ) if dept else []

    return render(request, 'portal/dashboard.html', {
        'profile': profile,
        'stats':   stats,
        'recent_resources': recent_resources,
        'dept_stats': dept_stats,
    })


# ════════════════════════════════════════════════════════════════
#  DEPARTMENTS
# ════════════════════════════════════════════════════════════════

@require_approved
def departments_view(request):
    profile = get_profile(request.user)
    departments = Department.objects.annotate(
        member_count=Count('members'), resource_count=Count('resources')
    ).prefetch_related('head__profile')

    return render(request, 'portal/departments.html', {
        'profile':     profile,
        'departments': departments,
        'form':        DepartmentForm(),
    })


@require_hr
def dept_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department created.")
        else:
            messages.error(request, "Invalid form data.")
    return redirect('departments')


@require_hr
def dept_delete(request, dept_id):
    dept = get_object_or_404(Department, pk=dept_id)
    dept.delete()
    messages.success(request, f'"{dept.name}" deleted.')
    return redirect('departments')


@require_hr
def dept_assign_head(request, dept_id):
    dept = get_object_or_404(Department, pk=dept_id)
    form = AssignHeadForm(dept, request.POST)
    if form.is_valid():
        new_head = form.cleaned_data['head']
        # Demote old head if different person
        if dept.head and dept.head != new_head:
            old = get_profile(dept.head)
            if old.role == 'dept_head':
                old.role = 'employee'
                old.save()
        dept.head = new_head
        dept.save()
        head_profile = get_profile(new_head)
        head_profile.role = 'dept_head'
        head_profile.department = dept
        head_profile.save()
        messages.success(request, f"{new_head.get_full_name()} is now head of {dept.name}.")
    return redirect('departments')


# ════════════════════════════════════════════════════════════════
#  RESOURCES
# ════════════════════════════════════════════════════════════════

@require_approved
def resources_view(request):
    profile = get_profile(request.user)
    dept_filter = request.GET.get('dept')
    search      = request.GET.get('q', '').strip()
    type_filter = request.GET.get('type', '')

    if profile.is_hr_admin:
        qs = Resource.objects.all()
        departments = Department.objects.all()
    else:
        qs = Resource.objects.filter(department=profile.department)
        departments = Department.objects.filter(pk=profile.department_id) if profile.department else Department.objects.none()

    if dept_filter:
        qs = qs.filter(department_id=dept_filter)
    if search:
        qs = qs.filter(title__icontains=search) | qs.filter(description__icontains=search) | qs.filter(tags__icontains=search)
    if type_filter:
        qs = qs.filter(resource_type=type_filter)

    qs = qs.select_related('department', 'added_by').order_by('-created_at')

    form = ResourceForm(profile)
    return render(request, 'portal/resources.html', {
        'profile':     profile,
        'resources':   qs,
        'departments': departments,
        'form':        form,
        'search':      search,
        'dept_filter': dept_filter,
        'type_filter': type_filter,
        'type_choices': Resource.TYPE_CHOICES,
    })


@require_approved
def resource_add(request):
    profile = get_profile(request.user)
    if request.method == 'POST':
        form = ResourceForm(profile, request.POST)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.added_by = request.user
            resource.save()
            messages.success(request, f'"{resource.title}" added.')
        else:
            messages.error(request, "Please fix the errors below.")
    return redirect('resources')


@require_manager
def resource_delete(request, res_id):
    resource = get_object_or_404(Resource, pk=res_id)
    profile  = get_profile(request.user)
    # Dept head can only delete their dept's resources
    if profile.is_dept_head and resource.department != profile.department:
        messages.error(request, "Access denied.")
        return redirect('resources')
    resource.delete()
    messages.success(request, "Resource deleted.")
    return redirect('resources')


@require_manager
def resource_edit(request, res_id):
    resource = get_object_or_404(Resource, pk=res_id)
    profile  = get_profile(request.user)
    if profile.is_dept_head and resource.department != profile.department:
        messages.error(request, "Access denied.")
        return redirect('resources')
    form = ResourceForm(profile, request.POST or None, instance=resource)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Resource updated.")
        return redirect('resources')
    return render(request, 'portal/resource_edit.html', {'form': form, 'profile': profile, 'resource': resource})


# ════════════════════════════════════════════════════════════════
#  PEOPLE
# ════════════════════════════════════════════════════════════════

@require_approved
def people_view(request):
    profile = get_profile(request.user)

    if profile.is_hr_admin:
        approved = UserProfile.objects.filter(is_approved=True).select_related('user', 'department').order_by('user__first_name')
        pending  = UserProfile.objects.filter(is_approved=False).select_related('user')
        departments = Department.objects.all()
    elif profile.is_dept_head:
        approved = UserProfile.objects.filter(department=profile.department, is_approved=True).select_related('user')
        pending  = UserProfile.objects.none()
        departments = Department.objects.none()
    else:
        approved = UserProfile.objects.filter(department=profile.department, is_approved=True).select_related('user')
        pending  = UserProfile.objects.none()
        departments = Department.objects.none()

    return render(request, 'portal/people.html', {
        'profile':     profile,
        'approved':    approved,
        'pending':     pending,
        'departments': departments,
    })


@require_hr
def approve_user(request, profile_id):
    up = get_object_or_404(UserProfile, pk=profile_id)
    up.is_approved = True
    up.save()
    messages.success(request, f"{up.user.get_full_name()} approved.")
    return redirect('people')


@require_hr
def reject_user(request, profile_id):
    up = get_object_or_404(UserProfile, pk=profile_id)
    name = up.user.get_full_name()
    up.user.delete()   # cascade-deletes profile
    messages.success(request, f"{name} rejected and removed.")
    return redirect('people')


@require_hr
def assign_dept_to_user(request, profile_id):
    up   = get_object_or_404(UserProfile, pk=profile_id)
    dept_id = request.POST.get('department')
    if dept_id:
        up.department = get_object_or_404(Department, pk=dept_id)
        up.save()
        messages.success(request, f"{up.user.get_full_name()} assigned to {up.department.name}.")
    return redirect('people')


@require_manager
def remove_from_dept(request, profile_id):
    up      = get_object_or_404(UserProfile, pk=profile_id)
    manager = get_profile(request.user)
    if manager.is_dept_head and up.department != manager.department:
        messages.error(request, "Access denied.")
        return redirect('people')
    up.department = None
    if up.role == 'dept_head':
        up.role = 'employee'
    up.save()
    messages.success(request, f"{up.user.get_full_name()} removed from department.")
    return redirect('people')


@require_hr
def change_role(request, profile_id):
    up   = get_object_or_404(UserProfile, pk=profile_id)
    role = request.POST.get('role')
    if role in dict(UserProfile.ROLE_CHOICES):
        up.role = role
        up.save()
        messages.success(request, f"Role updated to {up.get_role_display()}.")
    return redirect('people')
# Add this at the bottom of core/views.py

def global_context(request):
    """Injects pending_count into every template for the sidebar badge."""
    if request.user.is_authenticated:
        try:
            profile = get_profile(request.user)
            pending_count = UserProfile.objects.filter(is_approved=False).count() if profile.is_hr_admin else 0
            return {'profile': profile, 'pending_count': pending_count}
        except Exception:
            pass
    return {}