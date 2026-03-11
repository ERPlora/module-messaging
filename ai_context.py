"""
AI context for the Messaging module.
Loaded into the assistant system prompt when this module's tools are active.
"""

CONTEXT = """
## Module Knowledge: Messaging

### Models

**MessagingSettings** (singleton per hub)
- WhatsApp: `whatsapp_enabled`, `whatsapp_api_token`, `whatsapp_phone_id`, `whatsapp_business_id`
- SMS: `sms_enabled`, `sms_provider` (none/twilio/messagebird), `sms_api_key`, `sms_sender_name` (max 11 chars)
- Email: `email_enabled`, `email_from_name`, `email_from_address`, SMTP config fields, `email_smtp_use_tls`
- Automation: `appointment_reminder_enabled`, `appointment_reminder_hours` (default 24), `booking_confirmation_enabled`
- Use `MessagingSettings.get_settings(hub_id)` to get or create

**MessageTemplate**
- `name`, `channel` (whatsapp/sms/email/all), `category` (appointment_reminder/booking_confirmation/receipt/marketing/custom)
- `subject` (email subject line), `body` (text with {{variable}} placeholders)
- `is_active`, `is_system` (system templates cannot be deleted)
- Render with `.render_body(context_dict)` and `.render_subject(context_dict)` — replaces `{{key}}` with values

**Message** (sent message log)
- `channel` (whatsapp/sms/email), `recipient_name`, `recipient_contact` (phone or email)
- `subject`, `body`, `status` (queued/sent/delivered/failed/read)
- `template` (FK → MessageTemplate, nullable), `customer` (FK → customers.Customer, nullable)
- `sent_at`, `delivered_at`, `read_at`, `error_message`, `external_id` (provider ID), `metadata` (JSONField)
- Status transitions: `.mark_sent()`, `.mark_delivered()`, `.mark_read()`, `.mark_failed(error)`

**Campaign** (bulk messaging)
- `name`, `description`, `channel`, `template` (FK → MessageTemplate, nullable)
- `status` (draft/scheduled/sending/completed/cancelled), `scheduled_at`, `started_at`, `completed_at`
- `total_recipients`, `sent_count`, `delivered_count`, `failed_count`
- `target_filter` (JSONField) — customer filter criteria
- Transitions: `.start()`, `.complete()`, `.cancel()`

**MessageAutomation** (event-driven rules)
- `name`, `trigger` — choices: welcome, birthday, anniversary, post_sale, post_appointment, inactivity, loyalty_tier_change, lead_stage_change, ticket_resolved, booking_confirmed, booking_reminder, custom
- `channel`, `template` (FK → MessageTemplate, nullable), `delay_hours` (default 0)
- `is_active`, `conditions` (JSONField — e.g. `{"inactivity_days": 30}`)
- `total_sent`, `last_triggered_at`

**AutomationExecution** (execution log)
- `automation` (FK → MessageAutomation), `customer` (FK → customers.Customer, nullable)
- `message` (FK → Message, nullable), `status` (pending/sent/failed/skipped)
- `trigger_data` (JSONField), `error_message`, `scheduled_for`, `executed_at`

### Key flows

1. **Send a message**: Create Message with channel, recipient_contact, body → call gateway → `.mark_sent()`.
2. **Bulk campaign**: Create Campaign → link template → set `target_filter` → `.start()` → create individual Messages → update counts → `.complete()`.
3. **Automation**: Create MessageAutomation with trigger and template → when event fires, create AutomationExecution → send Message → update execution status.
4. **Templates**: Use `{{customer_name}}`, `{{booking_date}}` etc. as placeholders in body/subject.

### Relationships
- Message.template → MessageTemplate (FK, nullable)
- Message.customer → customers.Customer (FK, nullable)
- Campaign.template → MessageTemplate (FK, nullable)
- MessageAutomation.template → MessageTemplate (FK, nullable)
- AutomationExecution.automation → MessageAutomation, .customer → customers.Customer, .message → Message
"""
