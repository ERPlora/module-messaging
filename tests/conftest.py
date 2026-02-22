"""
Pytest fixtures for Messaging module tests.
"""
import os
import uuid
import pytest
from decimal import Decimal
from django.test import Client
from django.utils import timezone


os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'


@pytest.fixture
def hub_id(hub_config):
    """Hub ID from HubConfig singleton."""
    return hub_config.hub_id


@pytest.fixture
def messaging_settings(hub_id):
    """Create messaging settings for the hub."""
    from messaging.models import MessagingSettings
    return MessagingSettings.objects.create(
        hub_id=hub_id,
        whatsapp_enabled=True,
        whatsapp_api_token='test-token-123',
        whatsapp_phone_id='123456789',
        whatsapp_business_id='987654321',
        sms_enabled=True,
        sms_provider='twilio',
        sms_api_key='test-sms-key',
        sms_sender_name='TestBiz',
        email_enabled=True,
        email_from_name='Test Business',
        email_from_address='noreply@test.com',
        email_smtp_host='smtp.test.com',
        email_smtp_port=587,
        email_smtp_username='smtp_user',
        email_smtp_password='smtp_pass',
        email_smtp_use_tls=True,
        appointment_reminder_enabled=True,
        appointment_reminder_hours=24,
        booking_confirmation_enabled=True,
    )


@pytest.fixture
def message_template(hub_id):
    """Create a basic message template."""
    from messaging.models import MessageTemplate
    return MessageTemplate.objects.create(
        hub_id=hub_id,
        name='Appointment Reminder',
        channel='all',
        category='appointment_reminder',
        subject='Reminder: Your appointment at {{business_name}}',
        body='Hi {{customer_name}}, this is a reminder about your appointment on {{appointment_date}} at {{appointment_time}}. See you soon!',
        is_active=True,
    )


@pytest.fixture
def system_template(hub_id):
    """Create a system template (non-deletable)."""
    from messaging.models import MessageTemplate
    return MessageTemplate.objects.create(
        hub_id=hub_id,
        name='Booking Confirmation',
        channel='email',
        category='booking_confirmation',
        subject='Booking confirmed at {{business_name}}',
        body='Dear {{customer_name}}, your booking has been confirmed for {{appointment_date}}.',
        is_active=True,
        is_system=True,
    )


@pytest.fixture
def message(hub_id, message_template):
    """Create a sample sent message."""
    from messaging.models import Message
    return Message.objects.create(
        hub_id=hub_id,
        channel='whatsapp',
        recipient_name='Maria Garcia',
        recipient_contact='+34600123456',
        subject='',
        body='Hi Maria, reminder about your appointment tomorrow at 10:00.',
        status='sent',
        template=message_template,
        sent_at=timezone.now(),
        external_id='wa_msg_001',
    )


@pytest.fixture
def failed_message(hub_id):
    """Create a failed message."""
    from messaging.models import Message
    return Message.objects.create(
        hub_id=hub_id,
        channel='sms',
        recipient_name='Juan Lopez',
        recipient_contact='+34600999888',
        body='Your appointment is tomorrow.',
        status='failed',
        error_message='Invalid phone number format',
    )


@pytest.fixture
def email_message(hub_id):
    """Create an email message."""
    from messaging.models import Message
    return Message.objects.create(
        hub_id=hub_id,
        channel='email',
        recipient_name='Ana Martinez',
        recipient_contact='ana@example.com',
        subject='Your receipt',
        body='Thank you for your purchase. Here is your receipt.',
        status='delivered',
        sent_at=timezone.now(),
        delivered_at=timezone.now(),
    )


@pytest.fixture
def campaign(hub_id, message_template):
    """Create a draft campaign."""
    from messaging.models import Campaign
    return Campaign.objects.create(
        hub_id=hub_id,
        name='Summer Promo',
        description='Summer promotion campaign for all customers',
        channel='whatsapp',
        template=message_template,
        status='draft',
        total_recipients=100,
    )


@pytest.fixture
def sending_campaign(hub_id, message_template):
    """Create a campaign that is currently sending."""
    from messaging.models import Campaign
    return Campaign.objects.create(
        hub_id=hub_id,
        name='Active Campaign',
        channel='email',
        template=message_template,
        status='sending',
        started_at=timezone.now(),
        total_recipients=50,
        sent_count=25,
        delivered_count=20,
        failed_count=2,
    )


@pytest.fixture
def customer(hub_id):
    """Create a test customer (from customers module)."""
    from customers.models import Customer
    return Customer.objects.create(
        hub_id=hub_id,
        name='Maria Garcia',
        email='maria@example.com',
        phone='+34600123456',
    )
