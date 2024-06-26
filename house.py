# -*- coding: utf-8 -*-
"""House.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/16C6WK81_zRtzADJrb3BixJ1yUZUhMpx_
"""

from google.colab import files
files.upload()

import os
!mkdir -p ~/.kaggle
!cp kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json

!kaggle competitions download -c house-prices-advanced-regression-techniques
!unzip house-prices-advanced-regression-techniques.zip -d house

!pip install catboost

#0.12787

import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import KNNImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import GradientBoostingRegressor, StackingRegressor
from sklearn.model_selection import train_test_split
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_squared_error
import xgboost as xgb
import lightgbm as lgb
import optuna

# Încărcăm datele
train = pd.read_csv('house/train.csv')
test = pd.read_csv('house/test.csv')

# Păstrăm valorile originale ale coloanei 'Id'
test_ids = test['Id']

# Separăm caracteristicile și ținta
X = train.drop(['Id', 'SalePrice'], axis=1)
y = train['SalePrice']

# Identificăm coloanele numerice și categorice
numeric_features = X.select_dtypes(include=['float64', 'int64']).columns
categorical_features = X.select_dtypes(include=['object']).columns

# Transformare logaritmică pentru variabila țintă
y = np.log1p(y)

# Preprocesarea pentru datele numerice
numeric_transformer = Pipeline(steps=[
    ('imputer', KNNImputer(n_neighbors=5)),
    ('scaler', StandardScaler())])

# Preprocesarea pentru datele categorice
categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))])

# Combinăm preprocesările
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)])

# Funcția de optimizare a hiperparametrilor
def objective(trial):
    param = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0)
    }
    xgb_model = xgb.XGBRegressor(**param)

    stacking_model = StackingRegressor(
        estimators=[
            ('xgb', xgb_model),
            ('lgb', lgb.LGBMRegressor(n_estimators=1000, learning_rate=0.05))
        ],
        final_estimator=RidgeCV(),
        cv=5
    )

    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', stacking_model)
    ])

    model.fit(X_train, y_train)
    preds = model.predict(X_valid)
    rmse = np.sqrt(mean_squared_error(y_valid, preds))
    return rmse

# Împărțim setul de date pentru validare
X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=0.2, random_state=42)

# Optimizăm hiperparametrii
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=50)

# Antrenăm modelul cu cei mai buni hiperparametri
best_params = study.best_params
xgb_model = xgb.XGBRegressor(**best_params)

stacking_model = StackingRegressor(
    estimators=[
        ('xgb', xgb_model),
        ('lgb', lgb.LGBMRegressor(n_estimators=1000, learning_rate=0.05))
    ],
    final_estimator=RidgeCV(),
    cv=5
)

model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', stacking_model)
])

model.fit(X_train, y_train)

# Evaluăm performanța pe setul de validare
valid_predictions = model.predict(X_valid)
valid_rmse = np.sqrt(mean_squared_error(y_valid, valid_predictions))
print(f'RMSE pe setul de validare: {valid_rmse}')

# Preprocesăm și prezicem pe setul de test
test = test.drop(['Id'], axis=1)
test_predictions = np.expm1(model.predict(test))

# Creăm fișierul de submitere
submission = pd.DataFrame({'Id': test_ids, 'SalePrice': test_predictions})
submission.to_csv('submission.csv', index=False)

files.download('submission.csv')

##### Nu sunt folosite in cod, doar pentru a observa diferite caracteristici

# Pair plot pentru câteva caracteristici
sns.pairplot(train[['SalePrice', 'OverallQual', 'GrLivArea', 'GarageCars', 'TotalBsmtSF']])
plt.show()

# Matricea de corelație
plt.figure(figsize=(12, 10))
correlation_matrix = train.corr()
sns.heatmap(correlation_matrix, annot=True, cmap=plt.cm.Reds)
plt.title('Matricea de corelație')
plt.show()

from sklearn.feature_selection import SelectKBest, f_regression

# Selectarea caracteristicilor
X = train.drop('SalePrice', axis=1)
y = train['SalePrice']

selector = SelectKBest(score_func=f_regression, k=20)
X_new = selector.fit_transform(X, y)
selected_features = X.columns[selector.get_support()]

print(selected_features)