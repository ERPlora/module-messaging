"""
Unit tests for Messaging models.
"""

import pytest
from django.utils import timezone


pytestmark = [pytest.mark.django_db, pytest.mark.unit]


# ---------------------------------------------------------------------------
# MessagingSettings
# ---------------------------------------------------------------------------

class TestMessagingSettings:
    """Tests for MessagingSettings model."""

    def test_create(self, messaging_settings):
        assert messaging_settings.whatsapp_enabled is True
        assert messaging_settings.sms_enabled is True
        assert messaging_settings.email_enabled is True
        assert messaging_settings.sms_provider == 'twilio'
        assert messaging_settings.email_smtp_port == 587

    def test_str(self, messaging_settings):
        assert str(messaging_settings) == 'Messaging Settings'

    def test_default_values(self, hub_id):
        from messaging.models import MessagingSettings
        s = MessagingSettings.objects.create(hub_id=hub_id)
        assert s.whatsapp_enabled is False
        assert s.sms_enabled is False
        assert s.sms_provider == 'none'
        assert s.email_enabled is True
        assert s.email_smtp_port == 587
        assert s.email_smtp_use_tls is True
        assert s.appointment_reminder_enabled is False
        assert s.appointment_reminder_hours == 24
        assert s.booking_confirmation_enabled is True

    def test_get_settings_creates_if_missing(self, hub_id):
        from messaging.models import MessagingSettings
        # Ensure none exists first
        MessagingSettings.all_objects.filter(hub_id=hub_id).delete()
        settings = MessagingSettings.get_settings(hub_id)
        assert settings is not None
        assert settings.hub_id == hub_id

    def test_get_settings_returns_existing(self, hub_id, messaging_settings):
        from messaging.models import MessagingSettings
        settings = MessagingSettings.get_settings(hub_id)
        assert settings.pk == messaging_settings.pk


# ---------------------------------------------------------------------------
# MessageTemplate
# ---------------------------------------------------------------------------

class TestMessageTemplate:
    """Tests for MessageTemplate model."""

    def test_create(self, message_template):
        assert message_template.name == 'Appointment Reminder'
        assert message_template.channel == 'all'
        assert message_template.category == 'appointment_reminder'
        assert message_template.is_active is True
        assert message_template.is_system is False

    def test_str(self, message_template):
        assert str(message_template) == 'Appointment Reminder'

    def test_render_body(self, message_template):
        context = {
            'customer_name': 'Maria',
            'appointment_date': '25/02/2026',
            'appointment_time': '10:00',
        }
        rendered = message_template.render_body(context)
        assert 'Maria' in rendered
        assert '25/02/2026' in rendered
        assert '10:00' in rendered

    def test_render_body_no_context(self, message_template):
        rendered = message_template.render_body()
        assert '{{customer_name}}' in rendered

    def test_render_subject(self, message_template):
        context = {'business_name': 'Test Salon'}
        rendered = message_template.render_subject(context)
        assert 'Test Salon' in rendered

    def test_render_subject_no_context(self, message_template):
        rendered = message_template.render_subject()
        assert '{{business_name}}' in rendered

    def test_ordering(self, hub_id):
        from messaging.models import MessageTemplate
        t1 = MessageTemplate.objects.create(
            hub_id=hub_id, name='Z Template', category='marketing', body='body',
        )
        t2 = MessageTemplate.objects.create(
            hub_id=hub_id, name='A Template', category='appointment_reminder', body='body',
        )
        templates = list(MessageTemplate.objects.filter(hub_id=hub_id))
        # appointment_reminder < marketing alphabetically
        assert templates[0].pk == t2.pk

    def test_soft_delete(self, message_template):
        from messaging.models import MessageTemplate
        message_template.delete()
        assert message_template.is_deleted is True
        assert MessageTemplate.objects.filter(pk=message_template.pk).count() == 0
        assert MessageTemplate.all_objects.filter(pk=message_template.pk).count() == 1

    def test_system_template(self, system_template):
        assert system_template.is_system is True


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------

