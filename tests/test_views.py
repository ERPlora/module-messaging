"""
Integration tests for Messaging views.
"""

import json
import uuid
import pytest
from django.test import Client
from django.utils import timezone


pytestmark = [pytest.mark.django_db, pytest.mark.unit]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _set_hub_config(db, settings):
    """Ensure HubConfig + StoreConfig exist so middleware won't redirect."""
    from apps.configuration.models import HubConfig, StoreConfig
    config = HubConfig.get_solo()
    config.save()
    store = StoreConfig.get_solo()
    store.business_name = 'Test Business'
    store.is_configured = True
    store.save()


@pytest.fixture
def hub_id(db):
    from apps.configuration.models import HubConfig
    return HubConfig.get_solo().hub_id


@pytest.fixture
def employee(db):
    """Create a local user (employee)."""
    from apps.accounts.models import LocalUser
    return LocalUser.objects.create(
        name='Test Employee',
        email='employee@test.com',
        role='admin',
        is_active=True,
    )


@pytest.fixture
def auth_client(employee):
    """Authenticated Django test client."""
    client = Client()
    session = client.session
    session['local_user_id'] = str(employee.id)
    session['user_name'] = employee.name
    session['user_email'] = employee.email
    session['user_role'] = employee.role
    session['store_config_checked'] = True
    session.save()
    return client


@pytest.fixture
def sample_template(hub_id):
    """Create a sample message template."""
    from messaging.models import MessageTemplate
    return MessageTemplate.objects.create(
        hub_id=hub_id,
        name='Test Template',
        channel='all',
        category='custom',
        subject='Test Subject',
        body='Hello {{customer_name}}, test message.',
        is_active=True,
    )


@pytest.fixture
def sample_message(hub_id, sample_template):
    """Create a sample message."""
    from messaging.models import Message
    return Message.objects.create(
        hub_id=hub_id,
        channel='whatsapp',
        recipient_name='Maria Garcia',
        recipient_contact='+34600123456',
        body='Test message content',
        status='sent',
        template=sample_template,
        sent_at=timezone.now(),
    )


@pytest.fixture
def sample_campaign(hub_id, sample_template):
    """Create a sample campaign."""
    from messaging.models import Campaign
    return Campaign.objects.create(
        hub_id=hub_id,
        name='Test Campaign',
        channel='email',
        template=sample_template,
        status='draft',
        total_recipients=50,
    )


@pytest.fixture
def sample_settings(hub_id):
    """Create messaging settings."""
    from messaging.models import MessagingSettings
    return MessagingSettings.objects.create(
        hub_id=hub_id,
        email_enabled=True,
        email_from_name='Test',
        email_from_address='test@test.com',
    )


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class TestDashboard:

    def test_dashboard_loads(self, auth_client):
        response = auth_client.get('/m/messaging/')
        assert response.status_code == 200

    def test_dashboard_htmx(self, auth_client):
        response = auth_client.get('/m/messaging/', HTTP_HX_REQUEST='true')
        assert response.status_code == 200

    def test_requires_login(self):
        client = Client()
        response = client.get('/m/messaging/')
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

class TestMessagesList:

    def test_messages_list_loads(self, auth_client):
        response = auth_client.get('/m/messaging/messages/')
        assert response.status_code == 200

    def test_messages_list_htmx(self, auth_client):
        response = auth_client.get('/m/messaging/messages/', HTTP_HX_REQUEST='true')
        assert response.status_code == 200

    def test_messages_list_with_data(self, auth_client, sample_message):
        response = auth_client.get('/m/messaging/messages/')
        assert response.status_code == 200

    def test_messages_filter_by_channel(self, auth_client, sample_message):
        response = auth_client.get('/m/messaging/messages/?channel=whatsapp')
        assert response.status_code == 200

    def test_messages_filter_by_status(self, auth_client, sample_message):
        response = auth_client.get('/m/messaging/messages/?status=sent')
        assert response.status_code == 200

    def test_messages_search(self, auth_client, sample_message):
        response = auth_client.get('/m/messaging/messages/?q=Maria')
        assert response.status_code == 200


