from django.contrib import admin
from .models import TradingSession, Trade


@admin.register(TradingSession)
class TradingSessionAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'current_capital', 'total_trades', 'created_at']
    list_filter = ['created_at']
    search_fields = ['session_key']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['trade_number', 'session', 'is_win', 'profit_loss', 'capital_after', 'timestamp']
    list_filter = ['is_win', 'timestamp']
    search_fields = ['session__session_key']
    readonly_fields = ['timestamp']
