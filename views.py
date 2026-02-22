"""
Messaging Module Views

Dashboard, message log, compose, templates CRUD, campaigns CRUD, settings,
and API endpoints for programmatic sending and delivery webhooks.
"""
import json

from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render as django_render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib import messages as django_messages

from apps.accounts.decorators import login_required
from apps.core.htmx import htmx_view
from apps.modules_runtime.navigation import with_module_nav

from .models import (
    Message,
    MessageTemplate,
    Campaign,
    MessagingSettings,
    MessageStatusChoices,
    CampaignStatusChoices,
)
from .forms import (
    MessageForm,
    MessageTemplateForm,
    CampaignForm,
    MessagingSettingsForm,
)


# ============================================================================
# Helpers
# ============================================================================

def _hub_id(request):
    return request.session.get('hub_id')


PER_PAGE = 25


# ============================================================================
# Dashboard
# ============================================================================

@login_required
@with_module_nav('messaging', 'dashboard')
@htmx_view('messaging/pages/dashboard.html', 'messaging/partials/dashboard_content.html')
def dashboard(request):
    """Messaging overview: sent today, delivery rate, recent messages."""
    hub = _hub_id(request)
    today = timezone.now().date()

    total_messages = Message.objects.filter(hub_id=hub, is_deleted=False).count()
    sent_today = Message.objects.filter(
        hub_id=hub, is_deleted=False,
        created_at__date=today,
    ).count()
    delivered_count = Message.objects.filter(
        hub_id=hub, is_deleted=False,
        status__in=['delivered', 'read'],
    ).count()
    failed_count = Message.objects.filter(
        hub_id=hub, is_deleted=False,
        status='failed',
    ).count()
    delivery_rate = round((delivered_count / total_messages * 100), 1) if total_messages > 0 else 0

    recent_messages = Message.objects.filter(
        hub_id=hub, is_deleted=False,
    ).order_by('-created_at')[:10]

    active_campaigns = Campaign.objects.filter(
        hub_id=hub, is_deleted=False,
        status__in=['sending', 'scheduled'],
    ).count()

    template_count = MessageTemplate.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True,
    ).count()

    return {
        'total_messages': total_messages,
        'sent_today': sent_today,
        'delivered_count': delivered_count,
        'failed_count': failed_count,
        'delivery_rate': delivery_rate,
        'recent_messages': recent_messages,
        'active_campaigns': active_campaigns,
        'template_count': template_count,
    }


# ============================================================================
# Messages
# ============================================================================

@login_required
@with_module_nav('messaging', 'messages')
@htmx_view('messaging/pages/messages.html', 'messaging/partials/messages_content.html')
def messages_list(request):
    """Message log with filters (channel, status, date range)."""
    hub = _hub_id(request)
    search_query = request.GET.get('q', '').strip()
    channel_filter = request.GET.get('channel', '')
    status_filter = request.GET.get('status', '')

    qs = Message.objects.filter(hub_id=hub, is_deleted=False)

    if channel_filter:
        qs = qs.filter(channel=channel_filter)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if search_query:
        qs = qs.filter(
            Q(recipient_name__icontains=search_query) |
            Q(recipient_contact__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(body__icontains=search_query)
        )

    paginator = Paginator(qs, PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'messages_list': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'channel_filter': channel_filter,
        'status_filter': status_filter,
    }

    if request.htmx and request.htmx.target == 'messages-list-body':
        return django_render(request, 'messaging/partials/messages_list_rows.html', context)

    return context


@login_required
@with_module_nav('messaging', 'messages')
@htmx_view('messaging/pages/message_detail.html', 'messaging/partials/message_detail_content.html')
def message_detail(request, pk):
    """View a single message."""
    hub = _hub_id(request)
    message = get_object_or_404(Message, pk=pk, hub_id=hub, is_deleted=False)
    return {'message': message}


@login_required
@with_module_nav('messaging', 'messages')
@htmx_view('messaging/pages/compose.html', 'messaging/partials/compose_content.html')
def send_message(request):
    """Compose and send a single message."""
    hub = _hub_id(request)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.hub_id = hub
            message.status = MessageStatusChoices.QUEUED
            message.save()

            # In a real implementation, this would queue the message for sending
            # For now, we just mark it as sent
            message.mark_sent()

            django_messages.success(request, _('Message sent successfully'))
            return django_render(request, 'messaging/partials/messages_content.html', {
                'messages_list': Message.objects.filter(hub_id=hub, is_deleted=False)[:PER_PAGE],
                'page_obj': None,
                'search_query': '',
                'channel_filter': '',
                'status_filter': '',
            })
        else:
            django_messages.error(request, _('Please correct the errors below'))
    else:
        # Pre-fill from query params (e.g., from customer detail)
        initial = {}
        customer_id = request.GET.get('customer')
        channel = request.GET.get('channel')
        if channel:
            initial['channel'] = channel
        if customer_id:
            try:
                from customers.models import Customer
                customer = Customer.objects.get(pk=customer_id, hub_id=hub, is_deleted=False)
                initial['customer'] = customer.pk
                initial['recipient_name'] = customer.name
                if channel == 'email':
                    initial['recipient_contact'] = customer.email
                else:
                    initial['recipient_contact'] = customer.phone
            except Exception:
                pass
        form = MessageForm(initial=initial)

    templates = MessageTemplate.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True,
    ).order_by('name')

    return {
        'form': form,
        'templates': templates,
    }


