
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import re
import pandas as pd
from nltk.stem import WordNetLemmatizer
import keras
from keras.preprocessing.sequence import pad_sequences
from django.contrib import messages
import os
from tensorflow.keras.preprocessing.text import Tokenizer
import tensorflow as tf
import numpy as np
import json
from cryptography.fernet import Fernet


def modelTest(message):
    try:

        new_model = tf.keras.models.load_model("sentimentmodel.h5")

        try:
            with open("tokenizer.json", "r") as json_file:
                tokenizer_config = json_file.read()
                tokenizer1 = tf.keras.preprocessing.text.tokenizer_from_json(
                    tokenizer_config
                )
        except FileNotFoundError:
            raise Exception("Tokenizer file not found at 'tokenizer.json'")
        except json.JSONDecodeError:
            raise Exception("Invalid JSON format in tokenizer file")

        for resource in ["stopwords", "wordnet"]:
            try:
                nltk.download(resource, quiet=True)
            except Exception as e:
                print(f"Warning: Failed to download NLTK resource {resource}: {e}")

        stop_words = set(stopwords.words("english"))
        stemmer = SnowballStemmer("english")
        lemmatizer = WordNetLemmatizer()

        def textcleaning(text, stem=False):
            text = re.sub(
                "@\S+|https?:\S+|http?:\S|[^A-Za-z0-9]+", " ", str(text).lower()
            ).strip()

            tokens = []
            for token in text.split():
                if token not in stop_words:
                    if stem:
                        token = stemmer.stem(token)
                    if lemmatizer:
                        token = lemmatizer.lemmatize(token)
                    tokens.append(token)

            return " ".join(tokens)

        def get_sentiment(prediction):
            if 0.45 <= prediction[0] <= 0.55:
                return "calm"
            return "happy" if prediction[0] < 0.45 else "sad"

        finalResult = []
        try:
            cleaned_text = textcleaning(title)

            sequences = tokenizer1.texts_to_sequences([cleaned_text])
            padded_sequences = pad_sequences(sequences, padding="post", maxlen=50)

            predictions = new_model.predict(padded_sequences, verbose=0)
            print(predictions)
            sentiment = get_sentiment(predictions[0])

            finalResult.append(sentiment)

        except Exception as e:
            print(f"Error processing message: {e}")
            finalResult.append("error")

        return finalResult

    except Exception as e:
        print(f"Critical error in modelTest: {e}")
        return None
    

print(modelTest("Nice goal my messi. what a header!!!"))