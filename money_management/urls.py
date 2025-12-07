"""
URLs pour le module Money Management
"""

from django.urls import path
from . import views
from . import views_reference

app_name = 'money_management'

urlpatterns = [
    # Page HTML principale (visualiseur interactif)
    path('', views.visualizer_view, name='visualizer_view'),
    
    # Batch Runner
    path('batch/', views.batch_runner_view, name='batch_runner'),
    path('batch/run/', views.run_batch_simulations, name='run_batch'),
    path('batch/results/', views.batch_results_view, name='batch_results'),
    path('batch/<str:batch_id>/stats/', views.get_batch_statistics, name='batch_stats'),
    path('batch/<str:batch_id>/strategy/<str:strategy_key>/', views.get_strategy_details, name='strategy_details'),
    path('batch/<str:batch_id>/delete/', views.delete_batch, name='delete_batch'),
    
    # Ancienne page des stratégies
    path('list/', views.strategies_view, name='strategies_view'),
    
    # API: Liste des stratégies disponibles
    path('strategies/', views.list_strategies, name='list_strategies'),
    
    # API: Endpoint générique pour exécuter une stratégie
    path('simulate/<str:strategy_name>/', views.simulate_strategy, name='simulate_strategy'),
    
    # API: Gestion des paramètres de référence
    path('reference/<str:strategy_key>/save/', views_reference.save_reference_params, name='save_reference'),
    path('reference/<str:strategy_key>/load/', views_reference.load_reference_params, name='load_reference'),
    path('reference/<str:strategy_key>/delete/', views_reference.delete_reference_params, name='delete_reference'),
]
