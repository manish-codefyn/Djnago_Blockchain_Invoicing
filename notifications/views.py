from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Notification

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

class UnreadNotificationListView(NotificationListView):
    def get_queryset(self):
        return super().get_queryset().filter(is_read=False)

def mark_as_read(request, pk):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.mark_as_read()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

def mark_all_as_read(request):
    if request.method == 'POST':
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        return JsonResponse({'success': True, 'marked_read': updated})
    return JsonResponse({'success': False}, status=400)

def get_notification_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return JsonResponse({'count': count})
    return JsonResponse({'count': 0})

def get_latest_notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:5]
        
        data = [{
            'id': str(n.id),
            'message': n.template.name,
            'is_read': n.is_read,
            'url': n.get_absolute_url(),
            'time': n.created_at.strftime('%b %d, %I:%M %p')
        } for n in notifications]
        
        return JsonResponse({'notifications': data})
    return JsonResponse({'notifications': []})