class TestMessageDetail:

    def test_detail_loads(self, auth_client, sample_message):
        response = auth_client.get(f'/m/messaging/messages/{sample_message.pk}/')
        assert response.status_code == 200

    def test_detail_htmx(self, auth_client, sample_message):
        response = auth_client.get(
            f'/m/messaging/messages/{sample_message.pk}/',
            HTTP_HX_REQUEST='true',
        )
        assert response.status_code == 200

    def test_detail_not_found(self, auth_client):
        fake_uuid = uuid.uuid4()
        response = auth_client.get(f'/m/messaging/messages/{fake_uuid}/')
        assert response.status_code == 404


class TestSendMessage:

    def test_compose_form_loads(self, auth_client):
        response = auth_client.get('/m/messaging/messages/compose/')
        assert response.status_code == 200

    def test_compose_htmx(self, auth_client):
        response = auth_client.get('/m/messaging/messages/compose/', HTTP_HX_REQUEST='true')
        assert response.status_code == 200

    def test_send_message_success(self, auth_client, hub_id):
        from messaging.models import Message
        response = auth_client.post('/m/messaging/messages/compose/', {
            'channel': 'email',
            'recipient_name': 'Test User',
            'recipient_contact': 'test@example.com',
            'subject': 'Test Subject',
            'body': 'Test message body',
        })
        assert response.status_code == 200
        assert Message.objects.filter(hub_id=hub_id, channel='email').exists()


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

class TestTemplatesList:

    def test_templates_list_loads(self, auth_client):
        response = auth_client.get('/m/messaging/templates/')
        assert response.status_code == 200

    def test_templates_list_htmx(self, auth_client):
        response = auth_client.get('/m/messaging/templates/', HTTP_HX_REQUEST='true')
        assert response.status_code == 200

    def test_templates_with_data(self, auth_client, sample_template):
        response = auth_client.get('/m/messaging/templates/')
        assert response.status_code == 200

    def test_templates_search(self, auth_client, sample_template):
        response = auth_client.get('/m/messaging/templates/?q=Test')
        assert response.status_code == 200


class TestTemplateCreate:

    def test_create_form_loads(self, auth_client):
        response = auth_client.get('/m/messaging/templates/create/')
        assert response.status_code == 200

    def test_create_template(self, auth_client, hub_id):
        from messaging.models import MessageTemplate
        response = auth_client.post('/m/messaging/templates/create/', {
            'name': 'New Template',
            'channel': 'email',
            'category': 'custom',
            'subject': 'Subject line',
            'body': 'Hello {{customer_name}}',
            'is_active': 'on',
        })
        assert response.status_code == 200
        assert MessageTemplate.objects.filter(hub_id=hub_id, name='New Template').exists()


class TestTemplateEdit:

    def test_edit_form_loads(self, auth_client, sample_template):
        response = auth_client.get(f'/m/messaging/templates/{sample_template.pk}/edit/')
        assert response.status_code == 200

    def test_edit_template(self, auth_client, sample_template):
        response = auth_client.post(f'/m/messaging/templates/{sample_template.pk}/edit/', {
            'name': 'Updated Template',
            'channel': 'sms',
            'category': 'marketing',
            'subject': '',
            'body': 'Updated body',
            'is_active': 'on',
        })
        assert response.status_code == 200
        sample_template.refresh_from_db()
        assert sample_template.name == 'Updated Template'


class TestTemplateDelete:

    def test_delete_template(self, auth_client, sample_template):
        response = auth_client.post(f'/m/messaging/templates/{sample_template.pk}/delete/')
        assert response.status_code == 200
        sample_template.refresh_from_db()
        assert sample_template.is_deleted is True

    def test_delete_system_template_prevented(self, auth_client, hub_id):
        from messaging.models import MessageTemplate
        system_tmpl = MessageTemplate.objects.create(
            hub_id=hub_id,
            name='System Template',
            channel='all',
            category='custom',
            body='System body',
            is_system=True,
        )
        response = auth_client.post(f'/m/messaging/templates/{system_tmpl.pk}/delete/')
        assert response.status_code == 200
        system_tmpl.refresh_from_db()
        assert system_tmpl.is_deleted is False


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------

