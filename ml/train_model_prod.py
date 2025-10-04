import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import xgboost as xgb

import os
from sqlalchemy import create_engine
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
import joblib

#import airflow

#from airflow.providers.postgres.hooks.postgres import PostgresHook # Importation nécessaire

def get_data_from_db(conn_id="postgres_default"):
    """
    Récupère le jeu de données depuis la base de données.
    Note : Cette fonction est un placeholder. Pour ce projet,
    nous utilisons un fichier CSV pour simuler la base de données.
    """
    url = "https://lead-program-assets.s3.eu-west-3.amazonaws.com/M05-Projects/fraudTest.csv"
    df = pd.read_csv(url)
    return df


def preprocess_data(df):
    """Prétraite les données pour le modèle en créant les colonnes manquantes et en ajustant le schéma."""
    
    # Créer les colonnes 'hour' et 'dayofweek'
    df['current_time'] = pd.to_datetime(df['current_time'])
    df['hour'] = df['current_time'].dt.hour
    df['dayofweek'] = df['current_time'].dt.dayofweek
    
    # Encoder la colonne 'gender' en valeurs numériques (0 ou 1)
    df['gender'] = df['gender'].map({'F': 0, 'M': 1})
    
    # Encodage de la colonne 'category' en valeurs numériques
    df['category'] = df['category'].astype('category').cat.codes

    # Encodage de la colonne 'merchant'
    df['merchant_encoded'] = df['merchant'].astype('category').cat.codes
    
    # Sélectionner uniquement les colonnes requises par le modèle
    required_columns = ['category', 'amt', 'gender', 'city_pop', 'merchant_encoded', 'hour', 'dayofweek']
    df_processed = df[required_columns].copy()
    
    return df_processed



def train_and_log_model(**kwargs):
    """
    Fonction principale pour l'entraînement du modèle et le log dans MLflow.
    """
    print("✅ Récupération et pré-traitement des données...")
    df = get_data_from_db()
    df_model = preprocess_data(df)
    
    X = df_model.drop(columns=["is_fraud"])
    y = df_model["is_fraud"]
    X = df_model.drop(columns=["is_fraud"])
    y = df_model["is_fraud"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    # Paramètres pour GridSearch
    param_grid = {
        "n_estimators": [50, 100],
        "max_depth": [3, 5, 7],
        "learning_rate": [0.01, 0.1, 0.2],
        "scale_pos_weight": [1, 10],
    }

    xgb_model = xgb.XGBClassifier(eval_metric="logloss", random_state=42)

    grid_search = GridSearchCV(
        estimator=xgb_model,
        param_grid=param_grid,
        cv=3,
        scoring="f1",
        verbose=1,
        n_jobs=-1
    )
     # La variable d'environnement MLFLOW_TRACKING_URI est configurée dans docker-compose.yaml
    # pour pointer vers votre base de données NeonDB
    print("✅ Lancement de la session MLflow...")
    mlflow.set_experiment("Fraud Detection Training")

    with mlflow.start_run(run_name="XGBoost_Fraud_GridSearch"):
        grid_search.fit(X_train, y_train)

        best_params = grid_search.best_params_
        y_pred = grid_search.predict(X_test)

        mlflow.log_params(best_params)

        report = classification_report(y_test, y_pred, output_dict=True)
        mlflow.log_metric("f1_train_cv", grid_search.best_score_)
        mlflow.log_metric("precision", report["1"]["precision"])
        mlflow.log_metric("recall", report["1"]["recall"])
        mlflow.log_metric("f1_test", report["1"]["f1-score"])

        signature = infer_signature(X_train, grid_search.best_estimator_.predict(X_train))
        mlflow.sklearn.log_model(
            sk_model=grid_search.best_estimator_,
            artifact_path="model",
            signature=signature,
            input_example=X_train.iloc[[0]],
            registered_model_name="XGBoost_Fraud_Model_Prod"
        )
        
        # Sauvegarde et log de la matrice de confusion
        cm = confusion_matrix(y_test, y_pred)
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Non fraude", "Fraude"])
        disp.plot(cmap=plt.cm.Blues)
        plt.title("Matrice de confusion - XGBoost (Test set)")
        fig_path = "confusion_matrix.png"
        plt.savefig(fig_path, bbox_inches="tight")
        mlflow.log_artifact(fig_path)
        os.remove(fig_path) # Nettoyage du fichier local
    
    print("✅ Run MLflow terminé avec succès !")

    # Enregistrement du modèle en tant que joblib.
    # Note: MLflow gère déjà l'enregistrement, mais cela peut être utile pour d'autres usages.
    os.makedirs("models", exist_ok=True)
    local_model_path = "models/xgboost_fraud_model.pkl"
    joblib.dump(grid_search.best_estimator_, local_model_path)
    print("✅ Sauvegarde MLflow terminé avec succès !")

if __name__ == "__main__":
    train_and_log_model()


