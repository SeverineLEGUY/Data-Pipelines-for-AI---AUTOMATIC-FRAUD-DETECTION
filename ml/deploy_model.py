import mlflow
from mlflow.tracking import MlflowClient

# The URI is configured in your docker-compose.yaml
MLFLOW_TRACKING_URI = "http://mlflow-server:5000"
MODEL_NAME = "XGBoost_Fraud_Model_Prod"
# Note: MLflow a déprécié les "stages".
# Les nouveaux projets devraient utiliser des alias.
# Pour ce projet, nous allons continuer à utiliser le stage "Production"
# pour que le service de prédiction fonctionne.
MODEL_STAGE = "Production"

def deploy_model():
    """
    Passe la dernière version du modèle dans le stage "Production".
    """
    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)

    # Récupère la dernière version du modèle
    try:
        versions = client.get_latest_versions(MODEL_NAME)
        if not versions:
            print(f"Erreur : Aucune version trouvée pour le modèle '{MODEL_NAME}'. Avez-vous exécuté le script d'entraînement ?")
            return
        latest_version = versions[0].version
        print(f"✅ Dernière version trouvée pour le modèle '{MODEL_NAME}': version '{latest_version}'.")
    except Exception as e:
        print(f"Erreur lors de la récupération de la dernière version du modèle : {e}")
        return

    # Passe la version du modèle au stage "Production"
    print(f"⏳ Tentative de passage de la version '{latest_version}' au stage '{MODEL_STAGE}'...")
    try:
        client.transition_model_version_stage(
            name=MODEL_NAME,
            version=latest_version,
            stage=MODEL_STAGE,
        )
        print(f"✅ Modèle '{MODEL_NAME}' version '{latest_version}' est maintenant dans le stage '{MODEL_STAGE}' avec succès.")
    except Exception as e:
        print(f"Erreur lors du changement de stage du modèle : {e}")

if __name__ == "__main__":
    deploy_model()