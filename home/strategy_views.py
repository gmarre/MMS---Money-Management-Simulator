"""
Vue pour exécuter des trades avec une stratégie de Money Management
Ce fichier gère l'exécution trade par trade avec calcul du risque adaptatif
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from money_management.strategies import STRATEGIES
from home.models import TradingSession, Trade
from home.trading_logic import TradingSimulator


def get_or_create_session(request):
    """
    Récupère ou crée une session de trading
    Utilise la même logique que views.py
    """
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    trading_session, created = TradingSession.objects.get_or_create(
        session_key=session_key
    )
    return trading_session


@csrf_exempt
def execute_strategy_batch(request):
    """
    Exécute un batch de trades avec une stratégie de Money Management
    
    Cette vue :
    1. Récupère la session en cours via session_key (comme les autres endpoints)
    2. Pour chaque trade :
       - Récupère l'historique des trades précédents
       - Calcule le risque avec la stratégie
       - Exécute le trade normalement (comme execute_batch_trades)
    3. Retourne les stats mises à jour
    
    POST params:
        - strategy_key: clé de la stratégie (ex: "strategy_1")
        - params: dict des paramètres de la stratégie
        - count: nombre de trades à exécuter (défaut: 1000)
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    # Récupérer les paramètres
    strategy_key = data.get('strategy_key')
    strategy_params = data.get('params', {})
    count = data.get('count', 1000)
    
    # Vérifier que la stratégie existe
    if strategy_key not in STRATEGIES:
        return JsonResponse({
            'success': False, 
            'error': f'Stratégie "{strategy_key}" non trouvée'
        }, status=404)
    
    # Récupérer la session en cours (même système que les autres endpoints)
    session = get_or_create_session(request)
    
    # Vérifier que la session a été initialisée (start_session appelé)
    if session.total_trades == 0 and not hasattr(session, 'outcomes_config'):
        return JsonResponse({
            'success': False, 
            'error': 'Session non initialisée. Appelez start_session d\'abord.'
        }, status=400)
    
    # Récupérer la fonction de stratégie
    strategy_info = STRATEGIES[strategy_key]
    strategy_function = strategy_info['function']
    
    # Compteur de trades exécutés
    trades_executed = 0
    account_crashed = False
    
    # Exécuter les trades un par un
    for i in range(count):
        # Vérifier si le compte a crashé (capital < 1€)
        if session.current_capital < 1:
            account_crashed = True
            break
        
        # Récupérer l'historique des trades pour la stratégie
        # On convertit les trades Django en dict pour la stratégie
        all_trades = Trade.objects.filter(session=session).order_by('trade_number')
        history = []
        for trade in all_trades:
            history.append({
                'trade_number': trade.trade_number,
                'capital_before': float(trade.capital_before),
                'capital_after': float(trade.capital_after),
                'risk_percent': float(trade.risk_percent),
                'risk_amount': float(trade.risk_amount),
                'outcome_multiplier': float(trade.outcome_multiplier),
                'profit_loss': float(trade.profit_loss),
                'is_win': trade.is_win
            })
        
        # Calculer le risque avec la stratégie
        # La stratégie retourne un risque en % (ex: 1.0 pour 1%)
        risk_percent = strategy_function(history, float(session.current_capital), **strategy_params)
        
        # Limiter le risque entre 0.1% et 20%
        risk_percent = max(0.1, min(20.0, risk_percent))
        
        # Exécuter le trade avec ce risque (méthode statique)
        result = TradingSimulator.execute_trade(
            current_capital=float(session.current_capital),
            risk_percent=risk_percent,
            outcomes_config=session.outcomes_config
        )
        
        # Sauvegarder le capital avant le trade
        capital_before = session.current_capital
        
        # Mettre à jour le capital
        session.current_capital = result['new_capital']
        
        # Mettre à jour les statistiques de session
        session.total_trades += 1
        if result['is_win']:
            session.consecutive_wins += 1
            session.consecutive_losses = 0
            if session.consecutive_wins > session.max_consecutive_wins:
                session.max_consecutive_wins = session.consecutive_wins
        else:
            session.consecutive_losses += 1
            session.consecutive_wins = 0
            if session.consecutive_losses > session.max_consecutive_losses:
                session.max_consecutive_losses = session.consecutive_losses
        
        # Calculer le drawdown et la performance
        if session.current_capital > session.max_capital:
            session.max_capital = session.current_capital
        
        current_dd = ((session.current_capital - session.max_capital) / session.max_capital) * 100
        if current_dd < session.max_drawdown_percent:
            session.max_drawdown_percent = current_dd
        
        current_performance = ((session.current_capital - session.initial_capital) / session.initial_capital) * 100
        if current_performance > session.max_performance_percent:
            session.max_performance_percent = current_performance
        
        # Sauvegarder la session
        session.save()
        
        # Créer le trade dans la base de données
        Trade.objects.create(
            session=session,
            trade_number=session.total_trades,
            capital_before=capital_before,
            capital_after=session.current_capital,
            risk_percent=risk_percent,
            risk_amount=result['risk_amount'],
            outcome_multiplier=result['multiplier'],  # Utiliser 'multiplier' pas 'outcome'
            profit_loss=result['profit_loss'],
            is_win=result['is_win']
        )
        
        trades_executed += 1
    
    # Calculer les statistiques finales (méthode statique)
    stats = TradingSimulator.calculate_statistics(
        Trade.objects.filter(session=session),
        session
    )
    
    # Récupérer TOUS les trades pour l'equity curve et le graphique de risque
    # Utiliser values() pour être cohérent avec les autres endpoints
    history = list(Trade.objects.filter(session=session).values(
        'trade_number', 'capital_after', 'risk_percent'
    ).order_by('trade_number'))
    
    return JsonResponse({
        'success': True,
        'trades_executed': trades_executed,
        'account_crashed': account_crashed,
        'stats': stats,
        'history': history
    })
