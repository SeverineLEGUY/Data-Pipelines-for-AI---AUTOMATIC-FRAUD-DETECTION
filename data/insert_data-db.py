import pandas as pd
from sqlalchemy import create_engine
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

def initiate_database_tables():
    """
    Lit le fichier fraudTest.csv, insère toutes les transactions dans 'all_transactions'
    et filtre les transactions frauduleuses pour les insérer dans 'fraud_predictions'.
    """
    try:
        # Configuration de la base de données depuis les variables d'environnement
        # Remplacez cette ligne par la variable d'environnement réelle de votre docker-compose.yml
        db_uri = os.environ.get("PROD_DB_URI") 
        if not db_uri:
            logging.error("La variable d'environnement PROD_DB_URI n'est pas définie.")
            return
        
        engine = create_engine(db_uri)
        logging.info("✅ Connexion à la base de données établie.")

        file_path = "fraudTest.csv"
        
        # Lecture du fichier CSV
        df = pd.read_csv(file_path)
        logging.info(f"✅ Fichier de données de test chargé, {len(df)} transactions trouvées.")
        
        # Ajout d'une colonne de timestamp pour être cohérent avec le service en temps réel
        df['detection_timestamp'] = datetime.now()

        # Étape 1 : Sauvegarde de TOUTES les transactions dans la nouvelle table
        logging.info("⏳ Sauvegarde de toutes les transactions dans la table 'all_transactions'...")
        df.to_sql('all_transactions', engine, if_exists='replace', index=False)
        logging.info("✅ Toutes les transactions ont été sauvegardées avec succès.")
        
        # Étape 2 : Filtrage des transactions frauduleuses pour la table 'fraud_predictions'
        frauds_to_save = df[df['is_fraud'] == 1].copy()
        
        # Renommage de la colonne pour être cohérent avec le service de prédiction
        frauds_to_save.rename(columns={'is_fraud': 'is_fraud_predicted'}, inplace=True)
        
        logging.info(f"✅ {len(frauds_to_save)} transactions frauduleuses identifiées.")
        
        # Sauvegarde dans la base de données, en utilisant le nouveau nom de table et le mode 'replace' pour l'initialisation
        frauds_to_save.to_sql('fraud_predictions', engine, if_exists='replace', index=False)
        logging.info("✅ Les transactions frauduleuses ont été sauvegardées avec succès.")

    except Exception as e:
        logging.error(f"❌ Erreur lors du chargement des données : {e}")

if __name__ == "__main__":
    initiate_database_tables()