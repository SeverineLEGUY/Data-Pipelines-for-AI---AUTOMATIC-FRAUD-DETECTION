import pandas as pd
import requests
import time
import os
import mlflow.pyfunc
from sqlalchemy import create_engine
from datetime import datetime
import logging
import json

logging.basicConfig(level=logging.INFO)

# Configuration des services
DB_URI = os.environ.get("PROD_DB_URI")
API_URL = "https://charlestng-real-time-fraud-detection.hf.space/current-transactions"

# Nom du modèle dans le registre MLflow
MODEL_NAME = "XGBoost_Fraud_Model_Prod"
MODEL_STAGE = "Production" 

# Configuration des notifications
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD") # Mot de passe d'application pour les services de messagerie (ex: Gmail)
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def send_email(subject: str, body: str):
    """
    Envoie un email via SMTP Gmail
    """
    # Ce bloc de code doit être indenté sous la fonction send_email
    if not SENDER_EMAIL or not APP_PASSWORD or not RECEIVER_EMAIL:
        logging.error("Les variables d'environnement pour l'envoi d'e-mail ne sont pas configurées. Notification non envoyée.")
        return

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        logging.info("✅ Email envoyé avec succès.")
    except Exception as e:
        logging.error(f"❌ Erreur lors de l'envoi de l'e-mail : {e}")


def load_model():
    """Charge la dernière version du modèle depuis le registre MLflow."""
    try:
        client = mlflow.tracking.MlflowClient()
        latest_version = client.get_latest_versions(MODEL_NAME, stages=[MODEL_STAGE])
        if not latest_version:
            logging.error("Aucune version du modèle en production n'a été trouvée dans le registre MLflow.")
            return None
        model_uri = latest_version[0].source
        logging.info(f"Modèle chargé depuis : {model_uri}")
        return mlflow.pyfunc.load_model(model_uri)
    except Exception as e:
        logging.error(f"Erreur lors du chargement du modèle depuis MLflow : {e}")
        return None

def get_latest_transactions(api_url):
    """Étape 1 : Récupère les données brutes de l'API sous forme de chaîne de caractères."""
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        logging.info("Connexion à l'API de paiement")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur lors de la connexion à l'API de paiement : {e}")
        return None

def preprocess_data(df):
    """
    Prétraite les données pour le modèle en créant les colonnes manquantes et en ajustant le schéma.
    """
    
    # Créer les colonnes 'hour' et 'dayofweek'
    df['current_time'] = pd.to_datetime(df['current_time'])
    df['hour'] = df['current_time'].dt.hour
    df['dayofweek'] = df['current_time'].dt.dayofweek
    
    # Créer la colonne 'gender' (si elle n'existe pas)
    if 'gender' not in df.columns:
        df['gender'] = 0
    df['gender'] = df['gender'].map({'F': 0, 'M': 1}).fillna(-1).astype(int)
    # Encodage de la colonne 'category' en valeurs numériques (au lieu de one-hot encoding)
    df['category'] = df['category'].astype('category').cat.codes

    # Encodage de la colonne 'merchant'
    df['merchant_encoded'] = df['merchant'].astype('category').cat.codes
    
    # Sélectionner uniquement les colonnes requises par le modèle
    required_columns = ['category', 'amt', 'gender', 'city_pop', 'merchant_encoded', 'hour', 'dayofweek']
    df_processed = df[required_columns].copy()
    
    return df_processed

def main_loop():
    """Boucle principale de la détection de fraude en temps réel."""
    try:
        engine = create_engine(DB_URI)
        logging.info("Connexion à la base de données établie.")
    except Exception as e:
        logging.error(f"Erreur de connexion à la base de données : {e}")
        return

    model = load_model()
    if not model:
        logging.error("Le service ne peut pas démarrer sans modèle ML.")
        return

    while True:
        try:
            transactions_data = get_latest_transactions(API_URL)
            logging.info("1.Récupérer les données brutes de l'API")
            if not transactions_data:
                time.sleep(60)
                continue
            
            # Étape 2 : Décoder la chaîne JSON en un dictionnaire Python 
           
            transactions_data = json.loads(transactions_data)
            
            
            # Étape 3 : Accéder manuellement aux clés du dictionnaire pour créer le DataFrame 
            df = pd.DataFrame(transactions_data['data'], columns=transactions_data['columns'], index=transactions_data['index'])
            
            logging.info("DataFrame créé avec succès.")

        except Exception as e:
            logging.error(f"Erreur lors de la reconstruction du DataFrame: {e}")
            time.sleep(60)
            continue
        
        try:
            df_processed = preprocess_data(df)
            predictions = model.predict(df_processed)
            df['is_fraud_predicted'] = predictions
            df['detection_timestamp'] = datetime.now()

            frauds_to_save = df[df['is_fraud_predicted'] == 1].copy()
            frauds_to_save['detection_timestamp'] = datetime.now()

            if not frauds_to_save.empty:
                logging.info(f"Fraudes détectées : {len(frauds_to_save)}. Sauvegarde dans la base de données...")
                frauds_to_save.to_sql('fraud_predictions', engine, if_exists='append', index=False)
                logging.info("✅ Données sauvegardées avec succès.")
                send_fraud_notification(frauds_to_save) # Appel de la fonction de notification
            else:
                logging.info("✅ Aucune fraude détectée cette fois-ci.")

            # Sauvegarde de TOUTES les transactions
            logging.info("Sauvegarde de toutes les transactions dans la base de données...")
            df.to_sql('all_transactions', engine, if_exists='append', index=False)
            logging.info("✅ Toutes les transactions ont été sauvegardées avec succès.")

        except Exception as e:
            logging.error(f"❌ Erreur lors de la prédiction ou de la sauvegarde des données : {e}")

        logging.info("Pause de 60 secondes avant la prochaine requête...")
        time.sleep(60)

if __name__ == "__main__":
    main_loop()







