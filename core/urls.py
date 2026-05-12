from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('',          views.login_view,    name='login'),
    path('login/',    views.login_view,    name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/',   views.logout_view,   name='logout'),

    # Portal
    path('dashboard/',   views.dashboard_view,  name='dashboard'),
    path('departments/', views.departments_view, name='departments'),
    path('resources/',   views.resources_view,   name='resources'),
    path('people/',      views.people_view,      name='people'),

    # Department actions
    path('departments/create/',              views.dept_create,       name='dept_create'),
    path('departments/<int:dept_id>/delete/',views.dept_delete,       name='dept_delete'),
    path('departments/<int:dept_id>/head/',  views.dept_assign_head,  name='dept_assign_head'),

    # Resource actions
    path('resources/add/',               views.resource_add,    name='resource_add'),
    path('resources/<int:res_id>/edit/', views.resource_edit,   name='resource_edit'),
    path('resources/<int:res_id>/delete/',views.resource_delete, name='resource_delete'),

    # People actions
    path('people/<int:profile_id>/approve/',    views.approve_user,        name='approve_user'),
    path('people/<int:profile_id>/reject/',     views.reject_user,         name='reject_user'),
    path('people/<int:profile_id>/assign-dept/',views.assign_dept_to_user, name='assign_dept'),
    path('people/<int:profile_id>/remove-dept/',views.remove_from_dept,    name='remove_from_dept'),
    path('people/<int:profile_id>/role/',       views.change_role,         name='change_role'),
]