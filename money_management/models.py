from django.db import models
import json


class SimulationResult(models.Model):
    """Stocke les résultats d'une simulation individuelle"""
    
    # Identification de la simulation
    strategy_name = models.CharField(max_length=100)
    strategy_key = models.CharField(max_length=50)
    parameters = models.JSONField()  # Stocke les paramètres de la stratégie
    
    # Configuration de la simulation
    num_trades = models.IntegerField()
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2, default=10000)
    
    # Résultats finaux
    final_capital = models.DecimalField(max_digits=15, decimal_places=2)
    final_performance_pct = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Statistiques de capital
    max_capital = models.DecimalField(max_digits=15, decimal_places=2)
    max_drawdown_pct = models.DecimalField(max_digits=10, decimal_places=2)
    max_performance_pct = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Statistiques de risque
    avg_risk_pct = models.DecimalField(max_digits=10, decimal_places=4)
    avg_risk_amount = models.DecimalField(max_digits=15, decimal_places=2)
    avg_profit_loss = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Statistiques de séries
    max_consecutive_wins = models.IntegerField()
    max_consecutive_losses = models.IntegerField()
    
    # Taux de réussite
    success_rate = models.DecimalField(max_digits=5, decimal_places=2)
    total_wins = models.IntegerField()
    total_losses = models.IntegerField()
    
    # Données détaillées (optionnel, impact performance)
    equity_curve = models.JSONField(null=True, blank=True)  # Historique du capital trade par trade
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    batch_id = models.CharField(max_length=100, null=True, blank=True)  # Pour regrouper les simulations
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['strategy_key']),
            models.Index(fields=['batch_id']),
            models.Index(fields=['final_performance_pct']),
            models.Index(fields=['max_drawdown_pct']),
        ]
    
    def __str__(self):
        return f"{self.strategy_name} - {self.final_performance_pct}% (DD: {self.max_drawdown_pct}%)"


class SimulationBatch(models.Model):
    """Stocke les informations sur un lot de simulations"""
    
    batch_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    total_simulations = models.IntegerField()
    completed_simulations = models.IntegerField(default=0)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('running', 'En cours'),
            ('completed', 'Terminé'),
            ('failed', 'Échoué'),
        ],
        default='pending'
    )
    
    # Options de sauvegarde
    has_equity_curves = models.BooleanField(default=False)  # Indique si les equity curves ont été sauvegardées
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.completed_simulations}/{self.total_simulations})"