# ============================================================================
# Templates
# ============================================================================

@login_required
@with_module_nav('messaging', 'templates')
@htmx_view('messaging/pages/templates.html', 'messaging/partials/templates_content.html')
def templates_list(request):
    """Template list."""
    hub = _hub_id(request)
    search_query = request.GET.get('q', '').strip()

    qs = MessageTemplate.objects.filter(hub_id=hub, is_deleted=False)
    if search_query:
        qs = qs.filter(
            Q(name__icontains=search_query) |
            Q(body__icontains=search_query)
        )

    return {
        'templates': qs,
        'search_query': search_query,
    }


@login_required
@with_module_nav('messaging', 'templates')
@htmx_view('messaging/pages/template_form.html', 'messaging/partials/template_form_content.html')
def template_create(request):
    """Create a new template."""
    hub = _hub_id(request)

    if request.method == 'POST':
        form = MessageTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.hub_id = hub
            template.save()
            django_messages.success(request, _('Template created successfully'))
            return django_render(request, 'messaging/partials/templates_content.html', {
                'templates': MessageTemplate.objects.filter(hub_id=hub, is_deleted=False),
                'search_query': '',
            })
    else:
        form = MessageTemplateForm()

    return {
        'form': form,
        'is_edit': False,
    }


@login_required
@with_module_nav('messaging', 'templates')
@htmx_view('messaging/pages/template_form.html', 'messaging/partials/template_form_content.html')
def template_edit(request, pk):
    """Edit an existing template."""
    hub = _hub_id(request)
    template = get_object_or_404(MessageTemplate, pk=pk, hub_id=hub, is_deleted=False)

    if request.method == 'POST':
        form = MessageTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            django_messages.success(request, _('Template updated successfully'))
            return django_render(request, 'messaging/partials/templates_content.html', {
                'templates': MessageTemplate.objects.filter(hub_id=hub, is_deleted=False),
                'search_query': '',
            })
    else:
        form = MessageTemplateForm(instance=template)

    return {
        'form': form,
        'template': template,
        'is_edit': True,
    }


@login_required
@require_POST
def template_delete(request, pk):
    """Soft-delete a template."""
    hub = _hub_id(request)
    template = get_object_or_404(MessageTemplate, pk=pk, hub_id=hub, is_deleted=False)

    if template.is_system:
        django_messages.error(request, _('System templates cannot be deleted'))
    else:
        template.delete()
        django_messages.success(request, _('Template deleted successfully'))

    templates = MessageTemplate.objects.filter(hub_id=hub, is_deleted=False)
    return django_render(request, 'messaging/partials/templates_content.html', {
        'templates': templates,
        'search_query': '',
    })


# ============================================================================
# Campaigns
# ============================================================================

@login_required
@with_module_nav('messaging', 'campaigns')
@htmx_view('messaging/pages/campaigns.html', 'messaging/partials/campaigns_content.html')
def campaigns_list(request):
    """Campaign list."""
    hub = _hub_id(request)
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    qs = Campaign.objects.filter(hub_id=hub, is_deleted=False)
    if status_filter:
        qs = qs.filter(status=status_filter)
    if search_query:
        qs = qs.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    return {
        'campaigns': qs,
        'search_query': search_query,
        'status_filter': status_filter,
    }


@login_required
@with_module_nav('messaging', 'campaigns')
@htmx_view('messaging/pages/campaign_form.html', 'messaging/partials/campaign_form_content.html')
def campaign_create(request):
    """Create a new campaign."""
    hub = _hub_id(request)

    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.hub_id = hub
            campaign.save()
            django_messages.success(request, _('Campaign created successfully'))
            return django_render(request, 'messaging/partials/campaigns_content.html', {
                'campaigns': Campaign.objects.filter(hub_id=hub, is_deleted=False),
                'search_query': '',
                'status_filter': '',
            })
    else:
        form = CampaignForm()
        form.fields['template'].queryset = MessageTemplate.objects.filter(
            hub_id=hub, is_deleted=False, is_active=True,
        )

    return {
        'form': form,
        'is_edit': False,
    }


@login_required
@with_module_nav('messaging', 'campaigns')
@htmx_view('messaging/pages/campaign_detail.html', 'messaging/partials/campaign_detail_content.html')
def campaign_detail(request, pk):
    """View campaign details and stats."""
    hub = _hub_id(request)
    campaign = get_object_or_404(Campaign, pk=pk, hub_id=hub, is_deleted=False)
    return {'campaign': campaign}