class TestMessage:
    """Tests for Message model."""

    def test_create(self, message):
        assert message.channel == 'whatsapp'
        assert message.recipient_name == 'Maria Garcia'
        assert message.status == 'sent'
        assert message.sent_at is not None

    def test_str(self, message):
        result = str(message)
        assert 'WhatsApp' in result
        assert '+34600123456' in result

    def test_mark_sent(self, hub_id):
        from messaging.models import Message
        msg = Message.objects.create(
            hub_id=hub_id, channel='sms',
            recipient_contact='+34600111222', body='Test',
            status='queued',
        )
        msg.mark_sent()
        msg.refresh_from_db()
        assert msg.status == 'sent'
        assert msg.sent_at is not None

    def test_mark_delivered(self, message):
        message.mark_delivered()
        message.refresh_from_db()
        assert message.status == 'delivered'
        assert message.delivered_at is not None

    def test_mark_read(self, message):
        message.mark_read()
        message.refresh_from_db()
        assert message.status == 'read'
        assert message.read_at is not None

    def test_mark_failed(self, hub_id):
        from messaging.models import Message
        msg = Message.objects.create(
            hub_id=hub_id, channel='email',
            recipient_contact='test@test.com', body='Test',
            status='queued',
        )
        msg.mark_failed(error='SMTP connection timeout')
        msg.refresh_from_db()
        assert msg.status == 'failed'
        assert msg.error_message == 'SMTP connection timeout'

    def test_channel_icon(self, hub_id):
        from messaging.models import Message
        wa = Message.objects.create(
            hub_id=hub_id, channel='whatsapp',
            recipient_contact='+34600', body='Test',
        )
        sms = Message.objects.create(
            hub_id=hub_id, channel='sms',
            recipient_contact='+34600', body='Test',
        )
        email = Message.objects.create(
            hub_id=hub_id, channel='email',
            recipient_contact='a@b.com', body='Test',
        )
        assert wa.channel_icon == 'logo-whatsapp'
        assert sms.channel_icon == 'chatbubble-outline'
        assert email.channel_icon == 'mail-outline'

    def test_status_color(self, hub_id):
        from messaging.models import Message
        msg = Message.objects.create(
            hub_id=hub_id, channel='sms',
            recipient_contact='+34600', body='Test', status='queued',
        )
        assert msg.status_color == 'color-warning'
        msg.status = 'sent'
        assert msg.status_color == 'color-primary'
        msg.status = 'delivered'
        assert msg.status_color == 'color-success'
        msg.status = 'failed'
        assert msg.status_color == 'color-error'
        msg.status = 'read'
        assert msg.status_color == 'color-success'

    def test_ordering_newest_first(self, hub_id):
        from messaging.models import Message
        m1 = Message.objects.create(
            hub_id=hub_id, channel='sms',
            recipient_contact='+34600', body='First',
        )
        m2 = Message.objects.create(
            hub_id=hub_id, channel='sms',
            recipient_contact='+34600', body='Second',
        )
        messages = list(Message.objects.filter(hub_id=hub_id))
        assert messages[0].pk == m2.pk
        assert messages[1].pk == m1.pk

    def test_soft_delete(self, message):
        from messaging.models import Message
        message.delete()
        assert message.is_deleted is True
        assert Message.objects.filter(pk=message.pk).count() == 0
        assert Message.all_objects.filter(pk=message.pk).count() == 1

    def test_with_customer_fk(self, hub_id, customer):
        from messaging.models import Message
        msg = Message.objects.create(
            hub_id=hub_id, channel='whatsapp',
            recipient_contact=customer.phone, body='Test',
            customer=customer,
        )
        assert msg.customer.name == 'Maria Garcia'

    def test_with_template_fk(self, hub_id, message_template):
        from messaging.models import Message
        msg = Message.objects.create(
            hub_id=hub_id, channel='email',
            recipient_contact='a@b.com', body='Test',
            template=message_template,
        )
        assert msg.template.name == 'Appointment Reminder'

    def test_metadata_default(self, hub_id):
        from messaging.models import Message
        msg = Message.objects.create(
            hub_id=hub_id, channel='sms',
            recipient_contact='+34600', body='Test',
        )
        assert msg.metadata == {}

    def test_metadata_custom(self, hub_id):
        from messaging.models import Message
        msg = Message.objects.create(
            hub_id=hub_id, channel='sms',
            recipient_contact='+34600', body='Test',
            metadata={'appointment_id': '123', 'type': 'reminder'},
        )
        assert msg.metadata['appointment_id'] == '123'


