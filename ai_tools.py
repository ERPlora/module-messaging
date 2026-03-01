"""AI tools for the Messaging module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class ListMessageTemplates(AssistantTool):
    name = "list_message_templates"
    description = "List message templates (WhatsApp, SMS, email)."
    module_id = "messaging"
    required_permission = "messaging.view_messagetemplate"
    parameters = {
        "type": "object",
        "properties": {
            "channel": {"type": "string", "description": "whatsapp, sms, email, all"},
            "is_active": {"type": "boolean"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from messaging.models import MessageTemplate
        qs = MessageTemplate.objects.all()
        if args.get('channel'):
            qs = qs.filter(channel=args['channel'])
        if 'is_active' in args:
            qs = qs.filter(is_active=args['is_active'])
        return {"templates": [{"id": str(t.id), "name": t.name, "channel": t.channel, "category": t.category, "subject": t.subject, "is_active": t.is_active} for t in qs]}


@register_tool
class CreateMessageTemplate(AssistantTool):
    name = "create_message_template"
    description = "Create a message template for WhatsApp/SMS/email."
    module_id = "messaging"
    required_permission = "messaging.add_messagetemplate"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string"}, "channel": {"type": "string", "description": "whatsapp, sms, email, all"},
            "category": {"type": "string"}, "subject": {"type": "string"},
            "body": {"type": "string", "description": "Template body (supports {{variables}})"},
        },
        "required": ["name", "channel", "body"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from messaging.models import MessageTemplate
        t = MessageTemplate.objects.create(
            name=args['name'], channel=args['channel'], category=args.get('category', ''),
            subject=args.get('subject', ''), body=args['body'],
        )
        return {"id": str(t.id), "name": t.name, "created": True}


@register_tool
class ListMessages(AssistantTool):
    name = "list_messages"
    description = "List sent messages."
    module_id = "messaging"
    required_permission = "messaging.view_message"
    parameters = {
        "type": "object",
        "properties": {
            "channel": {"type": "string"}, "status": {"type": "string", "description": "queued, sent, delivered, failed, read"},
            "limit": {"type": "integer"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from messaging.models import Message
        qs = Message.objects.all()
        if args.get('channel'):
            qs = qs.filter(channel=args['channel'])
        if args.get('status'):
            qs = qs.filter(status=args['status'])
        limit = args.get('limit', 20)
        return {
            "messages": [
                {"id": str(m.id), "channel": m.channel, "recipient_name": m.recipient_name, "subject": m.subject, "status": m.status, "sent_at": m.sent_at.isoformat() if m.sent_at else None}
                for m in qs.order_by('-created_at')[:limit]
            ]
        }


@register_tool
class ListMessageAutomations(AssistantTool):
    name = "list_message_automations"
    description = "List message automations (triggers like welcome, birthday, post_sale)."
    module_id = "messaging"
    required_permission = "messaging.view_messageautomation"
    parameters = {
        "type": "object",
        "properties": {"is_active": {"type": "boolean"}},
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from messaging.models import MessageAutomation
        qs = MessageAutomation.objects.select_related('template').all()
        if 'is_active' in args:
            qs = qs.filter(is_active=args['is_active'])
        return {"automations": [{"id": str(a.id), "name": a.name, "trigger": a.trigger, "channel": a.channel, "template": a.template.name if a.template else None, "is_active": a.is_active, "delay_hours": a.delay_hours} for a in qs]}


@register_tool
class CreateMessageAutomation(AssistantTool):
    name = "create_message_automation"
    description = "Create a message automation (e.g., welcome SMS, birthday email, post-sale thank you)."
    module_id = "messaging"
    required_permission = "messaging.add_messageautomation"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "trigger": {"type": "string", "description": "welcome, birthday, post_sale, inactivity, etc."},
            "channel": {"type": "string"}, "template_id": {"type": "string"},
            "delay_hours": {"type": "integer", "description": "Hours to wait before sending"},
        },
        "required": ["name", "trigger", "channel", "template_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from messaging.models import MessageAutomation
        a = MessageAutomation.objects.create(
            name=args['name'], trigger=args['trigger'], channel=args['channel'],
            template_id=args['template_id'], delay_hours=args.get('delay_hours', 0),
        )
        return {"id": str(a.id), "name": a.name, "created": True}
