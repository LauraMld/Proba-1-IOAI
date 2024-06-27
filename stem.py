# -*- coding: utf-8 -*-
"""Stem.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1WvPMWgG6eGjK8Ck9_ndfIMbrzey4cNIP
"""

from google.colab import files
files.upload()

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Încărcarea datelor
df = pd.read_csv('games.csv')

# Preprocesarea datelor
df = df.dropna(subset=['Price'])

# Transformăm 'Release date' în anul lansării
df['release_year'] = pd.to_datetime(df['Release date'], errors='coerce').dt.year

# Selectăm caracteristicile relevante
features = df[['Estimated owners', 'Peak CCU', 'Required age', 'DLC count', 'Metacritic score', 'User score',
               'Positive', 'Negative', 'Achievements', 'Recommendations', 'Average playtime forever',
               'Median playtime forever', 'Developers', 'Publishers', 'Categories', 'Genres', 'release_year']]
target = df['Price']

# Tratarea valorilor lipsă
combined = pd.concat([features, target], axis=1)
combined = combined.dropna()
features = combined.drop(columns='Price')
target = combined['Price']

# Codificarea caracteristicilor categorice
categorical_features = ['Developers', 'Publishers', 'Categories', 'Genres']
numeric_features = ['release_year', 'Peak CCU', 'Required age', 'DLC count', 'Metacritic score', 'User score',
                    'Positive', 'Negative', 'Achievements', 'Recommendations', 'Average playtime forever',
                    'Median playtime forever']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])

# Împărțirea datelor în seturi de antrenament și testare
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

# Crearea pipeline-ului de preprocesare și modelare
model = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', RandomForestRegressor(random_state=42))
])

# Ajustarea hiperparametrilor folosind GridSearchCV
param_grid = {
    'regressor__n_estimators': [50, 100, 200],
    'regressor__max_depth': [None, 10, 20, 30],
    'regressor__min_samples_split': [2, 5, 10]
}

grid_search = GridSearchCV(model, param_grid, cv=5, scoring='neg_mean_squared_error')
grid_search.fit(X_train, y_train)

# Selectarea celui mai bun model
best_model = grid_search.best_estimator_

# Evaluarea modelului folosind validare încrucișată
scores = cross_val_score(best_model, X_train, y_train, cv=5, scoring='r2')
print(f'Cross-validated R^2 scores: {scores}')
print(f'Average R^2 score: {np.mean(scores)}')

# Prezicerea pe setul de testare
y_pred = best_model.predict(X_test)

# Evaluarea modelului pe setul de testare
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f'Mean Squared Error: {mse}')
print(f'R^2 Score: {r2}')

# Salvează modelul antrenat pentru utilizare ulterioară (opțional)
import joblib
joblib.dump(best_model, 'steam_price_predictor.pkl')