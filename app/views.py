"""
Views for CivicPulse Grievance Portal
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import User, Complaint, StatusHistory, Feedback, Notification
from .forms import (
    RegistrationForm, LoginForm, ComplaintForm, ComplaintUpdateForm,
    AssignOfficerForm, FeedbackForm, UserProfileForm, ComplaintSearchForm
)
from .ai_detection import detect_issue


# ============== PUBLIC VIEWS ==============

def home(request):
    """Home page with portal introduction and statistics."""
    stats = {
        'total_complaints': Complaint.objects.count(),
        'resolved': Complaint.objects.filter(status='resolved').count(),
        'in_progress': Complaint.objects.filter(status='in_progress').count(),
        'pending': Complaint.objects.filter(status__in=['submitted', 'under_review', 'assigned']).count(),
    }
    return render(request, 'home.html', {'stats': stats})


def register(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to CivicPulse.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()
    
    return render(request, 'auth/register.html', {'form': form})


def user_login(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.name}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    
    return render(request, 'auth/login.html', {'form': form})


def user_logout(request):
    """User logout view."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


def admin_login(request):
    """Admin-specific login view. Only allows users with the 'admin' role."""
    if request.user.is_authenticated:
        if request.user.is_admin_user:
            return redirect('all_complaints')
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.role == 'admin':
                login(request, user)
                messages.success(request, f'Welcome, Admin {user.name}!')
                return redirect('all_complaints')
            else:
                messages.error(request, 'Access denied. This login is for admins only.')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'auth/admin_login.html', {'form': form})


def officer_login(request):
    """Officer-specific login view. Only allows users with the 'officer' role."""
    if request.user.is_authenticated:
        if request.user.is_officer:
            return redirect('officer_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.role == 'officer':
                login(request, user)
                messages.success(request, f'Welcome, Officer {user.name}!')
                return redirect('officer_dashboard')
            else:
                messages.error(request, 'Access denied. This login is for officers only.')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'auth/officer_login.html', {'form': form})


def track_complaint(request):
    """Public complaint tracking by ID."""
    complaint = None
    form = ComplaintSearchForm()
    
    if request.method == 'POST':
        form = ComplaintSearchForm(request.POST)
        if form.is_valid():
            complaint_id = form.cleaned_data['complaint_id']
            try:
                complaint = Complaint.objects.get(complaint_id=complaint_id)
            except Complaint.DoesNotExist:
                messages.error(request, 'Complaint not found. Please check the ID.')
    
    return render(request, 'track_complaint.html', {'form': form, 'complaint': complaint})


# ============== DASHBOARD VIEWS ==============

@login_required
def dashboard(request):
    """Redirect to role-specific dashboard."""
    user = request.user
    if user.is_admin_user:
        return redirect('admin_dashboard')
    elif user.is_officer:
        return redirect('officer_dashboard')
    else:
        return redirect('citizen_dashboard')


@login_required
def citizen_dashboard(request):
    """Citizen dashboard view."""
    if not request.user.is_citizen:
        return redirect('dashboard')
    
    complaints = Complaint.objects.filter(citizen=request.user)
    stats = {
        'total': complaints.count(),
        'pending': complaints.filter(status__in=['submitted', 'under_review', 'assigned']).count(),
        'in_progress': complaints.filter(status='in_progress').count(),
        'resolved': complaints.filter(status='resolved').count(),
    }
    recent_complaints = complaints[:5]
    
    return render(request, 'citizen/dashboard.html', {
        'stats': stats,
        'recent_complaints': recent_complaints
    })


@login_required
def officer_dashboard(request):
    """Officer dashboard view."""
    if not request.user.is_officer:
        return redirect('dashboard')
    
    assigned_complaints = Complaint.objects.filter(assigned_officer=request.user)
    stats = {
        'total_assigned': assigned_complaints.count(),
        'pending': assigned_complaints.filter(status__in=['assigned', 'under_review']).count(),
        'in_progress': assigned_complaints.filter(status='in_progress').count(),
        'resolved': assigned_complaints.filter(status='resolved').count(),
    }
    recent_complaints = assigned_complaints.exclude(status='resolved')[:10]
    
    return render(request, 'officer/dashboard.html', {
        'stats': stats,
        'recent_complaints': recent_complaints
    })


@login_required
def admin_dashboard(request):
    """Admin dashboard view."""
    if not request.user.is_admin_user:
        return redirect('dashboard')
    
    all_complaints = Complaint.objects.all()
    stats = {
        'total': all_complaints.count(),
        'submitted': all_complaints.filter(status='submitted').count(),
        'under_review': all_complaints.filter(status='under_review').count(),
        'assigned': all_complaints.filter(status='assigned').count(),
        'in_progress': all_complaints.filter(status='in_progress').count(),
        'resolved': all_complaints.filter(status='resolved').count(),
        'total_users': User.objects.count(),
        'total_citizens': User.objects.filter(role='citizen').count(),
        'total_officers': User.objects.filter(role='officer').count(),
    }
    
    # Category breakdown
    category_stats = all_complaints.values('category').annotate(count=Count('category'))
    
    recent_complaints = all_complaints[:10]
    
    return render(request, 'admin/dashboard.html', {
        'stats': stats,
        'category_stats': category_stats,
        'recent_complaints': recent_complaints
    })


