from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Messages
    path('messages/', views.messages_list, name='messages'),
    path('messages/<uuid:pk>/', views.message_detail, name='message_detail'),
    path('messages/compose/', views.send_message, name='send_message'),

    # Templates
    path('templates/', views.templates_list, name='templates'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<uuid:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<uuid:pk>/delete/', views.template_delete, name='template_delete'),

    # Campaigns
    path('campaigns/', views.campaigns_list, name='campaigns'),
    path('campaigns/create/', views.campaign_create, name='campaign_create'),
    path('campaigns/<uuid:pk>/', views.campaign_detail, name='campaign_detail'),
    path('campaigns/<uuid:pk>/start/', views.campaign_start, name='campaign_start'),
    path('campaigns/<uuid:pk>/cancel/', views.campaign_cancel, name='campaign_cancel'),

    # API
    path('api/send/', views.api_send, name='api_send'),
    path('api/webhook/', views.api_webhook, name='api_webhook'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
    path('settings/save/', views.settings_save, name='settings_save'),
]
