from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Message,
    MessageTemplate,
    Campaign,
    MessagingSettings,
    ChannelChoices,
    TemplateCategoryChoices,
    SMSProviderChoices,
)


class MessageForm(forms.ModelForm):
    """Form for composing a single message."""

    class Meta:
        model = Message
        fields = [
            'channel', 'recipient_name', 'recipient_contact',
            'subject', 'body', 'template', 'customer',
        ]
        widgets = {
            'channel': forms.Select(attrs={
                'class': 'select',
            }),
            'recipient_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Recipient name'),
            }),
            'recipient_contact': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Phone number or email'),
            }),
            'subject': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Email subject (optional for SMS/WhatsApp)'),
            }),
            'body': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': 5,
                'placeholder': _('Message body...'),
            }),
            'template': forms.Select(attrs={
                'class': 'select',
            }),
            'customer': forms.Select(attrs={
                'class': 'select',
            }),
        }


class MessageTemplateForm(forms.ModelForm):
    """Form for creating/editing message templates."""

    class Meta:
        model = MessageTemplate
        fields = [
            'name', 'channel', 'category', 'subject', 'body',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Template name'),
            }),
            'channel': forms.Select(attrs={
                'class': 'select',
            }),
            'category': forms.Select(attrs={
                'class': 'select',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Email subject line'),
            }),
            'body': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': 8,
                'placeholder': _('Message body with {{customer_name}}, {{business_name}}, etc.'),
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
        }


class CampaignForm(forms.ModelForm):
    """Form for creating/editing campaigns."""

    class Meta:
        model = Campaign
        fields = [
            'name', 'description', 'channel', 'template',
            'scheduled_at',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Campaign name'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea',
                'rows': 3,
                'placeholder': _('Campaign description (optional)'),
            }),
            'channel': forms.Select(attrs={
                'class': 'select',
            }),
            'template': forms.Select(attrs={
                'class': 'select',
            }),
            'scheduled_at': forms.DateTimeInput(attrs={
                'class': 'input',
                'type': 'datetime-local',
            }),
        }


class MessagingSettingsForm(forms.ModelForm):
    """Form for messaging settings configuration."""

    class Meta:
        model = MessagingSettings
        fields = [
            # WhatsApp
            'whatsapp_enabled', 'whatsapp_api_token',
            'whatsapp_phone_id', 'whatsapp_business_id',
            # SMS
            'sms_enabled', 'sms_provider', 'sms_api_key', 'sms_sender_name',
            # Email
            'email_enabled', 'email_from_name', 'email_from_address',
            'email_smtp_host', 'email_smtp_port', 'email_smtp_username',
            'email_smtp_password', 'email_smtp_use_tls',
            # Automation
            'appointment_reminder_enabled', 'appointment_reminder_hours',
            'booking_confirmation_enabled',
        ]
        widgets = {
            'whatsapp_enabled': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'whatsapp_api_token': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('WhatsApp Cloud API token'),
                'type': 'password',
            }),
            'whatsapp_phone_id': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Phone number ID'),
            }),
            'whatsapp_business_id': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Business account ID'),
            }),
            'sms_enabled': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'sms_provider': forms.Select(attrs={
                'class': 'select',
            }),
            'sms_api_key': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('API key'),
                'type': 'password',
            }),
            'sms_sender_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Sender name (max 11 chars)'),
            }),
            'email_enabled': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'email_from_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('Your Business Name'),
            }),
            'email_from_address': forms.EmailInput(attrs={
                'class': 'input',
                'placeholder': _('noreply@yourbusiness.com'),
            }),
            'email_smtp_host': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('smtp.example.com'),
            }),
            'email_smtp_port': forms.NumberInput(attrs={
                'class': 'input',
                'min': '1',
                'max': '65535',
            }),
            'email_smtp_username': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('SMTP username'),
            }),
            'email_smtp_password': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('SMTP password'),
                'type': 'password',
            }),
            'email_smtp_use_tls': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'appointment_reminder_enabled': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'appointment_reminder_hours': forms.NumberInput(attrs={
                'class': 'input',
                'min': '1',
                'max': '168',
            }),
            'booking_confirmation_enabled': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
        }
