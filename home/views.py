from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
import json

from .models import TradingSession, Trade
from .trading_logic import TradingSimulator


def simulator_view(request):
    """Vue principale du simulateur"""
    return render(request, 'home/simulator.html')


def get_presets(request):
    """Récupère les presets de probabilités disponibles"""
    return JsonResponse({
        'success': True,
        'presets': TradingSimulator.PRESETS
    })


def get_or_create_session(request):
    """Récupère ou crée une session de trading"""
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    trading_session, created = TradingSession.objects.get_or_create(
        session_key=session_key
    )
    return trading_session


@csrf_exempt
def start_session(request):
    """Démarre une nouvelle session avec un capital initial"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            initial_capital = Decimal(str(data.get('initial_capital', 1000)))
            outcomes_config = data.get('outcomes_config', {})
            
            # Récupérer ou créer la session
            trading_session = get_or_create_session(request)
            
            # Réinitialiser la session
            trading_session.initial_capital = initial_capital
            trading_session.current_capital = initial_capital
            trading_session.max_capital = initial_capital
            trading_session.total_trades = 0
            trading_session.consecutive_wins = 0
            trading_session.consecutive_losses = 0
            trading_session.max_consecutive_wins = 0
            trading_session.max_consecutive_losses = 0
            trading_session.max_drawdown_percent = 0
            trading_session.max_performance_percent = 0
            trading_session.outcomes_config = outcomes_config
            trading_session.save()
            
            # Supprimer tous les anciens trades
            Trade.objects.filter(session=trading_session).delete()
            
            return JsonResponse({
                'success': True,
                'initial_capital': float(initial_capital),
                'current_capital': float(initial_capital),
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def execute_trade(request):
    """Exécute un trade avec le pourcentage de risque spécifié"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            risk_percent = Decimal(str(data.get('risk_percent')))
            
            # Récupérer la session
            trading_session = get_or_create_session(request)
            
            # Exécuter le trade
            result = TradingSimulator.execute_trade(
                trading_session.current_capital,
                risk_percent,
                trading_session.outcomes_config
            )
            
            # Créer l'enregistrement du trade
            trade_number = trading_session.total_trades + 1
            trade = Trade.objects.create(
                session=trading_session,
                trade_number=trade_number,
                capital_before=trading_session.current_capital,
                capital_after=result['new_capital'],
                risk_percent=risk_percent,
                risk_amount=result['risk_amount'],
                outcome_multiplier=result['multiplier'],
                profit_loss=result['profit_loss'],
                is_win=result['is_win']
            )
            
            # Mettre à jour la session
            trading_session.current_capital = result['new_capital']
            trading_session.total_trades = trade_number
            
            # Mettre à jour les séries de victoires/défaites
            if result['is_win']:
                trading_session.consecutive_wins += 1
                trading_session.consecutive_losses = 0
                if trading_session.consecutive_wins > trading_session.max_consecutive_wins:
                    trading_session.max_consecutive_wins = trading_session.consecutive_wins
            else:
                trading_session.consecutive_losses += 1
                trading_session.consecutive_wins = 0
                if trading_session.consecutive_losses > trading_session.max_consecutive_losses:
                    trading_session.max_consecutive_losses = trading_session.consecutive_losses
            
            # Mettre à jour le capital maximum
            if result['new_capital'] > trading_session.max_capital:
                trading_session.max_capital = result['new_capital']
            
            # Calculer la performance maximale
            current_performance = ((result['new_capital'] - trading_session.initial_capital) / 
                                 trading_session.initial_capital * 100)
            if current_performance > trading_session.max_performance_percent:
                trading_session.max_performance_percent = current_performance
            
            # Calculer le drawdown maximum
            current_drawdown = ((result['new_capital'] - trading_session.max_capital) / 
                              trading_session.max_capital * 100)
            if current_drawdown < trading_session.max_drawdown_percent:
                trading_session.max_drawdown_percent = current_drawdown
            
            trading_session.save()
            
            # Calculer les statistiques
            stats = TradingSimulator.calculate_statistics(
                trading_session.trades.all(),
                trading_session
            )
            
            # Récupérer l'historique pour le graphique
            trades_history = list(trading_session.trades.values(
                'trade_number', 'capital_after'
            ).order_by('trade_number'))
            
            return JsonResponse({
                'success': True,
                'trade': {
                    'number': trade_number,
                    'multiplier': float(result['multiplier']),
                    'risk_amount': float(result['risk_amount']),
                    'profit_loss': float(result['profit_loss']),
                    'is_win': result['is_win'],
                    'new_capital': float(result['new_capital'])
                },
                'stats': stats,
                'history': trades_history
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def execute_batch_trades(request):
    """Exécute plusieurs trades en une seule fois côté serveur"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            risk_percent = Decimal(str(data.get('risk_percent', 1)))
            count = int(data.get('count', 1000))
            
            trading_session = get_or_create_session(request)
            
            if trading_session.current_capital <= 0:
                return JsonResponse({
                    'success': False,
                    'error': 'Capital insuffisant pour trader'
                }, status=400)
            
            # Récupérer la configuration des outcomes
            if hasattr(trading_session, 'outcomes_config') and trading_session.outcomes_config:
                outcomes_config = trading_session.outcomes_config
            else:
                outcomes_config = {}
            
            # Exécuter tous les trades en boucle
            trades_executed = 0
            for i in range(count):
                if trading_session.current_capital < 1:
                    break  # Arrêter si le capital est en dessous de 1€
                
                # Sauvegarder le capital avant le trade
                capital_before = trading_session.current_capital
                
                # Exécuter le trade
                result = TradingSimulator.execute_trade(
                    current_capital=trading_session.current_capital,
                    risk_percent=risk_percent,
                    outcomes_config=outcomes_config
                )
                
                # Créer l'enregistrement du trade
                trade_number = trading_session.total_trades + 1
                Trade.objects.create(
                    session=trading_session,
                    trade_number=trade_number,
                    capital_before=capital_before,
                    capital_after=result['new_capital'],
                    risk_percent=risk_percent,
                    risk_amount=result['risk_amount'],
                    outcome_multiplier=result['multiplier'],
                    profit_loss=result['profit_loss'],
                    is_win=result['is_win']
                )
                
                # Mettre à jour la session
                trading_session.current_capital = result['new_capital']
                trading_session.total_trades = trade_number
                trades_executed += 1
                
                # Si le capital est en dessous de 1€, arrêter immédiatement
                if trading_session.current_capital < 1:
                    break
                
                # Mettre à jour les séries de victoires/défaites
                if result['is_win']:
                    trading_session.consecutive_wins += 1
                    trading_session.consecutive_losses = 0
                    if trading_session.consecutive_wins > trading_session.max_consecutive_wins:
                        trading_session.max_consecutive_wins = trading_session.consecutive_wins
                else:
                    trading_session.consecutive_losses += 1
                    trading_session.consecutive_wins = 0
                    if trading_session.consecutive_losses > trading_session.max_consecutive_losses:
                        trading_session.max_consecutive_losses = trading_session.consecutive_losses
                
                # Mettre à jour le capital maximum
                if result['new_capital'] > trading_session.max_capital:
                    trading_session.max_capital = result['new_capital']
                
                # Calculer la performance maximale
                current_performance = ((result['new_capital'] - trading_session.initial_capital) / 
                                     trading_session.initial_capital * 100)
                if current_performance > trading_session.max_performance_percent:
                    trading_session.max_performance_percent = current_performance
                
                # Calculer le drawdown maximum
                current_drawdown = ((result['new_capital'] - trading_session.max_capital) / 
                                  trading_session.max_capital * 100)
                if current_drawdown < trading_session.max_drawdown_percent:
                    trading_session.max_drawdown_percent = current_drawdown
            
            trading_session.save()
            
            # Calculer les statistiques finales
            stats = TradingSimulator.calculate_statistics(
                trading_session.trades.all(),
                trading_session
            )
            
            # Récupérer l'historique pour le graphique
            trades_history = list(trading_session.trades.values(
                'trade_number', 'capital_after'
            ).order_by('trade_number'))
            
            return JsonResponse({
                'success': True,
                'trades_executed': trades_executed,
                'account_crashed': trading_session.current_capital < 1,
                'stats': stats,
                'history': trades_history
            })
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in execute_batch_trades: {error_details}")
            return JsonResponse({'success': False, 'error': str(e), 'details': error_details}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def get_stats(request):
    """Récupère les statistiques de la session actuelle"""
    try:
        trading_session = get_or_create_session(request)
        stats = TradingSimulator.calculate_statistics(
            trading_session.trades.all(),
            trading_session
        )
        
        # Récupérer l'historique pour le graphique
        trades_history = list(trading_session.trades.values(
            'trade_number', 'capital_after'
        ).order_by('trade_number'))
        
        return JsonResponse({
            'success': True,
            'stats': stats,
            'history': trades_history
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