# ---------------------------------------------------------------------------
# Campaign
# ---------------------------------------------------------------------------

class TestCampaign:
    """Tests for Campaign model."""

    def test_create(self, campaign):
        assert campaign.name == 'Summer Promo'
        assert campaign.status == 'draft'
        assert campaign.total_recipients == 100
        assert campaign.channel == 'whatsapp'

    def test_str(self, campaign):
        assert str(campaign) == 'Summer Promo'

    def test_delivery_rate_zero_sent(self, campaign):
        assert campaign.delivery_rate == 0

    def test_delivery_rate(self, sending_campaign):
        # 20 delivered / 25 sent = 80%
        assert sending_campaign.delivery_rate == 80.0

    def test_progress_percent_zero_recipients(self, hub_id):
        from messaging.models import Campaign
        c = Campaign.objects.create(
            hub_id=hub_id, name='Empty', channel='sms',
            total_recipients=0,
        )
        assert c.progress_percent == 0

    def test_progress_percent(self, sending_campaign):
        # 25 sent / 50 total = 50%
        assert sending_campaign.progress_percent == 50.0

    def test_status_color(self, hub_id):
        from messaging.models import Campaign
        c = Campaign.objects.create(
            hub_id=hub_id, name='Test', channel='sms', status='draft',
        )
        assert c.status_color == ''
        c.status = 'scheduled'
        assert c.status_color == 'color-warning'
        c.status = 'sending'
        assert c.status_color == 'color-primary'
        c.status = 'completed'
        assert c.status_color == 'color-success'
        c.status = 'cancelled'
        assert c.status_color == 'color-error'

    def test_start(self, campaign):
        campaign.start()
        campaign.refresh_from_db()
        assert campaign.status == 'sending'
        assert campaign.started_at is not None

    def test_complete(self, sending_campaign):
        sending_campaign.complete()
        sending_campaign.refresh_from_db()
        assert sending_campaign.status == 'completed'
        assert sending_campaign.completed_at is not None

    def test_cancel(self, campaign):
        campaign.cancel()
        campaign.refresh_from_db()
        assert campaign.status == 'cancelled'

    def test_soft_delete(self, campaign):
        from messaging.models import Campaign
        campaign.delete()
        assert campaign.is_deleted is True
        assert Campaign.objects.filter(pk=campaign.pk).count() == 0
        assert Campaign.all_objects.filter(pk=campaign.pk).count() == 1

    def test_ordering_newest_first(self, hub_id):
        from messaging.models import Campaign
        c1 = Campaign.objects.create(
            hub_id=hub_id, name='First', channel='sms',
        )
        c2 = Campaign.objects.create(
            hub_id=hub_id, name='Second', channel='sms',
        )
        campaigns = list(Campaign.objects.filter(hub_id=hub_id))
        assert campaigns[0].pk == c2.pk
        assert campaigns[1].pk == c1.pk

    def test_campaign_with_template(self, campaign, message_template):
        assert campaign.template.name == 'Appointment Reminder'

    def test_target_filter_default(self, campaign):
        assert campaign.target_filter == {}


# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------

class TestMessageIndexes:
    """Tests for Message model indexes."""

    def test_indexes_exist(self):
        from messaging.models import Message
        index_fields = [idx.fields for idx in Message._meta.indexes]
        assert ['hub_id', 'channel', 'status', '-created_at'] in index_fields
