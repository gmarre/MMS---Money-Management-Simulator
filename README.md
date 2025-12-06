# MMS - Money Management Simulator

Projet Django pour la simulation de gestion de portefeuille boursier.

## Structure du projet

```
MMS - Money Management Simulator/
├── config/              # Configuration principale du projet Django
│   ├── settings.py     # Paramètres du projet
│   ├── urls.py         # Routes URL principales
│   └── wsgi.py         # Point d'entrée WSGI
├── home/               # Application principale
│   ├── views.py        # Vues de l'application
│   ├── models.py       # Modèles de données
│   └── admin.py        # Configuration admin
├── manage.py           # Script de gestion Django
└── .venv/              # Environnement virtuel Python
```

## Installation et démarrage

### Activer l'environnement virtuel

```powershell
.\.venv\Scripts\Activate.ps1
```

### Installer les dépendances

```powershell
pip install django
```

### Lancer le serveur de développement

```powershell
python manage.py runserver
```

Le site sera accessible sur http://127.0.0.1:8000/

## Commandes utiles

- Créer les migrations : `python manage.py makemigrations`
- Appliquer les migrations : `python manage.py migrate`
- Créer un super utilisateur : `python manage.py createsuperuser`
- Lancer les tests : `python manage.py test`