class TestCampaignsList:

    def test_campaigns_list_loads(self, auth_client):
        response = auth_client.get('/m/messaging/campaigns/')
        assert response.status_code == 200

    def test_campaigns_list_htmx(self, auth_client):
        response = auth_client.get('/m/messaging/campaigns/', HTTP_HX_REQUEST='true')
        assert response.status_code == 200

    def test_campaigns_with_data(self, auth_client, sample_campaign):
        response = auth_client.get('/m/messaging/campaigns/')
        assert response.status_code == 200

    def test_campaigns_filter_status(self, auth_client, sample_campaign):
        response = auth_client.get('/m/messaging/campaigns/?status=draft')
        assert response.status_code == 200


class TestCampaignCreate:

    def test_create_form_loads(self, auth_client):
        response = auth_client.get('/m/messaging/campaigns/create/')
        assert response.status_code == 200

    def test_create_campaign(self, auth_client, hub_id, sample_template):
        from messaging.models import Campaign
        response = auth_client.post('/m/messaging/campaigns/create/', {
            'name': 'New Campaign',
            'description': 'Test campaign',
            'channel': 'email',
            'template': str(sample_template.pk),
        })
        assert response.status_code == 200
        assert Campaign.objects.filter(hub_id=hub_id, name='New Campaign').exists()


class TestCampaignDetail:

    def test_detail_loads(self, auth_client, sample_campaign):
        response = auth_client.get(f'/m/messaging/campaigns/{sample_campaign.pk}/')
        assert response.status_code == 200

    def test_detail_htmx(self, auth_client, sample_campaign):
        response = auth_client.get(
            f'/m/messaging/campaigns/{sample_campaign.pk}/',
            HTTP_HX_REQUEST='true',
        )
        assert response.status_code == 200


class TestCampaignStart:

    def test_start_draft_campaign(self, auth_client, sample_campaign):
        response = auth_client.post(f'/m/messaging/campaigns/{sample_campaign.pk}/start/')
        assert response.status_code == 200
        sample_campaign.refresh_from_db()
        assert sample_campaign.status == 'sending'

    def test_start_completed_campaign_fails(self, auth_client, hub_id):
        from messaging.models import Campaign
        c = Campaign.objects.create(
            hub_id=hub_id, name='Done', channel='sms',
            status='completed',
        )
        response = auth_client.post(f'/m/messaging/campaigns/{c.pk}/start/')
        assert response.status_code == 200
        c.refresh_from_db()
        assert c.status == 'completed'


class TestCampaignCancel:

    def test_cancel_draft_campaign(self, auth_client, sample_campaign):
        response = auth_client.post(f'/m/messaging/campaigns/{sample_campaign.pk}/cancel/')
        assert response.status_code == 200
        sample_campaign.refresh_from_db()
        assert sample_campaign.status == 'cancelled'

    def test_cancel_completed_campaign_fails(self, auth_client, hub_id):
        from messaging.models import Campaign
        c = Campaign.objects.create(
            hub_id=hub_id, name='Done', channel='sms',
            status='completed',
        )
        response = auth_client.post(f'/m/messaging/campaigns/{c.pk}/cancel/')
        assert response.status_code == 200
        c.refresh_from_db()
        assert c.status == 'completed'


# ---------------------------------------------------------------------------
# API Send
# ---------------------------------------------------------------------------

