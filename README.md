# 🚀 Détection Automatique de Fraude : Pipeline Airflow

## 🎯 Objectif du Projet

Ce projet implémente une solution d'**Orchestration de Workflows** utilisant **Apache Airflow** pour la détection quotidienne et le reporting de transactions potentiellement frauduleuses. Il simule un environnement de production en :

1.  Stockant un jeu de données massives (555k transactions) dans une base de données **PostgreSQL**.
2.  Exécutant un **DAG** (`daily_fraud_report_pipeline`) qui interroge la base pour les transactions frauduleuses détectées la veille.
3.  Générant un rapport et en l'envoyant par e-mail.

### Technologies Clés

* **Orchestration :** Apache Airflow
* **Conteneurisation :** Docker & Docker Compose
* **Base de Données :** PostgreSQL
* **Data Pipelining :** Python, Pandas

---

## 📦 Architecture et Services

L'environnement est entièrement conteneurisé. Les services sont lancés via `docker-compose.yml`.

| Service Docker | Rôle | Port d'Accès |
| :--- | :--- | :--- |
| `airflow-webserver` | Interface Utilisateur d'Airflow (UI) | `http://localhost:8081` |
| `airflow-scheduler` | Planifie et monitore les DAGs | N/A |
| `airflow-airflow-worker-1` | Exécute les tâches distribuées | N/A |
| `airflow-postgres-1` | Base de données pour Airflow (metadata) et les données métier | 5432 (interne) |
| `airflow-redis-1` | Broker de messages pour Airflow (Celery Executor) | N/A |

---

## 🛠 Prérequis

* **Docker Desktop** (installé et en cours d'exécution).
* **Cloner** ce dépôt Git.

---

## 📌 1. Démarrage de l'Environnement

### 1.1 Lancer les conteneurs

Dans le répertoire racine du projet (contenant le `docker-compose.yml`), exécutez les commandes suivantes :

```bash
# 1. Initialiser la base de données Airflow
docker-compose up airflow-init

# 2. Démarrer l'ensemble des services en arrière-plan
docker-compose up -d --force-recreate
---
Le flag `--force-recreate` garantit un redémarrage propre des services Airflow.

### 1.2 Accès à Airflow

Ouvrez votre navigateur et accédez à : **`http://localhost:8081`**
Identifiants par défaut : `airflow` / `airflow` (si configuré).

---

## 📌 2. Initialisation des Données

Vous devez exécuter le script `insert_data-db.py` pour remplir la base de données métier. Ce script utilise le chargement par lots et date les données à la veille pour permettre un test immédiat du DAG.

1.  **Copiez les fichiers** dans le conteneur worker :
    ```bash
    docker cp fraudTest.csv airflow-airflow-worker-1:/opt/airflow/data/
    docker cp insert_data-db.py airflow-airflow-worker-1:/opt/airflow/data/
    ```

2.  **Exécutez le script** d'initialisation dans le conteneur :
    ```bash
    docker exec -it airflow-airflow-worker-1 /bin/bash
    
    # Dans le conteneur :
    cd /opt/airflow/data
    export PROD_DB_URI="postgresql://airflow:airflow@airflow-postgres-1:5432/airflow" 
    python insert_data-db.py
    exit # Quitter le conteneur
    ```
    Confirmez le message de succès : ✅ Toutes les données ont été chargées (555719 lignes) et les tables initialisées avec succès.

---

## 📌 3. Configuration des Connexions Airflow

### 3.1 Connexion PostgreSQL (Base Métier)

Créez cette connexion dans l'Airflow UI (**Admin** > **Connections**) :

* **Conn Id :** `NEON_DB`
* **Conn Type :** `Postgres`
* **Host :** `airflow-postgres-1` (Nom du service Docker)
* **Schema :** `airflow`
* **Login :** `airflow`
* **Password :** `airflow`
* **Port :** `5432`

### 3.2 Variables d'Environnement (E-mail)

Créez ces variables dans l'Airflow UI (**Admin** > **Variables**) pour la tâche d'envoi d'e-mail :

| Clé (Key) | Description |
| :--- | :--- |
| `SENDER_EMAIL` | Votre adresse Gmail utilisée pour l'envoi. |
| `APP_PASSWORD` | Le Mot de Passe d'Application généré par Google. |
| `RECEIVER_EMAIL` | L'adresse de destination du rapport. |

---

## 📌 4. Déclenchement du DAG

Une fois la configuration terminée, allez à l'Airflow UI :

1.  Trouvez le DAG **`daily_fraud_report_pipeline`**.
2.  Activez-le.
3.  Déclenchez une exécution manuelle.

### Flux du Pipeline

| Tâche (Task ID) | Rôle |
| :--- | :--- |
| `create_daily_fraud_report` | Se connecte à la BDD via `NEON_DB`, interroge la table `fraud_predictions` pour la veille, génère le rapport et le pousse vers XCom. |
| `send_daily_report_email` | Récupère le rapport via XCom et envoie l'e-mail à l'adresse spécifiée dans les Variables Airflow. |

---

## 📌 5. Arrêt de l'Environnement

Pour arrêter proprement et conserver vos volumes de données persistants :

```bash
docker-compose down