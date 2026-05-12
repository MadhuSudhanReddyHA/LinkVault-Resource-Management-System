from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Department, Resource


class RegisterForm(forms.Form):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name  = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email      = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Work Email'}))
    emp_id     = forms.CharField(max_length=20, label="Employee ID", widget=forms.TextInput(attrs={'placeholder': 'e.g. EMP-001'}))
    password   = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    confirm    = forms.CharField(label="Confirm Password", widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}))

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_emp_id(self):
        emp_id = self.cleaned_data['emp_id']
        if UserProfile.objects.filter(emp_id=emp_id).exists():
            raise forms.ValidationError("This Employee ID is already taken.")
        return emp_id

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm'):
            self.add_error('confirm', "Passwords do not match.")
        return cleaned


class DepartmentForm(forms.ModelForm):
    class Meta:
        model  = Department
        fields = ['name', 'description']
        widgets = {
            'name':        forms.TextInput(attrs={'placeholder': 'Department name'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Brief description…'}),
        }


class AssignHeadForm(forms.Form):
    head = forms.ModelChoiceField(
        queryset=User.objects.none(),
        empty_label="— Select a member —",
        label="Department Head"
    )

    def __init__(self, department, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['head'].queryset = User.objects.filter(
            profile__department=department,
            profile__is_approved=True
        ).exclude(pk=department.head_id if department.head_id else None)


class ResourceForm(forms.ModelForm):
    class Meta:
        model  = Resource
        fields = ['title', 'url', 'description', 'resource_type', 'department', 'tags']
        widgets = {
            'title':       forms.TextInput(attrs={'placeholder': 'Resource title'}),
            'url':         forms.URLInput(attrs={'placeholder': 'https://…'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'What is this resource about?'}),
            'tags':        forms.TextInput(attrs={'placeholder': 'e.g. onboarding, policy, hr'}),
        }

    def __init__(self, user_profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user_profile.is_hr_admin:
            self.fields['department'].queryset = Department.objects.all()
        else:
            self.fields['department'].queryset = Department.objects.filter(pk=user_profile.department_id)
            self.fields['department'].initial  = user_profile.department
            self.fields['department'].widget   = forms.HiddenInput()