class TestAPISend:

    def test_api_send_success(self, auth_client, hub_id):
        response = auth_client.post(
            '/m/messaging/api/send/',
            data=json.dumps({
                'channel': 'whatsapp',
                'recipient_contact': '+34600123456',
                'recipient_name': 'Test',
                'body': 'Hello!',
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'message_id' in data

    def test_api_send_missing_fields(self, auth_client):
        response = auth_client.post(
            '/m/messaging/api/send/',
            data=json.dumps({'channel': 'sms'}),
            content_type='application/json',
        )
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False

    def test_api_send_invalid_channel(self, auth_client):
        response = auth_client.post(
            '/m/messaging/api/send/',
            data=json.dumps({
                'channel': 'telegram',
                'recipient_contact': '+34600',
                'body': 'Test',
            }),
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_api_send_invalid_json(self, auth_client):
        response = auth_client.post(
            '/m/messaging/api/send/',
            data='not json',
            content_type='application/json',
        )
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# API Webhook
# ---------------------------------------------------------------------------

class TestAPIWebhook:

    def test_webhook_delivered(self, hub_id):
        from messaging.models import Message
        msg = Message.objects.create(
            hub_id=hub_id, channel='whatsapp',
            recipient_contact='+34600', body='Test',
            status='sent', external_id='ext_001',
        )
        client = Client()
        response = client.post(
            '/m/messaging/api/webhook/',
            data=json.dumps({
                'external_id': 'ext_001',
                'status': 'delivered',
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        msg.refresh_from_db()
        assert msg.status == 'delivered'

    def test_webhook_failed(self, hub_id):
        from messaging.models import Message
        msg = Message.objects.create(
            hub_id=hub_id, channel='sms',
            recipient_contact='+34600', body='Test',
            status='sent', external_id='ext_002',
        )
        client = Client()
        response = client.post(
            '/m/messaging/api/webhook/',
            data=json.dumps({
                'external_id': 'ext_002',
                'status': 'failed',
                'error': 'Number not reachable',
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        msg.refresh_from_db()
        assert msg.status == 'failed'
        assert msg.error_message == 'Number not reachable'

    def test_webhook_read(self, hub_id):
        from messaging.models import Message
        msg = Message.objects.create(
            hub_id=hub_id, channel='whatsapp',
            recipient_contact='+34600', body='Test',
            status='delivered', external_id='ext_003',
        )
        client = Client()
        response = client.post(
            '/m/messaging/api/webhook/',
            data=json.dumps({
                'external_id': 'ext_003',
                'status': 'read',
            }),
            content_type='application/json',
        )
        assert response.status_code == 200
        msg.refresh_from_db()
        assert msg.status == 'read'

    def test_webhook_not_found(self):
        client = Client()
        response = client.post(
            '/m/messaging/api/webhook/',
            data=json.dumps({
                'external_id': 'nonexistent',
                'status': 'delivered',
            }),
            content_type='application/json',
        )
        assert response.status_code == 404

    def test_webhook_missing_fields(self):
        client = Client()
        response = client.post(
            '/m/messaging/api/webhook/',
            data=json.dumps({'status': 'delivered'}),
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_webhook_invalid_json(self):
        client = Client()
        response = client.post(
            '/m/messaging/api/webhook/',
            data='not json',
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_webhook_no_csrf_required(self, hub_id):
        """Webhook should work without CSRF token (csrf_exempt)."""
        from messaging.models import Message
        msg = Message.objects.create(
            hub_id=hub_id, channel='whatsapp',
            recipient_contact='+34600', body='Test',
            status='sent', external_id='ext_csrf_test',
        )
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            '/m/messaging/api/webhook/',
            data=json.dumps({
                'external_id': 'ext_csrf_test',
                'status': 'delivered',
            }),
            content_type='application/json',
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

class TestSettings:

    def test_settings_loads(self, auth_client):
        response = auth_client.get('/m/messaging/settings/')
        assert response.status_code == 200

    def test_settings_htmx(self, auth_client):
        response = auth_client.get('/m/messaging/settings/', HTTP_HX_REQUEST='true')
        assert response.status_code == 200

    def test_settings_save(self, auth_client, hub_id):
        from messaging.models import MessagingSettings
        # First, ensure settings exist
        MessagingSettings.get_settings(hub_id)
        response = auth_client.post('/m/messaging/settings/save/', {
            'whatsapp_enabled': 'on',
            'whatsapp_api_token': 'new-token',
            'whatsapp_phone_id': '111',
            'whatsapp_business_id': '222',
            'sms_provider': 'twilio',
            'sms_api_key': 'key123',
            'sms_sender_name': 'MyBiz',
            'email_enabled': 'on',
            'email_from_name': 'My Business',
            'email_from_address': 'info@mybiz.com',
            'email_smtp_host': 'smtp.mybiz.com',
            'email_smtp_port': '465',
            'email_smtp_username': 'user',
            'email_smtp_password': 'pass',
            'email_smtp_use_tls': 'on',
            'appointment_reminder_enabled': 'on',
            'appointment_reminder_hours': '12',
            'booking_confirmation_enabled': 'on',
        })
        assert response.status_code == 200
        settings = MessagingSettings.get_settings(hub_id)
        assert settings.whatsapp_enabled is True
        assert settings.whatsapp_api_token == 'new-token'
        assert settings.email_smtp_port == 465
        assert settings.appointment_reminder_hours == 12
