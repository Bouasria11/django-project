# Commandes Rapides - Films Platform

## Setup Initial
```bash
# Installer les dépendances
pip install -r requirements.txt

# Appliquer les migrations
python manage.py makemigrations movies
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver
```

## Commandes Utiles

### Développement
```bash
# Créer des migrations à partir des modèles
python manage.py makemigrations movies

# Appliquer les migrations
python manage.py migrate

# Vider la base et recommencer
python manage.py flush

# Créer un superutilisateur admin
python manage.py createsuperuser

# Lancer le shell Django
python manage.py shell
```

### Tests
```bash
# Lancer tous les tests
python manage.py test

# Tester une app spécifique
python manage.py test movies

# Lancer les tests avec coverage
coverage run --source='.' manage.py test
coverage report
```

### Administration
```bash
# Collecter les fichiers statiques pour la production
python manage.py collectstatic --noinput

# Create a database dump
python manage.py dumpdata > backup.json

# Restore from dump
python manage.py loaddata backup.json
```

## Accès
- Application : http://127.0.0.1:8000/
- Admin : http://127.0.0.1:8000/admin/

## Résolution de Problèmes

### Erreur "no module named 'django'"
```bash
pip install -r requirements.txt
```

### Erreur de migration
```bash
python manage.py makemigrations movies --check
python manage.py migrate --fake-initial
```

### Problème de media files
En développement, vérifiez que `MEDIA_URL` et `MEDIA_ROOT` sont bien configurés dans `urls.py`.
