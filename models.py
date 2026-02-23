from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import HubBaseModel


# ============================================================================
# Channel / Status Choices
# ============================================================================

class ChannelChoices(models.TextChoices):
    WHATSAPP = 'whatsapp', _('WhatsApp')
    SMS = 'sms', _('SMS')
    EMAIL = 'email', _('Email')
    ALL = 'all', _('All Channels')


class MessageStatusChoices(models.TextChoices):
    QUEUED = 'queued', _('Queued')
    SENT = 'sent', _('Sent')
    DELIVERED = 'delivered', _('Delivered')
    FAILED = 'failed', _('Failed')
    READ = 'read', _('Read')


class CampaignStatusChoices(models.TextChoices):
    DRAFT = 'draft', _('Draft')
    SCHEDULED = 'scheduled', _('Scheduled')
    SENDING = 'sending', _('Sending')
    COMPLETED = 'completed', _('Completed')
    CANCELLED = 'cancelled', _('Cancelled')


class SMSProviderChoices(models.TextChoices):
    NONE = 'none', _('None')
    TWILIO = 'twilio', _('Twilio')
    MESSAGEBIRD = 'messagebird', _('MessageBird')


class TemplateCategoryChoices(models.TextChoices):
    APPOINTMENT_REMINDER = 'appointment_reminder', _('Appointment Reminder')
    BOOKING_CONFIRMATION = 'booking_confirmation', _('Booking Confirmation')
    RECEIPT = 'receipt', _('Receipt')
    MARKETING = 'marketing', _('Marketing')
    CUSTOM = 'custom', _('Custom')


# ============================================================================
# Messaging Settings
# ============================================================================

