"""
Competition & International Analysis
- Competition: Recommend products to sell based on competitor analysis
- International: Get average prices by category for international markets
"""

import warnings
warnings.filterwarnings('ignore')

import os
import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb

from db import query_df

competition_bp = Blueprint('competition', __name__)

# Path to competitor data file
COMPETITOR_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'all_concurrents.xls')

# ── helpers ──────────────────────────────────────────────────────────────────

def _load_competitor_data():
    """Load competitor product data from Excel file"""
    try:
        # Try reading with xlrd engine first
        try:
            df = pd.read_excel(COMPETITOR_FILE, engine='xlrd')
        except:
            # Fallback to openpyxl
            df = pd.read_excel(COMPETITOR_FILE, engine='openpyxl')
        
        # Clean column names
        df.columns = ['id', 'nom', 'prix', 'categorie', 'company']
        
        # Clean category names
        df['categorie'] = df['categorie'].astype(str).str.lower().str.strip()
        df['categorie'] = df['categorie'].replace({
            'boisd\'olivier': 'bois d\'olivier',
            'bois d\'olivier': 'bois d\'olivier',
            'boisd\'olivier': 'bois d\'olivier',
            'bois dolivier': 'bois d\'olivier',
            'céramiques': 'ceramiques',
            'déco': 'deco',
            'service de table': 'service de table'
        })
        
        # Clean prices
        df['prix'] = df['prix'].astype(str).str.replace(',', '.', regex=False)
        df['prix'] = df['prix'].str.extract(r'(\d+\.?\d*)')[0]
        df['prix'] = pd.to_numeric(df['prix'], errors='coerce')
        
        # Remove invalid rows
        df = df.dropna(subset=['prix'])
        df = df[df['prix'] > 0]
        df = df.reset_index(drop=True)
        
        return df
    except Exception as e:
        print(f"Error loading competitor data: {e}")
        return pd.DataFrame(columns=['id', 'nom', 'prix', 'categorie', 'company'])


def _train_best_seller_model(df):
    """Train XGBoost model to predict best-seller products"""
    if df.empty or len(df) < 10:
        return None, None, None
    
    # Create best_seller target (top 30% by price in each category)
    df['best_seller'] = df.groupby('categorie')['prix'].transform(
        lambda x: (x > x.quantile(0.7)).astype(int)
    )
    
    # Encode categorical features
    le_categorie = LabelEncoder()
    le_company = LabelEncoder()
    
    df['categorie_encoded'] = le_categorie.fit_transform(df['categorie'])
    df['company_encoded'] = le_company.fit_transform(df['company'])
    
    # Create features
    df['log_prix'] = np.log1p(df['prix'])
    df['prix_categorie_ratio'] = df.groupby('categorie')['prix'].transform(
        lambda x: x / x.mean() if x.mean() > 0 else 1
    )
    
    feature_cols = ['prix', 'log_prix', 'prix_categorie_ratio', 'categorie_encoded', 'company_encoded']
    X = df[feature_cols]
    y = df['best_seller']
    
    # Train model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss',
        use_label_encoder=False
    )
    
    model.fit(X, y)
    
    # Predict probabilities
    df['probabilite_best_seller'] = model.predict_proba(X)[:, 1]
    
    return df, model, feature_cols


def _get_category_prices():
    """Get average prices by category from sales data"""
    sql = """
        SELECT 
            c.name_category as category,
            COUNT(DISTINCT p.pk_id_product) as product_count,
            AVG(s.unit_price) as avg_price,
            MIN(s.unit_price) as min_price,
            MAX(s.unit_price) as max_price,
            SUM(s.quantity) as total_sold
        FROM fact_sale s
        INNER JOIN dim_product p ON s.fk_product = p.pk_id_product
        LEFT JOIN dim_category c ON p.fk_category = c.pk_id_category
        WHERE s.unit_price IS NOT NULL AND s.unit_price > 0
        GROUP BY c.name_category
        ORDER BY avg_price DESC
    """
    try:
        df = query_df(sql)
        return df
    except Exception:
        return pd.DataFrame()

# ── endpoints ─────────────────────────────────────────────────────────────────

@competition_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """Get recommended products to sell based on competitor analysis"""
    try:
        top_n = int(request.args.get('top_n', 20))
        
        df = _load_competitor_data()
        
        if df.empty:
            return jsonify({
                'success': True,
                'recommendations': [],
                'message': 'No competitor data available. Add products to analyze.'
            })
        
        df_predicted, model, features = _train_best_seller_model(df)
        
        if df_predicted is None:
            return jsonify({
                'success': False,
                'error': 'Insufficient data to train model'
            }), 400
        
        # Get top recommendations
        top_products = df_predicted.nlargest(top_n, 'probabilite_best_seller')
        
        recommendations = []
        for _, row in top_products.iterrows():
            recommendations.append({
                'id': int(row['id']),
                'name': row['nom'],
                'price': round(float(row['prix']), 2),
                'category': row['categorie'],
                'probability': round(float(row['probabilite_best_seller']) * 100, 1),
                'is_best_seller': int(row['best_seller'])
            })
        
        # Get model performance stats
        accuracy = (df_predicted['best_seller'] == (df_predicted['probabilite_best_seller'] > 0.5).astype(int)).mean()
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'total_products': len(df_predicted),
            'model_accuracy': round(accuracy * 100, 1),
            'categories': df_predicted['categorie'].nunique()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@competition_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get list of all categories with price statistics"""
    try:
        df = _get_category_prices()
        
        if df.empty:
            return jsonify({
                'success': True,
                'categories': [],
                'message': 'No category data available'
            })
        
        categories = []
        for _, row in df.iterrows():
            categories.append({
                'category': row['category'] if row['category'] else 'Uncategorized',
                'product_count': int(row['product_count']),
                'avg_price': round(float(row['avg_price']), 2),
                'min_price': round(float(row['min_price']), 2),
                'max_price': round(float(row['max_price']), 2),
                'total_sold': int(row['total_sold'])
            })
        
        return jsonify({
            'success': True,
            'categories': categories,
            'total_categories': len(categories)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@competition_bp.route('/category-price', methods=['GET'])
def get_category_price():
    """Get average price for a specific category"""
    try:
        category = request.args.get('category', '').strip()
        
        if not category:
            return jsonify({'success': False, 'error': 'Category parameter required'}), 400
        
        df = _get_category_prices()
        
        if df.empty:
            return jsonify({'success': False, 'error': 'No data available'}), 404
        
        # Find matching category (case-insensitive)
        category_data = df[df['category'].str.lower() == category.lower()]
        
        if category_data.empty:
            return jsonify({
                'success': False,
                'error': f'Category "{category}" not found'
            }), 404
        
        row = category_data.iloc[0]
        
        return jsonify({
            'success': True,
            'category': row['category'],
            'avg_price': round(float(row['avg_price']), 2),
            'min_price': round(float(row['min_price']), 2),
            'max_price': round(float(row['max_price']), 2),
            'product_count': int(row['product_count']),
            'total_sold': int(row['total_sold'])
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
