from django.utils.translation import gettext_lazy as _

MODULE_ID = 'messaging'
MODULE_NAME = _('Messaging')
MODULE_VERSION = '1.0.0'
MODULE_ICON = 'chatbubbles-outline'
MODULE_DESCRIPTION = _('Customer communication via WhatsApp, SMS, and email')
MODULE_AUTHOR = 'ERPlora'
MODULE_CATEGORY = 'marketing'

MENU = {
    'label': _('Messaging'),
    'icon': 'chatbubbles-outline',
    'order': 70,
}

NAVIGATION = [
    {'label': _('Dashboard'), 'icon': 'speedometer-outline', 'id': 'dashboard'},
    {'label': _('Messages'), 'icon': 'chatbubble-outline', 'id': 'messages'},
    {'label': _('Templates'), 'icon': 'document-text-outline', 'id': 'templates'},
    {'label': _('Campaigns'), 'icon': 'megaphone-outline', 'id': 'campaigns'},
    {'label': _('Settings'), 'icon': 'settings-outline', 'id': 'settings'},
]

DEPENDENCIES = []

PERMISSIONS = [
    'messaging.view_message',
    'messaging.send_message',
    'messaging.view_template',
    'messaging.add_template',
    'messaging.change_template',
    'messaging.delete_template',
    'messaging.view_campaign',
    'messaging.add_campaign',
    'messaging.manage_settings',
]
