"""
Simulateur générique pour exécuter 1000 trades avec une stratégie de MM
"""

import random
from decimal import Decimal


def run_simulation(strategy_function, outcomes_config, initial_capital=1000, params=None, n=1000):
    """
    Exécute n trades en utilisant une stratégie de Money Management
    
    Args:
        strategy_function: Fonction de stratégie qui retourne le risk_percent
        outcomes_config: Dict avec les outcomes et leurs probabilités
        initial_capital: Capital de départ (défaut: 1000€)
        params: Paramètres pour la stratégie (dict)
        n: Nombre de trades à exécuter (défaut: 1000)
    
    Returns:
        dict: {
            'capital_final': float,
            'drawdown_max': float,  # en %
            'moyenne': float,  # gain moyen par trade
            'ecart_type': float,
            'equity_curve': list,  # historique du capital
            'history': list,  # liste des trades détaillés
            'trades_executed': int,
            'account_crashed': bool
        }
    """
    if params is None:
        params = {}
    
    # Préparer la liste pondérée des outcomes
    outcomes_list = []
    for outcome, probability in outcomes_config.items():
        outcomes_list.extend([float(outcome)] * probability)
    
    # Initialisation
    current_capital = float(initial_capital)
    history = []
    equity_curve = [current_capital]
    max_capital = current_capital
    max_drawdown = 0
    
    # Exécution des trades
    for trade_num in range(1, n + 1):
        # Vérifier le crash (capital < 1€)
        if current_capital < 1:
            return {
                'capital_final': current_capital,
                'drawdown_max': max_drawdown,
                'moyenne': sum(t['profit_loss'] for t in history) / len(history) if history else 0,
                'ecart_type': _calculate_std_dev(history),
                'equity_curve': equity_curve,
                'history': history,
                'trades_executed': trade_num - 1,
                'account_crashed': True
            }
        
        # Calculer le risque avec la stratégie
        risk_percent = strategy_function(history, current_capital, **params)
        
        # Limiter le risque entre 0.1% et 20%
        risk_percent = max(0.1, min(20, risk_percent))
        
        # Calculer le montant risqué
        risk_amount = current_capital * (risk_percent / 100)
        
        # Tirer un outcome aléatoire
        outcome = random.choice(outcomes_list)
        
        # Calculer le profit/perte
        profit_loss = risk_amount * outcome
        
        # Sauvegarder le capital avant le trade
        capital_before = current_capital
        
        # Mettre à jour le capital
        current_capital += profit_loss
        current_capital = max(0, current_capital)  # Ne peut pas être négatif
        
        # Enregistrer le trade
        trade = {
            'trade_number': trade_num,
            'capital_before': capital_before,
            'capital_after': current_capital,
            'risk_percent': risk_percent,
            'risk_amount': risk_amount,
            'outcome_multiplier': outcome,
            'profit_loss': profit_loss,
            'is_win': profit_loss > 0
        }
        history.append(trade)
        equity_curve.append(current_capital)
        
        # Mettre à jour le max capital et drawdown
        max_capital = max(max_capital, current_capital)
        current_dd = ((current_capital - max_capital) / max_capital) * 100
        max_drawdown = min(max_drawdown, current_dd)
    
    # Calculs finaux
    moyenne = sum(t['profit_loss'] for t in history) / len(history) if history else 0
    ecart_type = _calculate_std_dev(history)
    
    return {
        'capital_final': current_capital,
        'drawdown_max': max_drawdown,
        'moyenne': moyenne,
        'ecart_type': ecart_type,
        'equity_curve': equity_curve,
        'history': history,
        'trades_executed': n,
        'account_crashed': False
    }


def _calculate_std_dev(history):
    """Calcule l'écart-type des profits/pertes"""
    if not history or len(history) < 2:
        return 0
    
    profits = [t['profit_loss'] for t in history]
    mean = sum(profits) / len(profits)
    variance = sum((p - mean) ** 2 for p in profits) / len(profits)
    
    return variance ** 0.5
