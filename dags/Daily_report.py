from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.models import Variable
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib
import pandas as pd
from datetime import datetime, timedelta

# Configuration de la connexion à la base de données Neon
NEON_CONN_ID = "NEON_DB"

def send_email(subject: str, body: str):
    """
    Envoie un email via SMTP Gmail
    """
    # Récupérer les variables d'Airflow ici, au moment de l'exécution de la fonction
    sender_email = Variable.get("SENDER_EMAIL")
    app_password = Variable.get("APP_PASSWORD")
    receiver_email = Variable.get("RECEIVER_EMAIL")

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        logging.info("Email envoyé avec succès.")
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi : {e}")
    finally:
        server.quit()

def create_daily_fraud_report():
    """
    Récupère les fraudes détectées la veille et génère un rapport.
    """
    logging.info("⏳ Génération du rapport de fraude quotidien...")
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    hook = PostgresHook(postgres_conn_id=NEON_CONN_ID)

    
    sql_query = f"SELECT * FROM fraud_predictions WHERE DATE(detection_timestamp) = '{yesterday}'"
    df = hook.get_pandas_df(sql_query)
    if df is not None and not df.empty:
        logging.info(f"Colonnes disponibles : {df.columns.tolist()}")
        logging.info(f"Aperçu des données :\n{df.head()}")
    else:
        logging.info("✅ Aucune donnée renvoyée par la requête.")

    if df.empty:
        report_body = "Aucune fraude n'a été détectée le jour précédent."
    else:
        report_body = f"📊 Rapport de fraude pour le {yesterday}:\n\n"
        report_body += f"Nombre de fraudes détectées : {len(df)}\n\n"
        report_body += "Détails des transactions :\n"
        report_body += df[['detection_timestamp', 'amt', 'category']].to_string()
    
    return report_body

def send_daily_report_email(ti):
    """
    Envoie le rapport de fraude quotidien par e-mail.
    """
    subject = "Rapport quotidien de détection de fraude"
    body = ti.xcom_pull(task_ids='create_daily_fraud_report')
    
    # Appel à la fonction send_email corrigée
    send_email(subject=subject, body=body)
    
# Définition des arguments par défaut du DAG
default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
    'retries': 1,
}

# Définition du DAG
with DAG(
    'daily_fraud_report_pipeline',
    default_args=default_args,
    description='Pipeline quotidien pour générer et envoyer le rapport de fraude',
    schedule_interval='@daily',
    catchup=False
) as dag:
    # Tâche 1 : Générer le rapport en se connectant à la BDD
    create_report_task = PythonOperator(
        task_id='create_daily_fraud_report',
        python_callable=create_daily_fraud_report
    )

    # Tâche 2 : Envoyer le rapport par e-mail
    send_report_email_task = PythonOperator(
        task_id='send_daily_report_email',
        python_callable=send_daily_report_email
    )

    # Définition de l'ordre d'exécution des tâches
    create_report_task >> send_report_email_task