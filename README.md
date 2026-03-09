# Messaging

## Overview

| Property | Value |
|----------|-------|
| **Module ID** | `messaging` |
| **Version** | `2.0.0` |
| **Icon** | `chatbubbles-outline` |
| **Dependencies** | `customers` |

## Dependencies

This module requires the following modules to be installed:

- `customers`

## Models

### `MessagingSettings`

Per-hub messaging configuration.

| Field | Type | Details |
|-------|------|---------|
| `whatsapp_enabled` | BooleanField |  |
| `whatsapp_api_token` | CharField | max_length=500, optional |
| `whatsapp_phone_id` | CharField | max_length=50, optional |
| `whatsapp_business_id` | CharField | max_length=50, optional |
| `sms_enabled` | BooleanField |  |
| `sms_provider` | CharField | max_length=20, choices: none, twilio, messagebird |
| `sms_api_key` | CharField | max_length=255, optional |
| `sms_sender_name` | CharField | max_length=11, optional |
| `email_enabled` | BooleanField |  |
| `email_from_name` | CharField | max_length=255, optional |
| `email_from_address` | EmailField | max_length=254, optional |
| `email_smtp_host` | CharField | max_length=255, optional |
| `email_smtp_port` | IntegerField |  |
| `email_smtp_username` | CharField | max_length=255, optional |
| `email_smtp_password` | CharField | max_length=255, optional |
| `email_smtp_use_tls` | BooleanField |  |
| `appointment_reminder_enabled` | BooleanField |  |
| `appointment_reminder_hours` | IntegerField |  |
| `booking_confirmation_enabled` | BooleanField |  |

**Methods:**

- `get_settings()` — Get or create settings for a hub.

### `MessageTemplate`

Reusable message templates with variable placeholders.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=200 |
| `channel` | CharField | max_length=20, choices: whatsapp, sms, email, all |
| `category` | CharField | max_length=30, choices: appointment_reminder, booking_confirmation, receipt, marketing, custom |
| `subject` | CharField | max_length=255, optional |
| `body` | TextField |  |
| `is_active` | BooleanField |  |
| `is_system` | BooleanField |  |

**Methods:**

- `render_body()` — Render template body with context variables.
- `render_subject()` — Render template subject with context variables.

### `Message`

Sent message log.

| Field | Type | Details |
|-------|------|---------|
| `channel` | CharField | max_length=20, choices: whatsapp, sms, email |
| `recipient_name` | CharField | max_length=255, optional |
| `recipient_contact` | CharField | max_length=255 |
| `subject` | CharField | max_length=255, optional |
| `body` | TextField |  |
| `status` | CharField | max_length=20, choices: queued, sent, delivered, failed, read |
| `template` | ForeignKey | → `messaging.MessageTemplate`, on_delete=SET_NULL, optional |
| `customer` | ForeignKey | → `customers.Customer`, on_delete=SET_NULL, optional |
| `sent_at` | DateTimeField | optional |
| `delivered_at` | DateTimeField | optional |
| `read_at` | DateTimeField | optional |
| `error_message` | TextField | optional |
| `external_id` | CharField | max_length=255, optional |
| `metadata` | JSONField | optional |

**Methods:**

- `mark_sent()` — Mark message as sent.
- `mark_delivered()` — Mark message as delivered.
- `mark_read()` — Mark message as read.
- `mark_failed()` — Mark message as failed.

**Properties:**

- `channel_icon` — Return icon name for this channel.
- `status_color` — Return ux color class for this status.

### `Campaign`

Bulk messaging campaigns.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=200 |
| `description` | TextField | optional |
| `channel` | CharField | max_length=20, choices: whatsapp, sms, email, all |
| `template` | ForeignKey | → `messaging.MessageTemplate`, on_delete=SET_NULL, optional |
| `status` | CharField | max_length=20, choices: draft, scheduled, sending, completed, cancelled |
| `scheduled_at` | DateTimeField | optional |
| `started_at` | DateTimeField | optional |
| `completed_at` | DateTimeField | optional |
| `total_recipients` | PositiveIntegerField |  |
| `sent_count` | PositiveIntegerField |  |
| `delivered_count` | PositiveIntegerField |  |
| `failed_count` | PositiveIntegerField |  |
| `target_filter` | JSONField | optional |

