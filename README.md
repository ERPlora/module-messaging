# Messaging Module

Customer communication via WhatsApp, SMS, and email with CRM automations.

## Features

- Multi-channel messaging: WhatsApp, SMS, and email from a single interface
- Reusable message templates with variable placeholders ({{variables}}) and categories
- Template categories: appointment reminder, booking confirmation, receipt, marketing, custom
- Bulk messaging campaigns with scheduling, progress tracking, and delivery analytics
- CRM-driven automations triggered by events: new customer welcome, birthday, anniversary, post-sale, post-appointment, inactivity, loyalty tier change, lead stage change, ticket resolved, booking confirmed/reminder
- Configurable delay between trigger and message delivery
- Automation execution logging with status tracking (pending, sent, failed, skipped)
- Message delivery tracking: queued, sent, delivered, read, and failed statuses
- WhatsApp Business API integration (API token, phone ID, business ID)
- SMS provider support: Twilio and MessageBird
- SMTP email configuration with TLS support
- Customer-linked messages for communication history
- Campaign delivery rate and progress percentage metrics

## Installation

This module is installed automatically via the ERPlora Marketplace.

**Dependencies**: Requires `customers` module.

## Configuration

Access settings via: **Menu > Messaging > Settings**

Settings include:
- WhatsApp: enable/disable, API token, phone ID, business ID
- SMS: enable/disable, provider (Twilio/MessageBird), API key, sender name
- Email: enable/disable, from name/address, SMTP host/port/credentials, TLS toggle
- Automations: appointment reminder toggle and hours before, booking confirmation toggle

## Usage

Access via: **Menu > Messaging**

### Views

| View | URL | Description |
|------|-----|-------------|
| Dashboard | `/m/messaging/dashboard/` | Messaging overview and channel statistics |
| Messages | `/m/messaging/messages/` | View sent messages and delivery statuses |
| Templates | `/m/messaging/templates/` | Create and manage reusable message templates |
| Campaigns | `/m/messaging/campaigns/` | Create and manage bulk messaging campaigns |
| Automations | `/m/messaging/automations/` | Configure CRM-triggered automated messages |
| Settings | `/m/messaging/settings/` | Channel configuration and provider setup |

## Models

| Model | Description |
|-------|-------------|
| `MessagingSettings` | Singleton per-hub settings for WhatsApp, SMS, and email channel configuration |
| `MessageTemplate` | Reusable message template with name, channel, category, subject, body with variable placeholders, and active/system flags |
| `Message` | Sent message log with channel, recipient, subject, body, delivery status, timestamps (sent/delivered/read), customer link, and external provider ID |
| `Campaign` | Bulk messaging campaign with name, channel, template, status (draft/scheduled/sending/completed/cancelled), scheduling, recipient count, and delivery metrics |
| `MessageAutomation` | Automated messaging rule with trigger event, channel, template, delay, conditions, and execution counter |
| `AutomationExecution` | Automation execution log with customer, message, status, trigger data, and scheduled/executed timestamps |

## Permissions

| Permission | Description |
|------------|-------------|
| `messaging.view_message` | View sent messages |
| `messaging.send_message` | Send messages |
| `messaging.view_template` | View message templates |
| `messaging.add_template` | Create new templates |
| `messaging.change_template` | Edit existing templates |
| `messaging.delete_template` | Delete templates |
| `messaging.view_campaign` | View campaigns |
| `messaging.add_campaign` | Create new campaigns |
| `messaging.view_automation` | View automations |
| `messaging.add_automation` | Create new automations |
| `messaging.change_automation` | Edit existing automations |
| `messaging.delete_automation` | Delete automations |
| `messaging.manage_settings` | Manage module settings |

## Integration with Other Modules

- **customers**: Messages and campaigns are linked to customer records. Automations can trigger based on customer events (welcome, birthday, anniversary, inactivity). Campaign targeting uses customer filters.

## License

MIT

## Author

ERPlora Team - support@erplora.com
