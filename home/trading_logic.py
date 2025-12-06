"""
Logique de simulation du trading avec les probabilités spécifiées
"""
import random
from decimal import Decimal


class TradingSimulator:
    """Simulateur de trading basé sur 22 issues possibles"""
    
    # Presets de distributions
    PRESETS = {
        'balanced': {
            'name': 'Équilibré (Espérance positive)',
            'description': '12×(-1R), 2×(-5R), 3×(+2R), 2×(+3R), 1×(+4R), 1×(+5R), 1×(+9R)',
            'outcomes': {-1: 12, -5: 2, 2: 3, 3: 2, 4: 1, 5: 1, 9: 1},
            'expectation': 0.27
        },
        'aggressive': {
            'name': 'Agressif (Espérance négative)',
            'description': '12×(-2R), 2×(-5R), 3×(+2R), 2×(+3R), 1×(+4R), 1×(+5R), 1×(+9R)',
            'outcomes': {-2: 12, -5: 2, 2: 3, 3: 2, 4: 1, 5: 1, 9: 1},
            'expectation': -0.182
        },
        'conservative': {
            'name': 'Conservateur (Forte espérance positive)',
            'description': '12×(-1R), 2×(-2R), 3×(+2R), 2×(+3R), 1×(+4R), 1×(+5R), 1×(+9R)',
            'outcomes': {-1: 12, -2: 2, 2: 3, 3: 2, 4: 1, 5: 1, 9: 1},
            'expectation': 0.545
        }
    }
    
    # Distribution par défaut (Équilibré)
    DEFAULT_OUTCOMES = (
        [-1] * 12 +  # 12 issues de perte 1R
        [-5] * 2 +   # 2 issues de perte 5R
        [2] * 3 +    # 3 issues de gain 2R
        [3] * 2 +    # 2 issues de gain 3R
        [4] * 1 +    # 1 issue de gain 4R
        [5] * 1 +    # 1 issue de gain 5R
        [9] * 1      # 1 issue de gain 9R
    )
    
    @classmethod
    def build_outcomes_list(cls, outcomes_config):
        """Construit la liste des issues à partir de la configuration"""
        if not outcomes_config:
            return cls.DEFAULT_OUTCOMES
        
        outcomes_list = []
        for multiplier, count in outcomes_config.items():
            outcomes_list.extend([int(multiplier)] * count)
        
        return tuple(outcomes_list)
    
    @classmethod
    def calculate_mathematical_expectation(cls, outcomes_config=None):
        """Calcule l'espérance mathématique"""
        outcomes = cls.build_outcomes_list(outcomes_config) if outcomes_config else cls.DEFAULT_OUTCOMES
        total = sum(outcomes)
        expectation = total / len(outcomes)
        return expectation
    
    @classmethod
    def get_random_outcome(cls, outcomes_config=None):
        """Tire aléatoirement une issue parmi les possibles"""
        outcomes = cls.build_outcomes_list(outcomes_config) if outcomes_config else cls.DEFAULT_OUTCOMES
        return random.choice(outcomes)
    
    @classmethod
    def execute_trade(cls, current_capital, risk_percent, outcomes_config=None):
        """
        Exécute un trade avec le capital et le pourcentage de risque donnés
        
        Args:
            current_capital (Decimal): Capital actuel
            risk_percent (Decimal): Pourcentage du capital risqué
            outcomes_config (dict): Configuration personnalisée des issues
            
        Returns:
            dict: Résultat du trade avec toutes les informations
        """
        # Conversion en Decimal pour précision
        current_capital = Decimal(str(current_capital))
        risk_percent = Decimal(str(risk_percent))
        
        # Calcul du montant risqué
        risk_amount = (current_capital * risk_percent) / Decimal('100')
        
        # Tirage aléatoire de l'issue
        multiplier = cls.get_random_outcome(outcomes_config)
        
        # Calcul du profit/perte
        profit_loss = risk_amount * Decimal(str(multiplier))
        
        # Nouveau capital
        new_capital = current_capital + profit_loss
        
        # Vérifier si c'est un gain ou une perte
        is_win = multiplier > 0
        
        return {
            'multiplier': multiplier,
            'risk_amount': risk_amount,
            'profit_loss': profit_loss,
            'new_capital': new_capital,
            'is_win': is_win
        }
    
    @classmethod
    def calculate_statistics(cls, trades_queryset, session):
        """
        Calcule les statistiques pour une session
        
        Args:
            trades_queryset: QuerySet des trades
            session: TradingSession instance
            
        Returns:
            dict: Statistiques calculées
        """
        total_trades = trades_queryset.count()
        
        if total_trades == 0:
            return {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'success_rate': 0,
                'current_capital': session.current_capital,
                'performance': 0,
                'drawdown': 0,
                'max_capital': session.max_capital,
                'max_performance': 0,
                'max_drawdown': 0,
            }
        
        wins = trades_queryset.filter(is_win=True).count()
        losses = trades_queryset.filter(is_win=False).count()
        success_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        # Performance actuelle
        performance = ((session.current_capital - session.initial_capital) / session.initial_capital * 100)
        
        # Drawdown actuel
        drawdown = ((session.current_capital - session.max_capital) / session.max_capital * 100) if session.max_capital > 0 else 0
        
        # Compter les occurrences de chaque issue
        from django.db.models import Count
        outcome_counts = {}
        for trade in trades_queryset:
            multiplier = int(trade.outcome_multiplier)
            outcome_counts[multiplier] = outcome_counts.get(multiplier, 0) + 1
        
        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'success_rate': round(success_rate, 2),
            'current_capital': float(session.current_capital),
            'initial_capital': float(session.initial_capital),
            'performance': round(float(performance), 2),
            'drawdown': round(float(drawdown), 2),
            'max_capital': float(session.max_capital),
            'max_performance': float(session.max_performance_percent),
            'max_drawdown': float(session.max_drawdown_percent),
            'consecutive_wins': session.consecutive_wins,
            'consecutive_losses': session.consecutive_losses,
            'max_consecutive_wins': session.max_consecutive_wins,
            'max_consecutive_losses': session.max_consecutive_losses,
            'outcome_distribution': outcome_counts,
        }
