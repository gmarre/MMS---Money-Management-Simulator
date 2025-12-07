"""
Views Django pour exécuter les 20 stratégies de Money Management
"""

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Avg, Max, Min, Count
from decimal import Decimal
import json
import uuid
import hashlib

from .strategies import STRATEGIES
from .simulator import run_simulation
from .models import SimulationResult, SimulationBatch


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


def batch_runner_view(request):
    """
    Vue principale pour le batch runner de simulations
    """
    strategies_data = []
    for key, info in STRATEGIES.items():
        strategies_data.append({
            'key': key,
            'name': info['name'],
            'description': info['description'],
            'params': info['params']
        })
    
    return render(request, 'money_management/batch_runner.html', {
        'strategies_json': json.dumps(strategies_data)
    })


@csrf_exempt
def run_batch_simulations(request):
    """
    Lance un batch de simulations
    
    POST /money-management/batch/run/
    Body: {
        "batch_name": "Test Stratégies DD",
        "simulations": [
            {
                "strategy_key": "strategy_1",
                "num_simulations": 20,
                "num_trades": 3000,
                "initial_capital": 10000,
                "params": {"base_risk": 0.5, "dd1": 5, "dd2": 20}
            },
            {
                "strategy_key": "strategy_2",
                "num_simulations": 20,
                "num_trades": 3000,
                "initial_capital": 10000,
                "params": {"base_risk": 0.5, "dd_step": 5, "decay": 0.8}
            }
        ]
    }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        batch_name = data.get('batch_name', f'Batch {timezone.now().strftime("%Y-%m-%d %H:%M")}')
        simulations_config = data.get('simulations', [])
        save_equity_curves = data.get('save_equity_curves', False)  # Option pour sauvegarder les equity curves
        
        if not simulations_config:
            return JsonResponse({'success': False, 'error': 'No simulations configured'}, status=400)
        
        # Calculer le nombre total de simulations
        total_sims = sum(s.get('num_simulations', 1) for s in simulations_config)
        
        # Créer le batch
        batch_id = str(uuid.uuid4())
        batch = SimulationBatch.objects.create(
            batch_id=batch_id,
            name=batch_name,
            description=f"{len(simulations_config)} configurations de stratégies",
            total_simulations=total_sims,
            status='running',
            has_equity_curves=save_equity_curves
        )
        
        # Exécuter toutes les simulations
        completed = 0
        results = []
        
        for sim_config in simulations_config:
            strategy_key = sim_config.get('strategy_key')
            num_simulations = sim_config.get('num_simulations', 1)
            num_trades = sim_config.get('num_trades', 1000)
            initial_capital = sim_config.get('initial_capital', 10000)
            params = sim_config.get('params', {})
            outcomes_config = sim_config.get('outcomes_config', None)
            
            if strategy_key not in STRATEGIES:
                continue
            
            strategy_info = STRATEGIES[strategy_key]
            strategy_function = strategy_info['function']
            
            # Générer un identifiant unique incluant les paramètres
            # Hash MD5 des paramètres pour différencier les variations
            params_str = json.dumps(params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            unique_strategy_key = f"{strategy_key}_{params_hash}"
            
            # Utiliser le preset balanced par défaut si outcomes_config n'est pas fourni
            if outcomes_config is None:
                outcomes_config = {
                    '-1': 12,
                    '-5': 2,
                    '2': 3,
                    '3': 2,
                    '4': 1,
                    '5': 1,
                    '9': 1
                }
            
            # Lancer num_simulations fois cette configuration
            for i in range(num_simulations):
                try:
                    print(f"[BATCH {batch_id[:8]}] Simulation {completed + 1}/{total_sims} - {strategy_info['name']} (run {i+1}/{num_simulations})")
                    
                    # Exécuter la simulation
                    result = run_simulation(
                        strategy_function=strategy_function,
                        outcomes_config=outcomes_config,
                        initial_capital=initial_capital,
                        params=params,
                        n=num_trades
                    )
                    
                    # Calculer les statistiques
                    trades = result.get('history', [])
                    
                    # Calculer les statistiques de risque
                    avg_risk_pct = sum(t['risk_percent'] for t in trades) / len(trades) if trades else 0
                    avg_risk_amount = sum(t['risk_amount'] for t in trades) / len(trades) if trades else 0
                    avg_profit_loss = sum(t['profit_loss'] for t in trades) / len(trades) if trades else 0
                    
                    # Calculer les séries consécutives
                    max_consecutive_wins = 0
                    max_consecutive_losses = 0
                    current_wins = 0
                    current_losses = 0
                    
                    for trade in trades:
                        if trade['profit_loss'] > 0:
                            current_wins += 1
                            current_losses = 0
                            max_consecutive_wins = max(max_consecutive_wins, current_wins)
                        else:
                            current_losses += 1
                            current_wins = 0
                            max_consecutive_losses = max(max_consecutive_losses, current_losses)
                    
                    # Calculer le taux de réussite
                    total_wins = sum(1 for t in trades if t['profit_loss'] > 0)
                    total_losses = len(trades) - total_wins
                    success_rate = (total_wins / len(trades) * 100) if trades else 0
                    
                    # Calculer max capital et max performance
                    equity_curve = result.get('equity_curve', [initial_capital])
                    max_capital = max(equity_curve)
                    
                    # Limite maximale stockable dans une base de données (Decimal peut aller jusqu'à 10^28 mais on limite pour la sécurité)
                    MAX_STORABLE = Decimal('9999999999999')  # ~10 trillions (13 chiffres)
                    
                    final_capital = result['capital_final']
                    
                    # Détection d'overflow et plafonnement
                    is_overflow = False
                    try:
                        final_capital_decimal = Decimal(str(final_capital))
                        if final_capital_decimal > MAX_STORABLE:
                            final_capital_decimal = MAX_STORABLE
                            is_overflow = True
                    except:
                        final_capital_decimal = MAX_STORABLE
                        is_overflow = True
                    
                    try:
                        max_capital_decimal = Decimal(str(max_capital))
                        if max_capital_decimal > MAX_STORABLE:
                            max_capital_decimal = MAX_STORABLE
                            is_overflow = True
                    except:
                        max_capital_decimal = MAX_STORABLE
                        is_overflow = True
                    
                    # Calculer les performances (gérer l'overflow)
                    try:
                        final_performance_pct = Decimal(str(((float(final_capital_decimal) - initial_capital) / initial_capital) * 100))
                        if final_performance_pct > MAX_STORABLE:
                            final_performance_pct = MAX_STORABLE
                    except:
                        final_performance_pct = MAX_STORABLE
                    
                    try:
                        max_performance_pct = Decimal(str(((float(max_capital_decimal) - initial_capital) / initial_capital) * 100))
                        if max_performance_pct > MAX_STORABLE:
                            max_performance_pct = MAX_STORABLE
                    except:
                        max_performance_pct = MAX_STORABLE
                    
                    # Sauvegarder dans la base de données
                    try:
                        # Préparer l'equity curve si demandé
                        equity_curve_data = None
                        if save_equity_curves:
                            equity_curve_data = [round(float(val), 2) for val in equity_curve]
                        
                        sim_result = SimulationResult.objects.create(
                            strategy_name=strategy_info['name'],
                            strategy_key=unique_strategy_key,
                            parameters=params,
                            num_trades=num_trades,
                            initial_capital=Decimal(str(initial_capital)),
                            final_capital=final_capital_decimal,
                            final_performance_pct=final_performance_pct,
                            max_capital=max_capital_decimal,
                            max_drawdown_pct=Decimal(str(result['drawdown_max'])),
                            max_performance_pct=max_performance_pct,
                            avg_risk_pct=Decimal(str(avg_risk_pct)),
                            avg_risk_amount=Decimal(str(min(avg_risk_amount, float(MAX_STORABLE)))),
                            avg_profit_loss=Decimal(str(min(avg_profit_loss, float(MAX_STORABLE)))),
                            max_consecutive_wins=max_consecutive_wins,
                            max_consecutive_losses=max_consecutive_losses,
                            success_rate=Decimal(str(success_rate)),
                            total_wins=total_wins,
                            total_losses=total_losses,
                            batch_id=batch_id,
                            equity_curve=equity_curve_data  # Sauvegarder l'equity curve si demandé
                        )
                        
                        completed += 1
                        
                        if is_overflow:
                            print(f"  ✅ Terminé (OVERFLOW MAX) - Perf: >{sim_result.final_performance_pct:.2f}% | DD: {sim_result.max_drawdown_pct:.2f}%")
                        else:
                            print(f"  ✅ Terminé - Perf: {sim_result.final_performance_pct:.2f}% | DD: {sim_result.max_drawdown_pct:.2f}%")
                        
                        results.append({
                            'id': sim_result.id,
                            'strategy': strategy_info['name'],
                            'final_performance': float(sim_result.final_performance_pct),
                            'max_drawdown': float(sim_result.max_drawdown_pct)
                        })
                    except Exception as db_error:
                        print(f"  ❌ Erreur DB: {str(db_error)}")
                        continue
                    
                except Exception as e:
                    print(f"  ❌ Erreur simulation {i+1}: {str(e)}")
                    continue
        
        # Mettre à jour le batch
        batch.completed_simulations = completed
        batch.status = 'completed'
        batch.completed_at = timezone.now()
        batch.save()
        
        print('=' * 80)
        print(f"✅ BATCH TERMINÉ: {batch_name}")
        print(f"📊 Résumé: {completed}/{total_sims} simulations réussies")
        if completed < total_sims:
            print(f"⚠️  {total_sims - completed} simulations ont échoué (overflow ou erreurs)")
        print(f"🔗 Batch ID: {batch_id}")
        print('=' * 80)
        
        return JsonResponse({
            'success': True,
            'batch_id': batch_id,
            'total_simulations': total_sims,
            'completed': completed,
            'results': results[:10]  # Retourner seulement les 10 premiers pour ne pas surcharger
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def delete_batch(request, batch_id):
    """
    Supprime un batch et toutes ses simulations
    
    DELETE /money-management/batch/<batch_id>/delete/
    """
    if request.method != 'POST' and request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        batch = SimulationBatch.objects.get(batch_id=batch_id)
        batch_name = batch.name
        
        # Compter les simulations avant suppression
        num_simulations = SimulationResult.objects.filter(batch_id=batch_id).count()
        
        # Supprimer toutes les simulations associées
        SimulationResult.objects.filter(batch_id=batch_id).delete()
        
        # Supprimer le batch
        batch.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Batch "{batch_name}" supprimé avec succès',
            'deleted_simulations': num_simulations
        })
        
    except SimulationBatch.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Batch not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def batch_results_view(request):
    """
    Vue pour afficher les résultats des simulations batch
    """
    # Récupérer tous les batches
    batches = SimulationBatch.objects.all()
    
    return render(request, 'money_management/batch_results.html', {
        'batches': batches
    })


def get_strategy_details(request, batch_id, strategy_key):
    """
    Récupère les détails de toutes les simulations d'une stratégie dans un batch
    
    GET /money-management/batch/<batch_id>/strategy/<strategy_key>/
    """
    try:
        batch = SimulationBatch.objects.get(batch_id=batch_id)
        results = SimulationResult.objects.filter(
            batch_id=batch_id,
            strategy_key=strategy_key
        ).order_by('-final_performance_pct')
        
        if not results.exists():
            return JsonResponse({
                'success': False,
                'error': 'No results found for this strategy'
            }, status=404)
        
        # Convertir les résultats en liste de dictionnaires
        simulations = []
        for result in results:
            sim_data = {
                'id': result.id,
                'strategy_name': result.strategy_name,
                'parameters': result.parameters,
                'num_trades': result.num_trades,
                'initial_capital': float(result.initial_capital),
                'final_capital': float(result.final_capital),
                'final_performance_pct': float(result.final_performance_pct),
                'max_capital': float(result.max_capital),
                'max_drawdown_pct': float(result.max_drawdown_pct),
                'max_performance_pct': float(result.max_performance_pct),
                'avg_risk_pct': float(result.avg_risk_pct),
                'avg_risk_amount': float(result.avg_risk_amount),
                'avg_profit_loss': float(result.avg_profit_loss),
                'max_consecutive_wins': result.max_consecutive_wins,
                'max_consecutive_losses': result.max_consecutive_losses,
                'success_rate': float(result.success_rate),
                'total_wins': result.total_wins,
                'total_losses': result.total_losses,
                'created_at': result.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Ajouter l'equity curve si disponible
            if result.equity_curve:
                sim_data['equity_curve'] = result.equity_curve
            
            simulations.append(sim_data)
        
        return JsonResponse({
            'success': True,
            'batch_id': batch_id,
            'batch_name': batch.name,
            'strategy_key': strategy_key,
            'strategy_name': results.first().strategy_name,
            'total_simulations': len(simulations),
            'simulations': simulations
        })
        
    except SimulationBatch.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Batch not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def get_batch_statistics(request, batch_id):
    """
    Récupère les statistiques d'un batch
    
    GET /money-management/batch/<batch_id>/stats/
    """
    try:
        batch = SimulationBatch.objects.get(batch_id=batch_id)
        results = SimulationResult.objects.filter(batch_id=batch_id)
        
        if not results.exists():
            return JsonResponse({
                'success': False,
                'error': 'No results found for this batch'
            }, status=404)
        
        # Regrouper par stratégie
        strategies_stats = {}
        
        for strategy_key in results.values_list('strategy_key', flat=True).distinct():
            strategy_results = results.filter(strategy_key=strategy_key)
            
            # Calculer les statistiques agrégées
            stats = strategy_results.aggregate(
                count=Count('id'),
                avg_final_perf=Avg('final_performance_pct'),
                median_final_perf=Avg('final_performance_pct'),  # Approximation
                avg_drawdown=Avg('max_drawdown_pct'),
                median_drawdown=Avg('max_drawdown_pct'),  # Approximation
                max_perf=Max('final_performance_pct'),
                min_perf=Min('final_performance_pct'),
                max_dd=Max('max_drawdown_pct'),
                min_dd=Min('max_drawdown_pct'),
                avg_success_rate=Avg('success_rate'),
                avg_consecutive_wins=Avg('max_consecutive_wins'),
                avg_consecutive_losses=Avg('max_consecutive_losses')
            )
            
            # Récupérer le nom de la stratégie
            first_result = strategy_results.first()
            
            strategies_stats[strategy_key] = {
                'strategy_name': first_result.strategy_name,
                'parameters': first_result.parameters,
                'num_simulations': stats['count'],
                'performance': {
                    'avg': float(stats['avg_final_perf'] or 0),
                    'median': float(stats['median_final_perf'] or 0),
                    'max': float(stats['max_perf'] or 0),
                    'min': float(stats['min_perf'] or 0)
                },
                'drawdown': {
                    'avg': float(stats['avg_drawdown'] or 0),
                    'median': float(stats['median_drawdown'] or 0),
                    'max': float(stats['max_dd'] or 0),
                    'min': float(stats['min_dd'] or 0)
                },
                'success_rate_avg': float(stats['avg_success_rate'] or 0),
                'consecutive_wins_avg': float(stats['avg_consecutive_wins'] or 0),
                'consecutive_losses_avg': float(stats['avg_consecutive_losses'] or 0)
            }
        
        return JsonResponse({
            'success': True,
            'batch_id': batch_id,
            'batch_name': batch.name,
            'total_simulations': batch.total_simulations,
            'strategies': strategies_stats
        })
        
    except SimulationBatch.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Batch not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