@login_required
@require_POST
def campaign_start(request, pk):
    """Start sending a campaign."""
    hub = _hub_id(request)
    campaign = get_object_or_404(Campaign, pk=pk, hub_id=hub, is_deleted=False)

    if campaign.status not in ('draft', 'scheduled'):
        django_messages.error(request, _('Campaign cannot be started in its current state'))
    else:
        campaign.start()
        django_messages.success(request, _('Campaign started'))

    return django_render(request, 'messaging/partials/campaign_detail_content.html', {
        'campaign': campaign,
    })


@login_required
@require_POST
def campaign_cancel(request, pk):
    """Cancel a campaign."""
    hub = _hub_id(request)
    campaign = get_object_or_404(Campaign, pk=pk, hub_id=hub, is_deleted=False)

    if campaign.status in ('completed', 'cancelled'):
        django_messages.error(request, _('Campaign is already finished'))
    else:
        campaign.cancel()
        django_messages.success(request, _('Campaign cancelled'))

    return django_render(request, 'messaging/partials/campaign_detail_content.html', {
        'campaign': campaign,
    })


# ============================================================================
# API Endpoints
# ============================================================================

@login_required
@require_POST
def api_send(request):
    """API endpoint to send a message programmatically from other modules."""
    hub = _hub_id(request)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    channel = data.get('channel')
    recipient_contact = data.get('recipient_contact', '')
    subject = data.get('subject', '')
    body = data.get('body', '')
    recipient_name = data.get('recipient_name', '')
    template_id = data.get('template_id')
    customer_id = data.get('customer_id')
    metadata = data.get('metadata', {})

    if not channel or not recipient_contact or not body:
        return JsonResponse({
            'success': False,
            'error': 'channel, recipient_contact, and body are required',
        }, status=400)

    if channel not in ('whatsapp', 'sms', 'email'):
        return JsonResponse({
            'success': False,
            'error': 'Invalid channel. Must be whatsapp, sms, or email',
        }, status=400)

    msg = Message.objects.create(
        hub_id=hub,
        channel=channel,
        recipient_name=recipient_name,
        recipient_contact=recipient_contact,
        subject=subject,
        body=body,
        status=MessageStatusChoices.QUEUED,
        template_id=template_id,
        customer_id=customer_id,
        metadata=metadata,
    )

    # In production this would queue for async sending
    msg.mark_sent()

    return JsonResponse({
        'success': True,
        'message_id': str(msg.pk),
        'status': msg.status,
    })


@csrf_exempt
@require_POST
def api_webhook(request):
    """
    Delivery status webhook endpoint.

    Receives status updates from messaging providers (WhatsApp, SMS, etc.)
    No login required, CSRF exempt.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    external_id = data.get('external_id', '')
    status = data.get('status', '')
    error_message = data.get('error', '')

    if not external_id or not status:
        return JsonResponse({'error': 'external_id and status required'}, status=400)

    try:
        msg = Message.objects.get(external_id=external_id)
    except Message.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)

    if status == 'delivered':
        msg.mark_delivered()
    elif status == 'read':
        msg.mark_read()
    elif status == 'failed':
        msg.mark_failed(error=error_message)
    elif status == 'sent':
        msg.mark_sent()

    return JsonResponse({'success': True, 'message_id': str(msg.pk)})


# ============================================================================
# Settings
# ============================================================================

@login_required
@with_module_nav('messaging', 'settings')
@htmx_view('messaging/pages/settings.html', 'messaging/partials/settings_content.html')
def settings_view(request):
    """View messaging settings."""
    hub = _hub_id(request)
    settings = MessagingSettings.get_settings(hub)

    total_messages = Message.objects.filter(hub_id=hub, is_deleted=False).count()
    total_templates = MessageTemplate.objects.filter(hub_id=hub, is_deleted=False).count()
    total_campaigns = Campaign.objects.filter(hub_id=hub, is_deleted=False).count()

    return {
        'settings': settings,
        'total_messages': total_messages,
        'total_templates': total_templates,
        'total_campaigns': total_campaigns,
    }


@login_required
@require_POST
def settings_save(request):
    """Save messaging settings."""
    hub = _hub_id(request)
    settings = MessagingSettings.get_settings(hub)

    form = MessagingSettingsForm(request.POST, instance=settings)
    if form.is_valid():
        form.save()
        django_messages.success(request, _('Settings saved successfully'))
    else:
        django_messages.error(request, _('Please correct the errors below'))

    total_messages = Message.objects.filter(hub_id=hub, is_deleted=False).count()
    total_templates = MessageTemplate.objects.filter(hub_id=hub, is_deleted=False).count()
    total_campaigns = Campaign.objects.filter(hub_id=hub, is_deleted=False).count()

    return django_render(request, 'messaging/partials/settings_content.html', {
        'settings': settings,
        'total_messages': total_messages,
        'total_templates': total_templates,
        'total_campaigns': total_campaigns,
    })
