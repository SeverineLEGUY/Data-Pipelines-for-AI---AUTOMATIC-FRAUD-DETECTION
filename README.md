AUTOMATIC FRAUD DETECTION : UNE ARCHITECTURE HYBRIDE

1. Détection de Fraude en Temps Réel dans une Infrastructure de Données robuste! </br>
<b>Description:
Ce projet met en place une infrastructure complète pour la détection automatisée et en temps réel de transactions frauduleuses. En utilisant un pipeline de données robuste, il ingère les paiements en continu via une API, les analyse instantanément avec un modèle de Machine Learning et envoie des notifications immédiates en cas de fraude. L'objectif est de dépasser le simple algorithme pour créer une solution de production fiable, capable de gérer des volumes de données importants et de fournir des rapports quotidiens pour l'analyse métier.<br>

2. Objectifs du Projet 🎯
Ce projet a été conçu pour répondre à deux besoins métiers fondamentaux :
   - la détection en temps réel: le système doit pouvoir identifier et notifier une fraude instantanément au moment où une transaction se produit. 
   - la production d'un rapport quotidien qui fournit une vue d'ensemble des fraudes de la veille, essentielle pour l'analyse et la prise de décision.

3. Architecture Overview
Include the infrastructure diagram you've created.

Provide a high-level explanation of how the services interact. You can use the table above as a guide, explaining each component and its role.

4. Prerequisites
List all necessary software for the user to have installed on their machine (e.g., Docker, Docker Compose, Git).

5. Getting Started
Step 1: Clone the repository. Provide the Git command.

Step 2: Configure Environment Variables. Explain that the .env file must be created from a template and filled in with the user's credentials (e.g., for AWS, NeonDB, and Gmail). This is a critical step, as your pipeline relies on these variables for successful authentication.

Step 3: Build and Run the containers. Provide the docker-compose up command. Mention that it might take a while to build all the images for the first time.

Step 4: Run the Training Pipeline. Explain how to trigger the train_model_prod.py and deploy_model.py scripts. You could even provide the command to run them from the airflow-cli service.

Step 5: Run the Data Ingestion Script. Explain how to run insert_data-db.py to populate the database with test fraud data.

Step 6: Access the Airflow UI. Provide the URL and default credentials (airflow/airflow) for the user to access the web server. Instruct them to manually enable the daily_fraud_report_pipeline DAG.

6. File Structure
Include a simple tree-like structure of your project files (you can use a text version of the image you provided). This helps users quickly find files.

7. Conclusion & Next Steps
Summarize the project's success and propose potential improvements, such as adding a deploy DAG to automate model updates or a Slack notification for real-time alerts.









# 🚀 Déploiement d'Airflow pour votre première pipeline

## 🎯 Objectif

Ce guide explique comment déployer **Airflow** avec **Docker Compose**, et configurer les connexions à **PostgreSQL** et **AWS S3** directement dans l’interface Airflow pour déployer votre première vraie pipeline !

---

## 🛠 Prérequis

- **Docker & Docker Compose** installés
- Un **bucket S3** (à créer)
- Une **base de données PostgreSQL** (à créer via NeonDB, Kubernetes, ou Docker)

---

## 📌 1. Dockerfile (Image Airflow)

Le fichier `Dockerfile` utilisé pour construire l’image Airflow :

```dockerfile
FROM apache/airflow:2.10.4-python3.10

USER root  # Passer en root pour installer les dépendances

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

USER airflow  # Revenir à l’utilisateur airflow pour la sécurité

# Copier les dépendances Python
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --upgrade --no-build-isolation -r requirements.txt
```

---

## 📌 2. requirements.txt (Dépendances Python)

Les packages requis :

```
apache-airflow-providers-postgres
apache-airflow-providers-amazon
psycopg[binary]
pandas
```

---

## 📌 3. docker-compose.yaml (Déploiement Airflow)

Récuperez le docker-compose du zip.

---

## 📌 4. Démarrage du Serveur Airflow

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

## 📌 5. Configuration des Connexions dans Airflow

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

## 📌 6. Configuration des Variables d'Environnement dans Airflow

Dans Airflow, les variables d’environnement peuvent être définies directement via l’interface web.

### Étapes :

1. Accédez à l'interface Airflow (http://localhost:8080).
2. Allez dans :
   Admin → Variables → "+" (Ajouter une variable)"
3. Ajoutez les variables suivantes :
   - S3BucketName → Nom du bucket S3
   - WeatherBitApiKey → Clé API WeatherBit
4. Exemple de configuration :
   | Clé | Valeur |
   | :--------------- | :-----------------: |
   | S3BucketName | nom-de-votre-bucket |
   | WeatherBitApiKey | votre-clé-api |

5. Cliquez sur "Enregistrer".

---

## 📌 7. Vous pouvez maintenant trigger votre dags !
