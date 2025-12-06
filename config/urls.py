"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from home import views
from home import strategy_views  # Import pour les vues de stratégies

urlpatterns = [
    path('', views.simulator_view, name='home'),
    path('api/get-presets/', views.get_presets, name='get_presets'),
    path('api/start-session/', views.start_session, name='start_session'),
    path('api/execute-trade/', views.execute_trade, name='execute_trade'),
    path('api/execute-batch-trades/', views.execute_batch_trades, name='execute_batch_trades'),
    path('api/execute-strategy-batch/', strategy_views.execute_strategy_batch, name='execute_strategy_batch'),  # Nouveau endpoint
    path('api/get-stats/', views.get_stats, name='get_stats'),
    path('money-management/', include('money_management.urls')),
    path('admin/', admin.site.urls),
]