class MessagingSettings(HubBaseModel):
    """Per-hub messaging configuration."""

    # WhatsApp
    whatsapp_enabled = models.BooleanField(
        _('WhatsApp Enabled'),
        default=False,
    )
    whatsapp_api_token = models.CharField(
        _('WhatsApp API Token'),
        max_length=500,
        blank=True,
    )
    whatsapp_phone_id = models.CharField(
        _('WhatsApp Phone ID'),
        max_length=50,
        blank=True,
    )
    whatsapp_business_id = models.CharField(
        _('WhatsApp Business ID'),
        max_length=50,
        blank=True,
    )

    # SMS
    sms_enabled = models.BooleanField(
        _('SMS Enabled'),
        default=False,
    )
    sms_provider = models.CharField(
        _('SMS Provider'),
        max_length=20,
        choices=SMSProviderChoices.choices,
        default=SMSProviderChoices.NONE,
    )
    sms_api_key = models.CharField(
        _('SMS API Key'),
        max_length=255,
        blank=True,
    )
    sms_sender_name = models.CharField(
        _('SMS Sender Name'),
        max_length=11,
        blank=True,
    )

    # Email
    email_enabled = models.BooleanField(
        _('Email Enabled'),
        default=True,
    )
    email_from_name = models.CharField(
        _('From Name'),
        max_length=255,
        blank=True,
    )
    email_from_address = models.EmailField(
        _('From Email Address'),
        blank=True,
    )
    email_smtp_host = models.CharField(
        _('SMTP Host'),
        max_length=255,
        blank=True,
    )
    email_smtp_port = models.IntegerField(
        _('SMTP Port'),
        default=587,
    )
    email_smtp_username = models.CharField(
        _('SMTP Username'),
        max_length=255,
        blank=True,
    )
    email_smtp_password = models.CharField(
        _('SMTP Password'),
        max_length=255,
        blank=True,
    )
    email_smtp_use_tls = models.BooleanField(
        _('Use TLS'),
        default=True,
    )

    # Automation
    appointment_reminder_enabled = models.BooleanField(
        _('Appointment Reminders'),
        default=False,
    )
    appointment_reminder_hours = models.IntegerField(
        _('Reminder Hours Before'),
        default=24,
    )
    booking_confirmation_enabled = models.BooleanField(
        _('Booking Confirmations'),
        default=True,
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'messaging_settings'
        verbose_name = _('Messaging Settings')
        verbose_name_plural = _('Messaging Settings')
        unique_together = [('hub_id',)]

    def __str__(self):
        return str(_('Messaging Settings'))

    @classmethod
    def get_settings(cls, hub_id):
        """Get or create settings for a hub."""
        settings, _ = cls.all_objects.get_or_create(hub_id=hub_id)
        return settings


# ============================================================================
# Message Template
# ============================================================================

class MessageTemplate(HubBaseModel):
    """Reusable message templates with variable placeholders."""

    name = models.CharField(
        _('Template Name'),
        max_length=200,
    )
    channel = models.CharField(
        _('Channel'),
        max_length=20,
        choices=ChannelChoices.choices,
        default=ChannelChoices.ALL,
    )
    category = models.CharField(
        _('Category'),
        max_length=30,
        choices=TemplateCategoryChoices.choices,
        default=TemplateCategoryChoices.CUSTOM,
    )
    subject = models.CharField(
        _('Subject'),
        max_length=255,
        blank=True,
        help_text=_('Email subject line'),
    )
    body = models.TextField(
        _('Body'),
        help_text=_('Message body with {{variables}}'),
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
    )
    is_system = models.BooleanField(
        _('System Template'),
        default=False,
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'messaging_template'
        verbose_name = _('Message Template')
        verbose_name_plural = _('Message Templates')
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

    def render_body(self, context=None):
        """Render template body with context variables."""
        if not context:
            return self.body
        result = self.body
        for key, value in context.items():
            result = result.replace('{{' + key + '}}', str(value))
        return result

    def render_subject(self, context=None):
        """Render template subject with context variables."""
        if not context:
            return self.subject
        result = self.subject
        for key, value in context.items():
            result = result.replace('{{' + key + '}}', str(value))
        return result


# ============================================================================
# Message
# ============================================================================

class Message(HubBaseModel):
    """Sent message log."""

    channel = models.CharField(
        _('Channel'),
        max_length=20,
        choices=[
            ('whatsapp', _('WhatsApp')),
            ('sms', _('SMS')),
            ('email', _('Email')),
        ],
    )
    recipient_name = models.CharField(
        _('Recipient Name'),
        max_length=255,
        blank=True,
    )
    recipient_contact = models.CharField(
        _('Recipient Contact'),
        max_length=255,
        help_text=_('Phone number or email address'),
    )
    subject = models.CharField(
        _('Subject'),
        max_length=255,
        blank=True,
    )
    body = models.TextField(
        _('Body'),
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=MessageStatusChoices.choices,
        default=MessageStatusChoices.QUEUED,
    )
    template = models.ForeignKey(
        MessageTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        verbose_name=_('Template'),
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        verbose_name=_('Customer'),
    )
    sent_at = models.DateTimeField(
        _('Sent At'),
        null=True,
        blank=True,
    )
    delivered_at = models.DateTimeField(
        _('Delivered At'),
        null=True,
        blank=True,
    )
    read_at = models.DateTimeField(
        _('Read At'),
        null=True,
        blank=True,
    )
    error_message = models.TextField(
        _('Error Message'),
        blank=True,
    )
    external_id = models.CharField(
        _('External ID'),
        max_length=255,
        blank=True,
        help_text=_('Provider message ID'),
    )
    metadata = models.JSONField(
        _('Metadata'),
        default=dict,
        blank=True,
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'messaging_message'
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['hub_id', 'channel', 'status', '-created_at']),
        ]

    def __str__(self):
        return f'{self.get_channel_display()} -> {self.recipient_contact}'

    def mark_sent(self):
        """Mark message as sent."""
        from django.utils import timezone
        self.status = MessageStatusChoices.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])

    def mark_delivered(self):
        """Mark message as delivered."""
        from django.utils import timezone
        self.status = MessageStatusChoices.DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at', 'updated_at'])

    def mark_read(self):
        """Mark message as read."""
        from django.utils import timezone
        self.status = MessageStatusChoices.READ
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at', 'updated_at'])

    def mark_failed(self, error=''):
        """Mark message as failed."""
        self.status = MessageStatusChoices.FAILED
        self.error_message = error
        self.save(update_fields=['status', 'error_message', 'updated_at'])

    @property
    def channel_icon(self):
        """Return icon name for this channel."""
        icons = {
            'whatsapp': 'logo-whatsapp',
            'sms': 'chatbubble-outline',
            'email': 'mail-outline',
        }
        return icons.get(self.channel, 'chatbubble-outline')

    @property
    def status_color(self):
        """Return ux color class for this status."""
        colors = {
            'queued': 'color-warning',
            'sent': 'color-primary',
            'delivered': 'color-success',
            'failed': 'color-error',
            'read': 'color-success',
        }
        return colors.get(self.status, '')


