"""
Views pour la gestion des paramètres de référence des stratégies
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .strategies import STRATEGIES
from .models import StrategyReference


@csrf_exempt
def save_reference_params(request, strategy_key):
    """
    Sauvegarde les paramètres actuels comme référence pour une stratégie
    
    Method: POST
    Body: { "params": {...} }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        params = data.get('params', {})
        
        if strategy_key not in STRATEGIES:
            return JsonResponse({
                'success': False,
                'error': f'Stratégie "{strategy_key}" non trouvée'
            }, status=404)
        
        strategy_info = STRATEGIES[strategy_key]
        
        # Créer ou mettre à jour la référence
        reference, created = StrategyReference.objects.update_or_create(
            strategy_key=strategy_key,
            defaults={
                'strategy_name': strategy_info['name'],
                'reference_params': params
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Paramètres de référence sauvegardés' if created else 'Paramètres de référence mis à jour',
            'strategy_key': strategy_key,
            'strategy_name': strategy_info['name'],
            'params': params
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def load_reference_params(request, strategy_key):
    """
    Charge les paramètres de référence pour une stratégie
    
    Method: GET
    """
    try:
        if strategy_key not in STRATEGIES:
            return JsonResponse({
                'success': False,
                'error': f'Stratégie "{strategy_key}" non trouvée'
            }, status=404)
        
        try:
            reference = StrategyReference.objects.get(strategy_key=strategy_key)
            return JsonResponse({
                'success': True,
                'strategy_key': strategy_key,
                'strategy_name': reference.strategy_name,
                'params': reference.reference_params,
                'saved_at': reference.updated_at.isoformat()
            })
        except StrategyReference.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Aucune référence sauvegardée pour cette stratégie',
                'has_reference': False
            }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def delete_reference_params(request, strategy_key):
    """
    Supprime les paramètres de référence pour une stratégie
    
    Method: DELETE
    """
    if request.method != 'DELETE':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        try:
            reference = StrategyReference.objects.get(strategy_key=strategy_key)
            reference.delete()
            return JsonResponse({
                'success': True,
                'message': 'Paramètres de référence supprimés'
            })
        except StrategyReference.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Aucune référence trouvée pour cette stratégie'
            }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
