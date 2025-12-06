"""
URLs pour le module Money Management
"""

from django.urls import path
from . import views

app_name = 'money_management'

urlpatterns = [
    # Page HTML principale (visualiseur interactif)
    path('', views.visualizer_view, name='visualizer_view'),
    
    # Ancienne page des stratégies
    path('list/', views.strategies_view, name='strategies_view'),
    
    # API: Liste des stratégies disponibles
    path('strategies/', views.list_strategies, name='list_strategies'),
    
    # API: Endpoint générique pour exécuter une stratégie
    path('simulate/<str:strategy_name>/', views.simulate_strategy, name='simulate_strategy'),
]