# ============== COMPLAINT VIEWS ==============

@login_required
def submit_complaint(request):
    """Submit a new complaint."""
    if not request.user.is_citizen:
        messages.error(request, 'Only citizens can submit complaints.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.citizen = request.user
            
            # AI Detection if image uploaded
            if complaint.image:
                detection_result = detect_issue(complaint.image)
                if detection_result:
                    complaint.ai_detected_issue = detection_result['issue']
                    complaint.ai_confidence = detection_result['confidence']
            
            complaint.save()
            
            # Create initial status history
            StatusHistory.objects.create(
                complaint=complaint,
                new_status='submitted',
                changed_by=request.user,
                remarks='Complaint submitted'
            )
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                title='Complaint Submitted',
                message=f'Your complaint {complaint.complaint_id} has been submitted successfully.',
                complaint=complaint
            )
            
            messages.success(request, f'Complaint submitted successfully! Your ID: {complaint.complaint_id}')
            return redirect('complaint_detail', complaint_id=complaint.complaint_id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ComplaintForm()
    
    return render(request, 'citizen/submit_complaint.html', {'form': form})


@login_required
def my_complaints(request):
    """View list of citizen's complaints."""
    if not request.user.is_citizen:
        return redirect('dashboard')
    
    complaints = Complaint.objects.filter(citizen=request.user)
    
    # Filtering
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    if category_filter:
        complaints = complaints.filter(category=category_filter)
    
    # Pagination
    paginator = Paginator(complaints, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'citizen/my_complaints.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'category_filter': category_filter
    })


@login_required
def complaint_detail(request, complaint_id):
    """View complaint details."""
    complaint = get_object_or_404(Complaint, complaint_id=complaint_id)
    
    # Access control
    user = request.user
    if user.is_citizen and complaint.citizen != user:
        messages.error(request, 'You do not have access to this complaint.')
        return redirect('dashboard')
    
    if user.is_officer and complaint.assigned_officer != user:
        messages.error(request, 'This complaint is not assigned to you.')
        return redirect('dashboard')
    
    # Get status history for timeline
    status_history = complaint.status_history.all()
    
    # Check if feedback exists
    has_feedback = hasattr(complaint, 'feedback')
    
    return render(request, 'complaint_detail.html', {
        'complaint': complaint,
        'status_history': status_history,
        'has_feedback': has_feedback
    })


@login_required
def update_complaint_status(request, complaint_id):
    """Officer updates complaint status."""
    if not request.user.is_officer:
        messages.error(request, 'Only officers can update complaints.')
        return redirect('dashboard')
    
    complaint = get_object_or_404(Complaint, complaint_id=complaint_id, assigned_officer=request.user)
    old_status = complaint.status
    
    if request.method == 'POST':
        form = ComplaintUpdateForm(request.POST, instance=complaint)
        if form.is_valid():
            complaint = form.save()
            
            # Create status history entry
            if old_status != complaint.status:
                StatusHistory.objects.create(
                    complaint=complaint,
                    old_status=old_status,
                    new_status=complaint.status,
                    changed_by=request.user,
                    remarks=complaint.officer_remarks
                )
                
                # Notify citizen
                Notification.objects.create(
                    user=complaint.citizen,
                    title='Complaint Status Updated',
                    message=f'Your complaint {complaint.complaint_id} status changed to {complaint.get_status_display()}.',
                    complaint=complaint
                )
                
                # Send email notification (optional)
                try:
                    send_mail(
                        subject=f'Complaint {complaint.complaint_id} - Status Update',
                        message=f'Your complaint status has been updated to: {complaint.get_status_display()}',
                        from_email=settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'noreply@civicpulse.ai',
                        recipient_list=[complaint.citizen.email],
                        fail_silently=True
                    )
                except Exception:
                    pass
            
            messages.success(request, 'Complaint updated successfully.')
            return redirect('complaint_detail', complaint_id=complaint.complaint_id)
    else:
        form = ComplaintUpdateForm(instance=complaint)
    
    return render(request, 'officer/update_complaint.html', {
        'form': form,
        'complaint': complaint
    })


@login_required
def assigned_complaints(request):
    """View officer's assigned complaints."""
    if not request.user.is_officer:
        return redirect('dashboard')
    
    complaints = Complaint.objects.filter(assigned_officer=request.user)
    
    # Filtering
    status_filter = request.GET.get('status', '')
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(complaints, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'officer/assigned_complaints.html', {
        'page_obj': page_obj,
        'status_filter': status_filter
    })


# ============== ADMIN VIEWS ==============

