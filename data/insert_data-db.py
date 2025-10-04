import pandas as pd
from sqlalchemy import create_engine
import os
import logging
from datetime import datetime,timedelta


logging.basicConfig(level=logging.INFO)

def initiate_database_tables():
    """
    Lit le fichier fraudTest.csv par lots (chunks), insère toutes les transactions 
    dans 'all_transactions' et filtre les fraudes pour 'fraud_predictions'.
    """
    try:
        db_uri = os.environ.get("PROD_DB_URI") 
        if not db_uri:
            logging.error("La variable d'environnement PROD_DB_URI n'est pas définie.")
            return
        
        engine = create_engine(db_uri)
        logging.info("✅ Connexion à la base de données établie.")

        file_path = "fraudTest.csv"
        
        # --- MODIFICATION CRUCIALE : Lecture par lots ---
        CHUNK_SIZE = 50000  # Taille du lot. Ajustez si "Killed" réapparaît.
        first_chunk = True
        total_rows = 0

        logging.info("⏳ Démarrage du chargement et de la sauvegarde des données par lots...")

        # Utilisation de chunksize pour lire le fichier itérativement
        for chunk in pd.read_csv(file_path, chunksize=CHUNK_SIZE):
            
            # Prétraitement
            yesterday_date = (datetime.now() - timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
            chunk['detection_timestamp'] = yesterday_date
            # chunk['detection_timestamp'] = datetime.now()
            total_rows += len(chunk)

            # Le mode 'replace' est utilisé uniquement pour le premier lot
            # Tous les lots suivants utilisent 'append'
            if_exists_mode = 'replace' if first_chunk else 'append'
            
            logging.info(f"⏳ Sauvegarde du lot de {len(chunk)} transactions. Mode: {if_exists_mode}...")
            
            # Étape 1 : Sauvegarde de TOUTES les transactions
            chunk.to_sql('all_transactions', engine, if_exists=if_exists_mode, index=False)
            
            # Étape 2 : Filtrage et sauvegarde des transactions frauduleuses
            frauds_to_save = chunk[chunk['is_fraud'] == 1].copy()
            frauds_to_save.rename(columns={'is_fraud': 'is_fraud_predicted'}, inplace=True)
            frauds_to_save.to_sql('fraud_predictions', engine, if_exists=if_exists_mode, index=False)
            
            first_chunk = False 

        logging.info(f"✅ Toutes les données ont été chargées ({total_rows} lignes) et les tables initialisées avec succès.")

    except Exception as e:
        logging.error(f"❌ Erreur lors du chargement des données : {e}")

if __name__ == "__main__":
    initiate_database_tables()