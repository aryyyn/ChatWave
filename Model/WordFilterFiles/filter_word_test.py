import joblib
model = joblib.load('Model/WordFilterFiles/text_classifier_model.pkl')
vectorizer = joblib.load('Model\WordFilterFiles/vectorizer.pkl')


def predict_text(text, model, vectorizer):
 
    vectorized_input = vectorizer.transform([text])
    
    prediction = model.predict(vectorized_input)
    
    return prediction[0]

a = predict_text("test", model, vectorizer)
print(a)