@login_required
def all_complaints(request):
    """Admin view all complaints."""
    if not request.user.is_admin_user:
        return redirect('dashboard')
    
    complaints = Complaint.objects.all()
    
    # Filtering
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    search = request.GET.get('search', '')
    
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    if category_filter:
        complaints = complaints.filter(category=category_filter)
    if search:
        complaints = complaints.filter(
            Q(complaint_id__icontains=search) |
            Q(title__icontains=search) |
            Q(citizen__name__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(complaints, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/all_complaints.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'search': search
    })


@login_required
def assign_officer(request, complaint_id):
    """Admin assigns officer to complaint."""
    if not request.user.is_admin_user:
        messages.error(request, 'Only admins can assign officers.')
        return redirect('dashboard')
    
    complaint = get_object_or_404(Complaint, complaint_id=complaint_id)
    
    if request.method == 'POST':
        form = AssignOfficerForm(request.POST, instance=complaint)
        if form.is_valid():
            complaint = form.save()
            if complaint.assigned_officer:
                complaint.status = 'assigned'
                complaint.save()
                
                # Create status history
                StatusHistory.objects.create(
                    complaint=complaint,
                    old_status='submitted',
                    new_status='assigned',
                    changed_by=request.user,
                    remarks=f'Assigned to {complaint.assigned_officer.name}'
                )
                
                # Notify officer
                Notification.objects.create(
                    user=complaint.assigned_officer,
                    title='New Complaint Assigned',
                    message=f'Complaint {complaint.complaint_id} has been assigned to you.',
                    complaint=complaint
                )
                
                # Notify citizen
                Notification.objects.create(
                    user=complaint.citizen,
                    title='Officer Assigned',
                    message=f'An officer has been assigned to your complaint {complaint.complaint_id}.',
                    complaint=complaint
                )
            
            messages.success(request, 'Officer assigned successfully.')
            return redirect('all_complaints')
    else:
        form = AssignOfficerForm(instance=complaint)
    
    return render(request, 'admin/assign_officer.html', {
        'form': form,
        'complaint': complaint
    })


@login_required
def manage_users(request):
    """Admin manages users."""
    if not request.user.is_admin_user:
        return redirect('dashboard')
    
    users = User.objects.all().order_by('-created_at')
    
    # Filtering
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/manage_users.html', {
        'page_obj': page_obj,
        'role_filter': role_filter
    })


@login_required
def update_user_role(request, user_id):
    """Admin updates user role."""
    if not request.user.is_admin_user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get('role')
        
        if new_role in ['citizen', 'officer', 'admin']:
            user.role = new_role
            user.save()
            return JsonResponse({'success': True, 'message': f'Role updated to {new_role}'})
        else:
            return JsonResponse({'error': 'Invalid role'}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ============== FEEDBACK & PROFILE VIEWS ==============

@login_required
def submit_feedback(request, complaint_id):
    """Citizen submits feedback for resolved complaint."""
    if not request.user.is_citizen:
        return redirect('dashboard')
    
    complaint = get_object_or_404(Complaint, complaint_id=complaint_id, citizen=request.user)
    
    if complaint.status != 'resolved':
        messages.error(request, 'You can only submit feedback for resolved complaints.')
        return redirect('complaint_detail', complaint_id=complaint_id)
    
    if hasattr(complaint, 'feedback'):
        messages.info(request, 'You have already submitted feedback for this complaint.')
        return redirect('complaint_detail', complaint_id=complaint_id)
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.complaint = complaint
            feedback.citizen = request.user
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('complaint_detail', complaint_id=complaint_id)
    else:
        form = FeedbackForm()
    
    return render(request, 'citizen/submit_feedback.html', {
        'form': form,
        'complaint': complaint
    })


@login_required
def profile(request):
    """User profile view and edit."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'profile.html', {'form': form})


@login_required
def notifications(request):
    """View user notifications."""
    user_notifications = Notification.objects.filter(user=request.user)
    
    # Mark as read
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        if notification_id:
            Notification.objects.filter(id=notification_id, user=request.user).update(is_read=True)
            return JsonResponse({'success': True})
    
    # Pagination
    paginator = Paginator(user_notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'notifications.html', {'page_obj': page_obj})


# ============== API VIEWS ==============

def api_complaints_stats(request):
    """API endpoint for complaint statistics."""
    stats = {
        'total': Complaint.objects.count(),
        'submitted': Complaint.objects.filter(status='submitted').count(),
        'under_review': Complaint.objects.filter(status='under_review').count(),
        'assigned': Complaint.objects.filter(status='assigned').count(),
        'in_progress': Complaint.objects.filter(status='in_progress').count(),
        'resolved': Complaint.objects.filter(status='resolved').count(),
    }
    return JsonResponse(stats)


def api_category_stats(request):
    """API endpoint for category statistics."""
    stats = list(
        Complaint.objects.values('category')
        .annotate(count=Count('category'))
        .order_by('-count')
    )
    return JsonResponse({'categories': stats})

def create_admin_once(request):
    from django.http import HttpResponse
    try:
        if not User.objects.filter(email='admin@civicpulse.com').exists():
            User.objects.create_superuser(
                email='admin@civicpulse.com',
                password='admin123',
                name='Admin',
                role='admin'
            )
            return HttpResponse('Admin created! Visit /admin-login/ to login. DELETE THIS URL NOW!')
        else:
            return HttpResponse('Admin already exists!')
    except Exception as e:
        return HttpResponse(f'Error: {e}')


