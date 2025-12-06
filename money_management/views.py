"""
Views Django pour exécuter les 20 stratégies de Money Management
"""

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json

from .strategies import STRATEGIES
from .simulator import run_simulation


def strategies_view(request):
    """
    Vue pour afficher la page HTML des stratégies (ancienne version)
    """
    return render(request, 'money_management/strategies.html')


def visualizer_view(request):
    """
    Vue pour afficher le visualiseur interactif des stratégies
    """
    # Préparer les données des stratégies pour le JSON
    strategies_data = []
    for key, info in STRATEGIES.items():
        strategies_data.append({
            'key': key,
            'name': info['name'],
            'description': info['description'],
            'params': info['params']
        })
    
    return render(request, 'money_management/visualizer.html', {
        'strategies_json': json.dumps(strategies_data)
    })


@csrf_exempt
def simulate_strategy(request, strategy_name):
    """
    Endpoint générique pour simuler n'importe quelle stratégie
    
    URL: /money-management/simulate/<strategy_name>/
    Method: POST
    
    Body: {
        "initial_capital": 1000,  # optionnel
        "outcomes_config": {...},  # optionnel, sinon preset balanced
        "params": {...},  # paramètres de la stratégie (optionnel)
        "n_trades": 1000  # optionnel
    }
    
    Response: {
        "success": true,
        "strategy_name": "...",
        "capital_final": 1234.56,
        "drawdown_max": -15.3,
        "moyenne": 2.34,
        "ecart_type": 45.67,
        "equity_curve": [...],
        "trades_executed": 1000,
        "account_crashed": false
    }
    """
    # Vérifier que la stratégie existe
    if strategy_name not in STRATEGIES:
        return JsonResponse({
            'success': False,
            'error': f'Stratégie "{strategy_name}" non trouvée',
            'available_strategies': list(STRATEGIES.keys())
        }, status=404)
    
    # Récupérer les paramètres de la requête
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}
    
    # Paramètres par défaut
    initial_capital = data.get('initial_capital', 1000)
    n_trades = data.get('n_trades', 1000)
    
    # Outcomes config (preset balanced par défaut)
    outcomes_config = data.get('outcomes_config', {
        '-1': 12, '-5': 2, '2': 3, '3': 2, '4': 1, '5': 1, '9': 1
    })
    
    # Paramètres de la stratégie (merge avec valeurs par défaut)
    strategy_info = STRATEGIES[strategy_name]
    strategy_params = strategy_info['params'].copy()
    if 'params' in data:
        strategy_params.update(data['params'])
    
    # Exécuter la simulation
    strategy_function = strategy_info['function']
    result = run_simulation(
        strategy_function=strategy_function,
        outcomes_config=outcomes_config,
        initial_capital=initial_capital,
        params=strategy_params,
        n=n_trades
    )
    
    # Retourner le résultat
    return JsonResponse({
        'success': True,
        'strategy_name': strategy_info['name'],
        'strategy_key': strategy_name,
        'description': strategy_info['description'],
        'params_used': strategy_params,
        'capital_initial': initial_capital,
        'capital_final': round(result['capital_final'], 2),
        'drawdown_max': round(result['drawdown_max'], 2),
        'moyenne': round(result['moyenne'], 2),
        'ecart_type': round(result['ecart_type'], 2),
        'equity_curve': [round(val, 2) for val in result['equity_curve']],
        'trades_executed': result['trades_executed'],
        'account_crashed': result['account_crashed']
    })


def list_strategies(request):
    """
    Liste toutes les stratégies disponibles
    
    URL: /money-management/strategies/
    Method: GET
    """
    strategies_list = []
    for key, info in STRATEGIES.items():
        strategies_list.append({
            'key': key,
            'name': info['name'],
            'description': info['description'],
            'params': info['params']
        })
    
    return JsonResponse({
        'success': True,
        'strategies': strategies_list,
        'total': len(strategies_list)
    })