**Methods:**

- `start()` — Mark campaign as sending.
- `complete()` — Mark campaign as completed.
- `cancel()` — Cancel the campaign.

**Properties:**

- `delivery_rate` — Calculate delivery rate as a percentage.
- `progress_percent` — Calculate send progress as a percentage.
- `status_color` — Return ux color class for this status.

### `MessageAutomation`

Automated messaging rules that fire on CRM events.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=200 |
| `description` | TextField | optional |
| `trigger` | CharField | max_length=30, choices: welcome, birthday, anniversary, post_sale, post_appointment, inactivity, ... |
| `channel` | CharField | max_length=20, choices: whatsapp, sms, email, all |
| `template` | ForeignKey | → `messaging.MessageTemplate`, on_delete=SET_NULL, optional |
| `delay_hours` | IntegerField |  |
| `is_active` | BooleanField |  |
| `conditions` | JSONField | optional |
| `total_sent` | PositiveIntegerField |  |
| `last_triggered_at` | DateTimeField | optional |

**Properties:**

- `trigger_icon`

### `AutomationExecution`

Log of automation executions.

| Field | Type | Details |
|-------|------|---------|
| `automation` | ForeignKey | → `messaging.MessageAutomation`, on_delete=CASCADE |
| `customer` | ForeignKey | → `customers.Customer`, on_delete=SET_NULL, optional |
| `message` | ForeignKey | → `messaging.Message`, on_delete=SET_NULL, optional |
| `status` | CharField | max_length=20, choices: pending, sent, failed, skipped |
| `trigger_data` | JSONField | optional |
| `error_message` | TextField | optional |
| `scheduled_for` | DateTimeField | optional |
| `executed_at` | DateTimeField | optional |

## Cross-Module Relationships

| From | Field | To | on_delete | Nullable |
|------|-------|----|-----------|----------|
| `Message` | `template` | `messaging.MessageTemplate` | SET_NULL | Yes |
| `Message` | `customer` | `customers.Customer` | SET_NULL | Yes |
| `Campaign` | `template` | `messaging.MessageTemplate` | SET_NULL | Yes |
| `MessageAutomation` | `template` | `messaging.MessageTemplate` | SET_NULL | Yes |
| `AutomationExecution` | `automation` | `messaging.MessageAutomation` | CASCADE | No |
| `AutomationExecution` | `customer` | `customers.Customer` | SET_NULL | Yes |
| `AutomationExecution` | `message` | `messaging.Message` | SET_NULL | Yes |

## URL Endpoints

Base path: `/m/messaging/`

| Path | Name | Method |
|------|------|--------|
| `(root)` | `dashboard` | GET |
| `messages/` | `messages` | GET |
| `messages/<uuid:pk>/` | `message_detail` | GET |
| `messages/compose/` | `send_message` | GET |
| `templates/` | `templates` | GET |
| `templates/create/` | `template_create` | GET/POST |
| `templates/<uuid:pk>/edit/` | `template_edit` | GET |
| `templates/<uuid:pk>/delete/` | `template_delete` | GET/POST |
| `campaigns/` | `campaigns` | GET |
| `campaigns/create/` | `campaign_create` | GET/POST |
| `campaigns/<uuid:pk>/` | `campaign_detail` | GET |
| `campaigns/<uuid:pk>/start/` | `campaign_start` | GET |
| `campaigns/<uuid:pk>/cancel/` | `campaign_cancel` | GET |
| `automations/` | `automations` | GET |
| `automations/add/` | `automation_add` | GET/POST |
| `automations/<uuid:pk>/edit/` | `automation_edit` | GET |
| `automations/<uuid:pk>/delete/` | `automation_delete` | GET/POST |
| `automations/<uuid:pk>/toggle/` | `automation_toggle` | GET |
| `api/send/` | `api_send` | GET |
| `api/webhook/` | `api_webhook` | GET |
| `settings/` | `settings` | GET |
| `settings/save/` | `settings_save` | GET/POST |

