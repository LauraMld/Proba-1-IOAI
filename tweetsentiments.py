# -*- coding: utf-8 -*-
"""TweetSentiments.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ipIx9F-Osa7JnVsTWD1Moqo0KHgZP7NN
"""

from google.colab import files
files.upload()

import os
!mkdir -p ~/.kaggle
!cp kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json

!kaggle competitions download -c tweet-sentiment-extraction
!unzip tweet-sentiment-extraction.zip -d tweet

import pandas as pd
import re
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
import torch

train_df = pd.read_csv('tweet/train.csv')
test_df = pd.read_csv('tweet/test.csv')

# Verifică valorile lipsă în setul de date
print(train_df['text'].isnull().sum())
print(test_df['text'].isnull().sum())

# Înlocuiește valorile lipsă cu un string gol
train_df['text'].fillna('', inplace=True)
test_df['text'].fillna('', inplace=True)

# Conversia etichetelor în int
train_df['sentiment'] = train_df['sentiment'].astype(int)
test_df['sentiment'] = test_df['sentiment'].astype(int)

# Funcții pentru curățarea textului
def basic_cleaning(text):
    text = re.sub(r'https?://www\.\S+\.com', '', text)
    text = re.sub(r'[^A-Za-z\s]', '', text)
    text = re.sub(r'\*+', 'swear', text)  # Capturarea cuvintelor cenzurate cu ****
    return text

def remove_html(text):
    html = re.compile(r'<.*?>')
    return html.sub(r'', text)

def remove_emoji(text):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def remove_multiplechars(text):
    text = re.sub(r'(.)\1{3,}', r'\1', text)
    return text

def preprocess_text(text):
    text = text.lower()
    text = basic_cleaning(text)
    text = remove_html(text)
    text = remove_emoji(text)
    text = remove_multiplechars(text)
    return text

train_df['text'] = train_df['text'].astype(str).apply(preprocess_text)
test_df['text'] = test_df['text'].astype(str).apply(preprocess_text)

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

def tokenize_function(examples):
    return tokenizer(examples['text'], padding="max_length", truncation=True)

train_texts = train_df['text'].tolist()
train_labels = train_df['sentiment'].tolist()

test_texts = test_df['text'].tolist()
test_labels = [0] * len(test_texts)  # Placeholder pentru setul de testare fără etichete

train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=128)
test_encodings = tokenizer(test_texts, truncation=True, padding=True, max_length=128)

class TweetDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

train_dataset = TweetDataset(train_encodings, train_labels)
test_dataset = TweetDataset(test_encodings, test_labels)

!pip uninstall accelerate transformers
!pip install accelerate transformers[torch]
!pip install accelerate>=0.21.0
!pip install transformers[torch]>=4.30.0

from transformers import BertForSequenceClassification, Trainer, TrainingArguments

# Model
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=3)

# Argumentele de antrenament
training_args = TrainingArguments(
    output_dir='./results',
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
)

# Antrenare
trainer.train()