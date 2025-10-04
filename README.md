
# 🚀 Déploiement d'Airflow : une approche hybride

## 🎯 Objectif

Ce guide explique comment déployer **Airflow** avec **Docker Compose**, et configurer les connexions à **PostgreSQL** et **AWS S3** directement dans l’interface Airflow pour déployer votre première vraie pipeline !

---

## 🛠 Prérequis

- **Docker & Docker Compose** installés
- Un **bucket S3** 
- Une **base de données PostgreSQL** 

---


## 📌 1. docker-compose.yaml (Déploiement Airflow)

Récuperez le docker-compose 

---

## 📌 2. Démarrage du Serveur Airflow

1. Lancer les conteneurs : (pas besoin de build c'est fait dans le docker compose)

```bash
docker-compose up airflow-init
```

```bash
docker-compose up
```

2. Accéder à Airflow :
   - Ouvrez http://localhost:8080.
   - Connectez-vous avec airflow / airflow.

---

## 📌 3. Configuration des Connexions dans Airflow

### Connexion AWS (S3)

1. Admin > Connections dans Airflow.
2. Créez une connexion avec :

   - Conn Id : aws_default
   - Conn Type : Amazon Web Services
   - AWS Access Key ID : VOTRE_ACCESS_KEY
   - AWS Secret Access Key : VOTRE_SECRET_KEY
   - Extra :

   ```json
   {
     "region_name": "VOTRE_REGION"
   }
   ```

3. Sauvegardez.

### Connexion PostgreSQL

1. Admin > Connections dans Airflow.
2. Créez une connexion avec :
   - Conn Id : postgres_default
   - Conn Type : Postgres
   - Host : VOTRE_HOST
   - Database : VOTRE_BDD
   - Login : VOTRE_UTILISATEUR
   - Password : VOTRE_MOT_DE_PASSE
   - Port : 5432
   - Extra :
   ```json
   {
     "sslmode": "require"
   }
   ```
3. Sauvegardez.

---

## 📌 4. Vous pouvez maintenant trigger votre dags !