## Permissions

| Permission | Description |
|------------|-------------|
| `messaging.view_message` | View Message |
| `messaging.send_message` | Send Message |
| `messaging.view_template` | View Template |
| `messaging.add_template` | Add Template |
| `messaging.change_template` | Change Template |
| `messaging.delete_template` | Delete Template |
| `messaging.view_campaign` | View Campaign |
| `messaging.add_campaign` | Add Campaign |
| `messaging.view_automation` | View Automation |
| `messaging.add_automation` | Add Automation |
| `messaging.change_automation` | Change Automation |
| `messaging.delete_automation` | Delete Automation |
| `messaging.manage_settings` | Manage Settings |

**Role assignments:**

- **admin**: All permissions
- **manager**: `add_automation`, `add_campaign`, `add_template`, `change_automation`, `change_template`, `send_message`, `view_automation`, `view_campaign` (+2 more)
- **employee**: `send_message`, `view_automation`, `view_campaign`, `view_message`, `view_template`

## Navigation

| View | Icon | ID | Fullpage |
|------|------|----|----------|
| Dashboard | `speedometer-outline` | `dashboard` | No |
| Messages | `chatbubble-outline` | `messages` | No |
| Templates | `document-text-outline` | `templates` | No |
| Campaigns | `megaphone-outline` | `campaigns` | No |
| Automations | `flash-outline` | `automations` | No |
| Settings | `settings-outline` | `settings` | No |

## AI Tools

Tools available for the AI assistant:

### `list_message_templates`

List message templates (WhatsApp, SMS, email).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel` | string | No | whatsapp, sms, email, all |
| `is_active` | boolean | No |  |

### `create_message_template`

Create a message template for WhatsApp/SMS/email.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes |  |
| `channel` | string | Yes | whatsapp, sms, email, all |
| `category` | string | No |  |
| `subject` | string | No |  |
| `body` | string | Yes | Template body (supports {{variables}}) |

### `list_messages`

List sent messages.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `channel` | string | No |  |
| `status` | string | No | queued, sent, delivered, failed, read |
| `limit` | integer | No |  |

### `list_message_automations`

List message automations (triggers like welcome, birthday, post_sale).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `is_active` | boolean | No |  |

### `create_message_automation`

Create a message automation (e.g., welcome SMS, birthday email, post-sale thank you).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes |  |
| `trigger` | string | Yes | welcome, birthday, post_sale, inactivity, etc. |
| `channel` | string | Yes |  |
| `template_id` | string | Yes |  |
| `delay_hours` | integer | No | Hours to wait before sending |

## File Structure

```
README.md
__init__.py
ai_tools.py
forms.py
locale/
  es/
    LC_MESSAGES/
      django.po
migrations/
  0001_initial.py
  __init__.py
models.py
module.py
static/
  messaging/
    css/
    js/
templates/
  messaging/
    pages/
      automation_add.html
      automation_edit.html
      automations.html
      campaign_detail.html
      campaign_form.html
      campaigns.html
      compose.html
      dashboard.html
      message_detail.html
      messages.html
      settings.html
      template_form.html
      templates.html
    partials/
      automation_add_content.html
      automation_edit_content.html
      automations_content.html
      automations_list.html
      campaign_detail_content.html
      campaign_form_content.html
      campaigns_content.html
      compose_content.html
      dashboard_content.html
      message_detail_content.html
      messages_content.html
      messages_list_rows.html
      panel_automation_add.html
      panel_automation_edit.html
      settings_content.html
      template_form_content.html
      templates_content.html
tests/
  __init__.py
  conftest.py
  test_models.py
  test_views.py
urls.py
views.py
```