# ============================================================================
# Campaign
# ============================================================================

class Campaign(HubBaseModel):
    """Bulk messaging campaigns."""

    name = models.CharField(
        _('Campaign Name'),
        max_length=200,
    )
    description = models.TextField(
        _('Description'),
        blank=True,
    )
    channel = models.CharField(
        _('Channel'),
        max_length=20,
        choices=[
            ('whatsapp', _('WhatsApp')),
            ('sms', _('SMS')),
            ('email', _('Email')),
            ('all', _('All Channels')),
        ],
    )
    template = models.ForeignKey(
        MessageTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns',
        verbose_name=_('Template'),
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=CampaignStatusChoices.choices,
        default=CampaignStatusChoices.DRAFT,
    )
    scheduled_at = models.DateTimeField(
        _('Scheduled At'),
        null=True,
        blank=True,
    )
    started_at = models.DateTimeField(
        _('Started At'),
        null=True,
        blank=True,
    )
    completed_at = models.DateTimeField(
        _('Completed At'),
        null=True,
        blank=True,
    )
    total_recipients = models.PositiveIntegerField(
        _('Total Recipients'),
        default=0,
    )
    sent_count = models.PositiveIntegerField(
        _('Sent Count'),
        default=0,
    )
    delivered_count = models.PositiveIntegerField(
        _('Delivered Count'),
        default=0,
    )
    failed_count = models.PositiveIntegerField(
        _('Failed Count'),
        default=0,
    )
    target_filter = models.JSONField(
        _('Target Filter'),
        default=dict,
        blank=True,
        help_text=_('Customer filter criteria'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'messaging_campaign'
        verbose_name = _('Campaign')
        verbose_name_plural = _('Campaigns')
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def delivery_rate(self):
        """Calculate delivery rate as a percentage."""
        if self.sent_count == 0:
            return 0
        return round((self.delivered_count / self.sent_count) * 100, 1)

    @property
    def progress_percent(self):
        """Calculate send progress as a percentage."""
        if self.total_recipients == 0:
            return 0
        return round((self.sent_count / self.total_recipients) * 100, 1)

    @property
    def status_color(self):
        """Return ux color class for this status."""
        colors = {
            'draft': '',
            'scheduled': 'color-warning',
            'sending': 'color-primary',
            'completed': 'color-success',
            'cancelled': 'color-error',
        }
        return colors.get(self.status, '')

    def start(self):
        """Mark campaign as sending."""
        from django.utils import timezone
        self.status = CampaignStatusChoices.SENDING
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at', 'updated_at'])

    def complete(self):
        """Mark campaign as completed."""
        from django.utils import timezone
        self.status = CampaignStatusChoices.COMPLETED
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def cancel(self):
        """Cancel the campaign."""
        self.status = CampaignStatusChoices.CANCELLED
        self.save(update_fields=['status', 'updated_at'])


# ============================================================================
# Message Automation (CRM triggers)
# ============================================================================

class AutomationTriggerChoices(models.TextChoices):
    WELCOME = 'welcome', _('New Customer Welcome')
    BIRTHDAY = 'birthday', _('Birthday')
    ANNIVERSARY = 'anniversary', _('Anniversary')
    POST_SALE = 'post_sale', _('After Sale')
    POST_APPOINTMENT = 'post_appointment', _('After Appointment')
    INACTIVITY = 'inactivity', _('Customer Inactivity')
    LOYALTY_TIER_CHANGE = 'loyalty_tier_change', _('Loyalty Tier Change')
    LEAD_STAGE_CHANGE = 'lead_stage_change', _('Lead Stage Change')
    TICKET_RESOLVED = 'ticket_resolved', _('Ticket Resolved')
    BOOKING_CONFIRMED = 'booking_confirmed', _('Booking Confirmed')
    BOOKING_REMINDER = 'booking_reminder', _('Booking Reminder')
    CUSTOM = 'custom', _('Custom Trigger')


class MessageAutomation(HubBaseModel):
    """Automated messaging rules that fire on CRM events."""

    name = models.CharField(
        _('Automation Name'),
        max_length=200,
    )
    description = models.TextField(
        _('Description'),
        blank=True,
    )
    trigger = models.CharField(
        _('Trigger'),
        max_length=30,
        choices=AutomationTriggerChoices.choices,
    )
    channel = models.CharField(
        _('Channel'),
        max_length=20,
        choices=ChannelChoices.choices,
        default=ChannelChoices.EMAIL,
    )
    template = models.ForeignKey(
        MessageTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='automations',
        verbose_name=_('Template'),
    )
    delay_hours = models.IntegerField(
        _('Delay (hours)'),
        default=0,
        help_text=_('Hours to wait after trigger before sending'),
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
    )
    conditions = models.JSONField(
        _('Conditions'),
        default=dict,
        blank=True,
        help_text=_('Additional conditions (e.g., inactivity_days: 30)'),
    )
    total_sent = models.PositiveIntegerField(
        _('Total Sent'),
        default=0,
    )
    last_triggered_at = models.DateTimeField(
        _('Last Triggered'),
        null=True,
        blank=True,
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'messaging_automation'
        verbose_name = _('Message Automation')
        verbose_name_plural = _('Message Automations')
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_trigger_display()})'

    @property
    def trigger_icon(self):
        icons = {
            'welcome': 'hand-right-outline',
            'birthday': 'gift-outline',
            'anniversary': 'heart-outline',
            'post_sale': 'cart-outline',
            'post_appointment': 'calendar-outline',
            'inactivity': 'time-outline',
            'loyalty_tier_change': 'trophy-outline',
            'lead_stage_change': 'funnel-outline',
            'ticket_resolved': 'checkmark-done-outline',
            'booking_confirmed': 'globe-outline',
            'booking_reminder': 'alarm-outline',
            'custom': 'code-outline',
        }
        return icons.get(self.trigger, 'flash-outline')


class AutomationExecution(HubBaseModel):
    """Log of automation executions."""

    automation = models.ForeignKey(
        MessageAutomation,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name=_('Automation'),
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='automation_executions',
        verbose_name=_('Customer'),
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='automation_executions',
        verbose_name=_('Message'),
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('sent', _('Sent')),
            ('failed', _('Failed')),
            ('skipped', _('Skipped')),
        ],
        default='pending',
    )
    trigger_data = models.JSONField(
        _('Trigger Data'),
        default=dict,
        blank=True,
    )
    error_message = models.TextField(
        _('Error'),
        blank=True,
    )
    scheduled_for = models.DateTimeField(
        _('Scheduled For'),
        null=True,
        blank=True,
    )
    executed_at = models.DateTimeField(
        _('Executed At'),
        null=True,
        blank=True,
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'messaging_automation_execution'
        verbose_name = _('Automation Execution')
        verbose_name_plural = _('Automation Executions')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.automation.name} -> {self.customer}'
