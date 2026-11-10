import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
from dataset import DATASET

def train():
    texts = [x[0] for x in DATASET]
    labels = [x[1] for x in DATASET]

    # Requirement 1: TF-IDF character n-grams (char_wb, 2-5) + Logistic Regression
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 5), min_df=1)),
        ('clf', LogisticRegression(C=5.0, max_iter=1000, random_state=42))
    ])

    scores = cross_val_score(pipeline, texts, labels, cv=3)
    print(f"Cross-Validation Accuracy (3-fold): {scores.mean()*100:.2f}% (+/- {scores.std()*100:.2f}%)")

    pipeline.fit(texts, labels)
    joblib.dump(pipeline, 'model.joblib')
    print("Trained model successfully saved to model.joblib")

if __name__ == '__main__':
    train()
