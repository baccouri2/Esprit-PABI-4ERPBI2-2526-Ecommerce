"""
NLP Sentiment Analysis — Analyze customer feedback and claims
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from flask import Blueprint, jsonify, request
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import re

from db import query_df

sentiment_bp = Blueprint('sentiment', __name__)

# ── helpers ──────────────────────────────────────────────────────────────────

def _load_claims():
    """Load real customer claims (negative feedback)"""
    sql = "SELECT description, status FROM dim_claim WHERE description IS NOT NULL"
    try:
        df = query_df(sql)
        claims = df['description'].dropna().astype(str).tolist()
        claims = [re.sub(r'\s+', ' ', t).strip() for t in claims if len(t.strip()) > 10]
        return claims
    except Exception:
        return []


def _generate_positive_reviews():
    """Generate synthetic positive reviews from product names"""
    sql = "SELECT TOP 50 name_product FROM dim_product"
    try:
        df = query_df(sql)
        products = df['name_product'].dropna().tolist()
        
        positive_templates = [
            "Excellent product! Very satisfied with {}",
            "Great quality, highly recommend {}",
            "Amazing {}, exceeded expectations",
            "Perfect {}, will buy again",
            "Love this {}, fantastic value",
            "Outstanding {}, very happy",
            "{} is wonderful, great purchase",
            "Superb {}, exactly what I needed",
            "Brilliant {}, top quality",
            "Fantastic {}, very pleased",
            "Best {} I've ever bought",
            "Incredible {}, worth every penny",
            "Awesome {}, five stars",
            "Delighted with {}, perfect choice",
            "Impressive {}, highly satisfied"
        ]
        
        # Generate more positive reviews
        positive_reviews = []
        for prod in products:
            for _ in range(2):  # 2 reviews per product
                template = np.random.choice(positive_templates)
                positive_reviews.append(template.format(prod))
        
        # Add generic positive reviews
        generic_positive = [
            "Great product, very satisfied with my purchase",
            "Excellent quality, highly recommend to everyone",
            "Amazing service, will definitely buy again",
            "Perfect purchase, exceeded all my expectations",
            "Love it, fantastic value for money",
            "Outstanding quality, very happy customer",
            "Wonderful experience, great product",
            "Superb quality, exactly what I needed",
            "Brilliant purchase, top quality product",
            "Fantastic service, very pleased with everything",
            "Best purchase ever, highly satisfied",
            "Incredible quality, worth every penny",
            "Awesome product, five stars all the way",
            "Delighted with purchase, perfect choice",
            "Impressive quality, highly satisfied customer",
            "Excellent service and product quality",
            "Great experience, will recommend to friends",
            "Perfect quality, exactly as described",
            "Amazing value, very happy with purchase",
            "Outstanding product, exceeded expectations"
        ]
        
        positive_reviews.extend(generic_positive)
        return positive_reviews
    except Exception:
        return [
            "Great product, very satisfied",
            "Excellent quality, highly recommend",
            "Amazing service, will buy again",
            "Perfect purchase, exceeded expectations",
            "Love it, fantastic value",
            "Outstanding quality, very happy",
            "Wonderful product, great purchase",
            "Superb quality, exactly what I needed",
            "Brilliant product, top quality",
            "Fantastic service, very pleased"
        ]


def _train_sentiment_model():
    """Train a sentiment classifier on claims (negative) + synthetic positive reviews"""
    negative_texts = _load_claims()
    positive_texts = _generate_positive_reviews()
    
    # Ensure we have data
    if len(negative_texts) < 5:
        negative_texts = [
            "Product arrived damaged, very disappointed",
            "Very disappointed with quality, not what I expected",
            "Terrible service, not happy at all",
            "Defective item, requesting refund immediately",
            "Poor quality, complete waste of money",
            "Broken on arrival, very upset",
            "Not as described, feeling cheated",
            "Horrible experience, never again",
            "Worst purchase ever, total disappointment",
            "Faulty product, demanding replacement"
        ]
    
    if len(positive_texts) < 5:
        positive_texts = [
            "Great product, very satisfied",
            "Excellent quality, highly recommend",
            "Amazing service, will buy again",
            "Perfect purchase, exceeded expectations",
            "Love it, fantastic value",
            "Outstanding quality, very happy",
            "Wonderful product, great purchase",
            "Superb quality, exactly what I needed",
            "Brilliant product, top quality",
            "Fantastic service, very pleased"
        ]
    
    # Balance dataset - ensure equal positive and negative samples
    max_len = max(len(negative_texts), len(positive_texts))
    
    # Duplicate samples if needed to balance
    while len(negative_texts) < max_len:
        negative_texts.extend(negative_texts[:max_len - len(negative_texts)])
    
    while len(positive_texts) < max_len:
        positive_texts.extend(positive_texts[:max_len - len(positive_texts)])
    
    # Trim to same length
    negative_texts = negative_texts[:max_len]
    positive_texts = positive_texts[:max_len]
    
    # Create labeled dataset
    texts = negative_texts + positive_texts
    labels = [0] * len(negative_texts) + [1] * len(positive_texts)  # 0=negative, 1=positive
    
    # Vectorize with better parameters
    vectorizer = TfidfVectorizer(
        max_features=200, 
        ngram_range=(1, 3),
        min_df=1,
        max_df=0.9
    )
    X = vectorizer.fit_transform(texts)
    
    # Train with balanced class weights
    X_train, X_test, y_train, y_test = train_test_split(
        X, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    model = RandomForestClassifier(
        n_estimators=150, 
        random_state=42,
        class_weight='balanced',  # Important: balance classes
        max_depth=20
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    return model, vectorizer, accuracy, len(negative_texts), len(positive_texts)


def _analyze_text(text, model, vectorizer):
    """Predict sentiment of a single text"""
    X = vectorizer.transform([text])
    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    
    sentiment = 'Positive' if pred == 1 else 'Negative'
    confidence = float(proba[pred])
    
    return {
        'text': text,
        'sentiment': sentiment,
        'confidence': round(confidence * 100, 1)
    }

# ── endpoints ─────────────────────────────────────────────────────────────────

@sentiment_bp.route('/train', methods=['GET'])
def train_model():
    """Train the sentiment model and return stats"""
    try:
        model, vectorizer, accuracy, n_neg, n_pos = _train_sentiment_model()
        
        # Store in memory (in production, save to disk)
        sentiment_bp.model = model
        sentiment_bp.vectorizer = vectorizer
        
        return jsonify({
            'success': True,
            'accuracy': round(accuracy * 100, 1),
            'training_data': {
                'negative_samples': n_neg,
                'positive_samples': n_pos,
                'total': n_neg + n_pos
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@sentiment_bp.route('/analyze', methods=['POST'])
def analyze():
    """Analyze sentiment of user-provided text"""
    try:
        body = request.get_json(force=True) or {}
        text = body.get('text', '').strip()
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        # Train model if not already trained
        if not hasattr(sentiment_bp, 'model'):
            model, vectorizer, _, _, _ = _train_sentiment_model()
            sentiment_bp.model = model
            sentiment_bp.vectorizer = vectorizer
        
        result = _analyze_text(text, sentiment_bp.model, sentiment_bp.vectorizer)
        
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@sentiment_bp.route('/batch', methods=['GET'])
def analyze_batch():
    """Analyze all claims in the database"""
    try:
        claims = _load_claims()
        
        if not claims:
            return jsonify({
                'success': True,
                'results': [],
                'summary': {'total': 0, 'positive': 0, 'negative': 0}
            })
        
        # Train model if not already trained
        if not hasattr(sentiment_bp, 'model'):
            model, vectorizer, _, _, _ = _train_sentiment_model()
            sentiment_bp.model = model
            sentiment_bp.vectorizer = vectorizer
        
        results = [
            _analyze_text(text, sentiment_bp.model, sentiment_bp.vectorizer)
            for text in claims[:50]  # Limit to 50 for performance
        ]
        
        positive_count = sum(1 for r in results if r['sentiment'] == 'Positive')
        negative_count = len(results) - positive_count
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total': len(results),
                'positive': positive_count,
                'negative': negative_count,
                'positive_rate': round((positive_count / len(results)) * 100, 1) if results else 0
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
