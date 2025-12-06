from django.db import models
from django.contrib.sessions.models import Session


class TradingSession(models.Model):
    """Session de trading pour suivre l'historique d'un utilisateur"""
    session_key = models.CharField(max_length=40, unique=True, db_index=True)
    initial_capital = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)
    current_capital = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)
    total_trades = models.IntegerField(default=0)
    consecutive_wins = models.IntegerField(default=0)
    consecutive_losses = models.IntegerField(default=0)
    max_consecutive_wins = models.IntegerField(default=0)
    max_consecutive_losses = models.IntegerField(default=0)
    max_capital = models.DecimalField(max_digits=12, decimal_places=2, default=1000.00)
    max_drawdown_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    max_performance_percent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Configuration des probabilités (JSON string)
    outcomes_config = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.session_key[:8]} - Capital: {self.current_capital}€"


class Trade(models.Model):
    """Représente un trade individuel"""
    session = models.ForeignKey(TradingSession, on_delete=models.CASCADE, related_name='trades')
    trade_number = models.IntegerField()
    capital_before = models.DecimalField(max_digits=12, decimal_places=2)
    capital_after = models.DecimalField(max_digits=12, decimal_places=2)
    risk_percent = models.DecimalField(max_digits=5, decimal_places=2)
    risk_amount = models.DecimalField(max_digits=12, decimal_places=2)
    outcome_multiplier = models.DecimalField(max_digits=6, decimal_places=2)  # -5, -2, +2, +3, +4, +5, +9
    profit_loss = models.DecimalField(max_digits=12, decimal_places=2)
    is_win = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['trade_number']

    def __str__(self):
        return f"Trade #{self.trade_number} - {'Win' if self.is_win else 'Loss'}: {self.profit_loss}€"
