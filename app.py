import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import csv
from datetime import datetime, timedelta
import io
import time
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import json
import random
import psycopg2
import base64
import re
import hashlib
import csv          # 📥 nécessaire pour écrire dans le catalogue
import ast
from typing import Tuple, Optional
import string
import uuid

# Imports ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Configuration de la page
st.set_page_config(
    page_title="FLUX/PARA Commander",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# FORCER LE MODE CLAIR ☀️
st.markdown("""
<style>
    .stApp {
        background-color: #ffffff;
        color: #262626;
    }
    
    .stSidebar {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }
    
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        border: none;
        border-radius: 6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        background-color: #0d5aa7;
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .stExpander {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
    }
    
    .stSelectbox > div > div {
        background-color: #ffffff;
        border: 1px solid #ced4da;
    }
    
    .stTextInput > div > div > input {
        background-color: #ffffff;
        border: 1px solid #ced4da;
        color: #495057;
    }
    
    /* RESPONSIVE MOBILE 📱 */
    @media (max-width: 768px) {
        .stButton > button {
            font-size: 14px;
            padding: 0.75rem;
            margin: 0.25rem 0;
        }
        
        .stColumns {
            flex-direction: column;
        }
        
        .stExpander {
            margin: 0.25rem 0;
        }
        
        .stSidebar {
            min-width: 100% !important;
        }
    }
    
    /* Style pour les métriques */
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Messages d'erreur/succès plus visibles */
    .stAlert {
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Indicateur de build pour vérifier que le bon app.py est chargé
st.caption("Build: local-" + datetime.now().strftime('%H:%M:%S'))

st.markdown("""
<style>
/* === RESPONSIVE MOBILE DESIGN === */
@media (max-width: 768px) {
    /* Masquer la sidebar par défaut sur mobile */
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Boutons plus gros pour les doigts */
    .stButton > button {
        height: 50px !important;
        font-size: 16px !important;
        padding: 12px 20px !important;
        margin: 5px 0 !important;
    }
    
    /* Navigation en colonnes sur mobile */
    .mobile-nav {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 10px 0;
    }
    
    /* Formulaires adaptés mobile */
    .stTextInput > div > div > input {
        height: 45px !important;
        font-size: 16px !important;
    }
    
    .stSelectbox > div > div > div {
        height: 45px !important;
        font-size: 16px !important;
    }
    
    /* Cartes articles plus grandes sur mobile */
    .article-card-mobile {
        padding: 15px;
        margin: 10px 0;
        border: 1px solid #ddd;
        border-radius: 8px;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Texte plus lisible sur mobile */
    .main .block-container {
        padding: 1rem !important;
    }
    
    /* Métriques empilées sur mobile */
    .metric-mobile {
        text-align: center;
        padding: 10px;
        margin: 5px 0;
        background: #f0f2f6;
        border-radius: 5px;
    }
}

/* === NAVIGATION HAMBURGER === */
.hamburger-menu {
    display: none;
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
    background: #ff6b6b;
    color: white;
    border: none;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    cursor: pointer;
    font-size: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
}

@media (max-width: 768px) {
    .hamburger-menu {
        display: block;
    }
}

/* === ANIMATIONS === */
.fade-in {
    animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

.slide-in {
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from { transform: translateX(-100%); }
    to { transform: translateX(0); }
}

/* === THEME MODERNE === */
.modern-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 15px;
    margin: 10px 0;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}

.modern-card:hover {
    transform: translateY(-5px);
}

.glass-effect {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 15px;
    padding: 20px;
}

/* === INTERFACE VOCALE SUPPRIMÉE === */

.ai-suggestions {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    padding: 15px;
    margin: 10px 0;
    color: white;
}

.suggestion-item {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 10px;
    margin: 5px 0;
    cursor: pointer;
    transition: all 0.3s ease;
}

.suggestion-item:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateX(5px);
}

/* Styles de détection de doublons supprimés */
</style>
""", unsafe_allow_html=True)

# === VARIABLES GLOBALES ===
MAX_CART_AMOUNT = 1500.0  # Budget maximum par commande

# Configuration base de données
# Utiliser DATABASE_URL de Railway (variable d'environnement) pour éviter les erreurs 502
# Railway fournit cette variable automatiquement quand Postgres est lié au service
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:XmqANsOjbMMrtzLvkoDhRueHSTUpocsQ@gondola.proxy.rlwy.net:15641/railway")
# Railway fournit postgres://, psycopg2 accepte postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
# Chemin absolu du CSV des articles (évite les erreurs de répertoire courant)
ARTICLES_CSV_PATH = os.path.join(os.path.dirname(__file__), 'articles.csv')
# Fichier SQLite local (fallback)
DATABASE_PATH = "commandes.db"
# Par défaut: PostgreSQL (prod). Pour forcer SQLite en local: USE_POSTGRESQL=false
USE_POSTGRESQL = os.environ.get("USE_POSTGRESQL", "true").lower() in ("1", "true", "yes")

# === CHARGEMENT DES DONNÉES ===
@st.cache_data(ttl=300, show_spinner="🔄 Chargement des articles...")
def load_articles():
    """Charge les articles depuis PostgreSQL (prod) ou CSV (local)"""
    if USE_POSTGRESQL:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT reference, nom, description, prix, unitee 
                FROM articles 
                ORDER BY reference
            """)
            rows = cursor.fetchall()
            conn.close()
            if not rows:
                return _load_articles_from_csv_fallback()
            df = pd.DataFrame(rows, columns=['N° Référence', 'Nom', 'Description', 'Prix', 'Unitée'])
            df['Prix'] = pd.to_numeric(df['Prix'], errors='coerce')
            df = df.dropna(subset=['Prix'])
            df = df[df['Prix'] >= 0]
            df['Nom'] = df['Nom'].astype(str).str.strip()
            df = df[df['Nom'].str.len() >= 1]
            return df
        except Exception as e:
            return _load_articles_from_csv_fallback()
    
    return _load_articles_from_csv_fallback()

def _load_articles_from_csv_fallback():
    """Charge depuis le CSV (local / fallback)"""
    try:
        df = pd.read_csv(ARTICLES_CSV_PATH, encoding='utf-8', usecols=[0,1,2,3,4])
        df.columns = ['N° Référence', 'Nom', 'Description', 'Prix', 'Unitée']
        df = df.dropna(subset=['Prix'])
        df['Prix'] = pd.to_numeric(df['Prix'], errors='coerce')
        df = df.dropna(subset=['Prix'])
        df = df[df['Prix'] >= 0]
        df['Nom'] = df['Nom'].astype(str).str.strip()
        df = df[df['Nom'].str.len() >= 1]
        return df
    except FileNotFoundError:
        return create_sample_articles()
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(ARTICLES_CSV_PATH, encoding='latin-1', usecols=[0,1,2,3,4])
            df.columns = ['N° Référence', 'Nom', 'Description', 'Prix', 'Unitée']
            return df
        except Exception:
            return create_sample_articles()
    except Exception:
        return create_sample_articles()

def read_csv_safe(filename):
    """Lecture sécurisée du CSV ligne par ligne"""
    import csv
    data = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            # Lire la première ligne pour les en-têtes
            first_line = file.readline().strip()
            headers = first_line.split(',')
            
            # Lire le reste ligne par ligne
            for line_num, line in enumerate(file, 2):
                try:
                    # Nettoyer la ligne
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Séparer les champs
                    fields = line.split(',')
                    
                    # Si trop de champs, prendre seulement les premiers
                    if len(fields) > len(headers):
                        fields = fields[:len(headers)]
                    
                    # Si pas assez de champs, compléter avec des valeurs vides
                    while len(fields) < len(headers):
                        fields.append('')
                    
                    # Créer un dictionnaire
                    row_dict = dict(zip(headers, fields))
                    data.append(row_dict)
                    
                except Exception as e:
                    st.warning(f"⚠️ Ligne {line_num} ignorée: {e}")
                    continue
        
        # Créer le DataFrame
        df = pd.DataFrame(data)
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur lecture manuelle: {e}")
        return create_sample_articles()

def create_sample_articles():
    """Crée des articles d'exemple si le CSV ne peut pas être lu"""
    st.warning("⚠️ Utilisation d'articles d'exemple")
    
    sample_data = {
        'N° Référence': [
            '40953', '34528', '41074', '334', '37386'
        ],
        'Nom': [
            'Chaussure de sécurité JALAS Taille 42',
            'Blouson Orange Taille L',
            'Gants RIG ROG Taille 9',
            'Casque Polyester Blanc',
            'Bollé Transparente TRACPSI'
        ],
        'Description': [
            'Chaussures',
            'Veste Blouson', 
            'Gants',
            'Casque',
            'Lunette'
        ],
        'Prix': [99.90, 105.00, 8.80, 22.99, 10.50],
        'Unitée': [
            'Par paire', 'Par Veste', 'La paire', 'Par casque', 'Par unitée'
        ]
    }
    
    return pd.DataFrame(sample_data)

articles_df = load_articles()

# === CACHE INTELLIGENT ===
@st.cache_data(ttl=600, show_spinner="📊 Calcul des statistiques...")
def get_cached_statistics():
    """Cache les statistiques pour éviter les recalculs"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as total_orders, 
                       SUM(total_prix) as total_amount,
                       AVG(total_prix) as avg_amount
                FROM commandes
            """)
            stats = cursor.fetchone()
            conn.close()
            return {
                'total_orders': stats[0] or 0,
                'total_amount': stats[1] or 0,
                'avg_amount': stats[2] or 0
            }
    except Exception:
        pass
    return {'total_orders': 0, 'total_amount': 0, 'avg_amount': 0}

@st.cache_data(ttl=180, show_spinner="🔄 Mise à jour du catalogue...")
def get_cached_categories():
    """Cache les catégories et compteurs d'articles"""
    articles_df = load_articles()
    if articles_df.empty:
        return {}
    
    categories = {}
    for category in ["Protection Tête", "Protection Auditive", "Protection Oculaire", "Protection Respiratoire",
                    "Protection Main", "Protection Pied", "Protection Corps", "Vêtements Haute Visibilité",
                    "Oxycoupage", "EPI Général", "No Touch", "Outils", "Éclairage", "Marquage", 
                    "Bureau", "Nettoyage", "Hygiène", "Divers"]:
        count = count_articles_in_category(category)
        if count > 0:
            categories[category] = count
    return categories

# === INTELLIGENCE ARTIFICIELLE ===
@st.cache_data(ttl=900, show_spinner="🤖 Analyse IA en cours...")
def get_ai_suggestions_for_user(user_id, current_cart=None):
    """Génère des suggestions IA basées sur l'historique utilisateur"""
    try:
        if not USE_POSTGRESQL or not user_id:
            return []
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Récupérer l'historique des commandes de l'utilisateur
        cursor.execute("""
            SELECT articles_json FROM commandes 
            WHERE user_id = %s 
            ORDER BY date DESC 
            LIMIT 10
        """, (user_id,))
        
        user_orders = cursor.fetchall()
        
        # Récupérer les articles les plus commandés par l'équipe
        cursor.execute("""
            SELECT c.articles_json FROM commandes c
            JOIN users u ON c.contremaître = u.username
            WHERE u.equipe = (SELECT equipe FROM users WHERE id = %s)
            ORDER BY c.date DESC 
            LIMIT 20
        """, (user_id,))
        
        team_orders = cursor.fetchall()
        conn.close()
        
        # Analyser les patterns
        article_frequency = {}
        article_combinations = {}
        
        # Analyser l'historique personnel
        for order in user_orders:
            if order[0]:
                try:
                    articles = json.loads(order[0])
                    if not isinstance(articles, list):
                        articles = [articles]
                    
                    for article in articles:
                        if isinstance(article, dict):
                            nom = article.get('Nom', '')
                            if nom:
                                article_frequency[nom] = article_frequency.get(nom, 0) + 2  # Poids plus fort pour l'historique personnel
                except:
                    continue
        
        # Analyser l'historique d'équipe
        for order in team_orders:
            if order[0]:
                try:
                    articles = json.loads(order[0])
                    if not isinstance(articles, list):
                        articles = [articles]
                    
                    for article in articles:
                        if isinstance(article, dict):
                            nom = article.get('Nom', '')
                            if nom:
                                article_frequency[nom] = article_frequency.get(nom, 0) + 1
                except:
                    continue
        
        # Filtrer les articles déjà dans le panier
        current_cart_items = set()
        if current_cart:
            for item in current_cart:
                if isinstance(item, dict):
                    current_cart_items.add(item.get('Nom', ''))
        
        # Générer les suggestions (exclure les articles déjà dans le panier)
        suggestions = []
        seen_references = set()
        articles_df = load_articles()
        
        for nom, freq in sorted(article_frequency.items(), key=lambda x: x[1], reverse=True)[:10]:
            if nom not in current_cart_items:
                # Trouver l'article dans le catalogue
                matching_articles = articles_df[articles_df['Nom'].str.contains(nom, case=False, na=False, regex=False)]
                if not matching_articles.empty:
                    article = matching_articles.iloc[0].to_dict()
                    # Éviter les doublons: plusieurs noms proches peuvent matcher le même article
                    ref = str(article.get('N° Référence', '')) or article.get('Nom', '')
                    if ref in seen_references:
                        continue
                    seen_references.add(ref)
                    suggestions.append({
                        'article': article,
                        'score': freq,
                        'reason': f"Commandé {freq} fois récemment"
                    })
        
        return suggestions[:5]  # Top 5 suggestions
        
    except Exception as e:
        return []

@st.cache_data(ttl=300)
# Fonction de détection de doublons supprimée (fonctionnalité gênante)

def get_contextual_recommendations(current_article):
    """Recommandations contextuelles basées sur l'article sélectionné"""
    if not isinstance(current_article, dict):
        return []
    
    current_name = current_article.get('Nom', '').lower()
    current_category = current_article.get('Description', '')
    
    articles_df = load_articles()
    recommendations = []
    
    # Règles de recommandation contextuelle
    context_rules = {
        'casque': ['lunette', 'bouchon', 'protection auditive'],
        'gant': ['manche', 'protection', 'crème'],
        'chaussure': ['semelle', 'chaussette', 'protection pied'],
        'masque': ['filtre', 'cartouche', 'protection respiratoire'],
        'soudage': ['cagoule', 'gant', 'protection', 'tablier'],
        'oxycoup': ['tablier', 'gant', 'protection chaleur']
    }
    
    # Trouver les recommandations basées sur les règles
    for keyword, related_items in context_rules.items():
        if keyword in current_name:
            for related in related_items:
                matching = articles_df[
                    articles_df['Nom'].str.contains(related, case=False, na=False) &
                    (articles_df['Nom'] != current_article.get('Nom', ''))
                ]
                if not matching.empty:
                    for _, article in matching.head(2).iterrows():
                        recommendations.append({
                            'article': article.to_dict(),
                            'reason': f"Complément recommandé avec {keyword}"
                        })
    
    # Recommandations par catégorie
    if current_category:
        same_category = articles_df[
            (articles_df['Description'] == current_category) &
            (articles_df['Nom'] != current_article.get('Nom', ''))
        ]
        if not same_category.empty:
            for _, article in same_category.head(3).iterrows():
                recommendations.append({
                    'article': article.to_dict(),
                    'reason': f"Même catégorie: {current_category}"
                })
    
    return recommendations[:4]  # Limiter à 4 recommandations

# === INTERFACE VOCALE SUPPRIMÉE ===
# (Fonctionnalité retirée à la demande de l'utilisateur)

def show_ai_suggestions_panel(user_id, current_cart):
    """Panneau de suggestions IA intelligentes"""
    suggestions = get_ai_suggestions_for_user(user_id, current_cart)
    
    if suggestions:
        st.markdown('<div class="ai-suggestions">', unsafe_allow_html=True)
        st.markdown("### 🤖 Suggestions IA pour vous")
        
        for idx, suggestion in enumerate(suggestions):
            article = suggestion['article']
            reason = suggestion['reason']
            score = suggestion['score']
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div class="suggestion-item">
                    <strong>{article.get('Nom', '')[:40]}</strong><br>
                    <small>💡 {reason} | 🎯 Score: {score}</small><br>
                    <small>💰 {article.get('Prix', 0)}€</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("➕", key=f"ai_add_{idx}_{article.get('N° Référence', '')}", 
                           help=f"Ajouter {article.get('Nom', '')} au panier"):
                    add_to_cart(article)
                    st.success(f"✅ {article.get('Nom', '')[:30]} ajouté!")
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# Fonction de détection de doublons supprimée (fonctionnalité gênante)

# === ANALYTICS AVANCÉS ===
@st.cache_data(ttl=1800, show_spinner="📊 Génération des analytics avancés...")
def get_advanced_analytics(year=None):
    """Génère des analytics avancés avec prédictions (filtré par année si précisée)"""
    try:
        if not USE_POSTGRESQL:
            return None
        
        year = year or datetime.now().year
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Données de base (filtrées par année)
        cursor.execute("""
            SELECT 
                DATE_TRUNC('month', date) as mois,
                COUNT(*) as nb_commandes,
                SUM(total_prix) as montant_total,
                AVG(total_prix) as montant_moyen,
                equipe,
                contremaître
            FROM commandes 
            WHERE EXTRACT(YEAR FROM date) = %s
            GROUP BY DATE_TRUNC('month', date), equipe, contremaître
            ORDER BY mois DESC
        """, (year,))
        
        monthly_data = cursor.fetchall()
        
        # Top articles (filtré par année)
        cursor.execute("""
            SELECT 
                articles_json,
                date,
                total_prix,
                equipe
            FROM commandes 
            WHERE EXTRACT(YEAR FROM date) = %s
            ORDER BY date DESC
        """, (year,))
        
        orders_data = cursor.fetchall()
        
        # Budget par équipe (requête dédiée pour précision)
        cursor.execute("""
            SELECT equipe, 
                   COUNT(*) as nb_commandes, 
                   SUM(total_prix) as total_value,
                   AVG(total_prix) as avg_order
            FROM commandes 
            WHERE EXTRACT(YEAR FROM date) = %s AND equipe IS NOT NULL
            GROUP BY equipe
            ORDER BY total_value DESC
        """, (year,))
        team_budget_rows = cursor.fetchall()
        
        # Dépenses mensuelles par équipe
        cursor.execute("""
            SELECT TO_CHAR(date, 'YYYY-MM') as mois, equipe, SUM(total_prix) as total
            FROM commandes 
            WHERE EXTRACT(YEAR FROM date) = %s AND equipe IS NOT NULL
            GROUP BY TO_CHAR(date, 'YYYY-MM'), equipe
            ORDER BY mois, equipe
        """, (year,))
        monthly_by_team_rows = cursor.fetchall()
        
        # Top commandeurs (contremaîtres)
        cursor.execute("""
            SELECT contremaître, COUNT(*) as nb_cmd, SUM(total_prix) as total
            FROM commandes 
            WHERE EXTRACT(YEAR FROM date) = %s
            GROUP BY contremaître
            ORDER BY total DESC
            LIMIT 10
        """, (year,))
        top_commanders = cursor.fetchall()
        
        conn.close()
        
        # Budget par équipe
        team_performance = {}
        total_global = 0
        for row in team_budget_rows:
            equipe, nb_cmd, total_val, avg_ord = row
            team = equipe or 'Unknown'
            total_val = float(total_val or 0)
            total_global += total_val
            team_performance[team] = {
                'orders': int(nb_cmd or 0),
                'total_value': total_val,
                'avg_order': float(avg_ord or 0)
            }
        for t in team_performance:
            team_performance[t]['pct_total'] = (team_performance[t]['total_value'] / total_global * 100) if total_global > 0 else 0
        
        # Dépenses mensuelles par équipe
        monthly_by_team = {}
        for mois, equipe, total in monthly_by_team_rows:
            team = equipe or 'Unknown'
            if mois not in monthly_by_team:
                monthly_by_team[mois] = {}
            monthly_by_team[mois][team] = float(total or 0)
        
        # Analyse des articles
        article_stats = {}
        monthly_trends = {}
        
        for order in orders_data:
            if order[0]:  # articles_json
                try:
                    articles = json.loads(order[0])
                    if not isinstance(articles, list):
                        articles = [articles]
                    
                    month_key = order[1].strftime('%Y-%m') if order[1] else 'unknown'
                    team = order[3] or 'Unknown'
                    
                    for article in articles:
                        if isinstance(article, dict):
                            nom = article.get('Nom', 'Unknown')
                            prix = float(article.get('Prix', 0))
                            
                            if nom not in article_stats:
                                article_stats[nom] = {
                                    'count': 0,
                                    'total_value': 0,
                                    'avg_price': 0,
                                    'teams': set()
                                }
                            article_stats[nom]['count'] += 1
                            article_stats[nom]['total_value'] += prix
                            article_stats[nom]['teams'].add(team)
                            article_stats[nom]['avg_price'] = article_stats[nom]['total_value'] / article_stats[nom]['count']
                            
                            if month_key not in monthly_trends:
                                monthly_trends[month_key] = {'orders': 0, 'value': 0, 'articles': 0}
                            monthly_trends[month_key]['articles'] += 1
                            monthly_trends[month_key]['value'] += prix
                except:
                    continue
        
        # Calcul des prédictions simples (tendance linéaire)
        predictions = {}
        if len(monthly_trends) >= 3:
            sorted_months = sorted(monthly_trends.keys())
            recent_months = sorted_months[-3:]
            
            # Prédiction basée sur la moyenne des 3 derniers mois
            avg_orders = sum(monthly_trends[m]['articles'] for m in recent_months) / len(recent_months)
            avg_value = sum(monthly_trends[m]['value'] for m in recent_months) / len(recent_months)
            
            # Calcul de la tendance (croissance/décroissance)
            if len(recent_months) >= 2:
                trend_orders = (monthly_trends[recent_months[-1]]['articles'] - monthly_trends[recent_months[0]]['articles']) / len(recent_months)
                trend_value = (monthly_trends[recent_months[-1]]['value'] - monthly_trends[recent_months[0]]['value']) / len(recent_months)
            else:
                trend_orders = 0
                trend_value = 0
            
            predictions = {
                'next_month_articles': max(0, avg_orders + trend_orders),
                'next_month_value': max(0, avg_value + trend_value),
                'trend_direction': 'up' if trend_value > 0 else 'down' if trend_value < 0 else 'stable',
                'confidence': min(100, max(50, 80 - abs(trend_value) / avg_value * 100)) if avg_value > 0 else 50
            }
        
        return {
            'article_stats': article_stats,
            'monthly_trends': monthly_trends,
            'team_performance': team_performance,
            'monthly_by_team': monthly_by_team,
            'top_commanders': top_commanders,
            'predictions': predictions,
            'top_articles': sorted(article_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:10],
            'top_value_articles': sorted(article_stats.items(), key=lambda x: x[1]['total_value'], reverse=True)[:10],
            'year': year
        }
        
    except Exception as e:
        st.error(f"Erreur analytics: {e}")
        return None

@st.cache_data(ttl=3600)
def get_budget_alerts():
    """Génère des alertes automatiques sur les budgets"""
    try:
        if not USE_POSTGRESQL:
            return []
            
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Alertes par équipe - dépassements récents
        cursor.execute("""
            SELECT 
                equipe,
                SUM(total_prix) as total_mensuel,
                COUNT(*) as nb_commandes,
                AVG(total_prix) as moyenne_commande
            FROM commandes 
            WHERE date >= DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY equipe
            HAVING SUM(total_prix) > 5000  -- Seuil d'alerte
            ORDER BY total_mensuel DESC
        """)
        
        budget_alerts = []
        for row in cursor.fetchall():
            equipe, total, nb_cmd, moyenne = row
            budget_alerts.append({
                'type': 'budget_high',
                'equipe': equipe,
                'message': f"Équipe {equipe}: {total:.2f}€ ce mois ({nb_cmd} commandes)",
                'severity': 'high' if total > 10000 else 'medium',
                'value': total
            })
        
        # Alertes commandes inhabituellement élevées
        cursor.execute("""
            SELECT contremaître, total_prix, date, equipe
            FROM commandes 
            WHERE total_prix > %s 
            AND date >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY total_prix DESC
        """, (MAX_CART_AMOUNT * 1.5,))
        
        for row in cursor.fetchall():
            contremaitre, total, date, equipe = row
            budget_alerts.append({
                'type': 'order_high',
                'message': f"Commande élevée: {contremaitre} ({equipe}) - {total:.2f}€",
                'severity': 'high',
                'date': date,
                'value': total
            })
        
        conn.close()
        return budget_alerts
        
    except Exception as e:
        return []

def export_analytics_to_excel(analytics_data):
    """Exporte les analytics vers Excel"""
    try:
        import io
        
        if not analytics_data:
            return None
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Feuille Top Articles (tous les articles triés par quantité)
            article_stats = analytics_data.get('article_stats', {})
            top_articles = sorted(article_stats.items(), key=lambda x: x[1]['count'], reverse=True)
            if top_articles:
                excel_data = []
                for nom, stats in top_articles:
                    excel_data.append({
                        'Article': str(nom)[:255],
                        'Quantité commandée': stats['count'],
                        'Valeur totale (€)': round(stats['total_value'], 2),
                        'Prix moyen (€)': round(stats['avg_price'], 2),
                        'Équipes utilisatrices': len(stats.get('teams', set()))
                    })
                pd.DataFrame(excel_data).to_excel(writer, sheet_name='Top Articles', index=False)
            else:
                pd.DataFrame(columns=['Article', 'Quantité', 'Valeur (€)']).to_excel(writer, sheet_name='Top Articles', index=False)
            
            # Feuille Tendances mensuelles
            monthly_trends = analytics_data.get('monthly_trends', {})
            if monthly_trends:
                monthly_df = pd.DataFrame([
                    {'Mois': month, 'Nb articles': data['articles'], 'Valeur (€)': round(data['value'], 2)}
                    for month, data in sorted(monthly_trends.items())
                ])
                monthly_df.to_excel(writer, sheet_name='Tendances Mensuelles', index=False)
            
            # Feuille Budget par équipe
            team_perf = analytics_data.get('team_performance', {})
            if team_perf:
                team_df = pd.DataFrame([
                    {
                        'Équipe': t,
                        'Budget consommé (€)': round(d['total_value'], 2),
                        'Nb commandes': d['orders'],
                        'Moyenne/commande (€)': round(d.get('avg_order', 0), 2),
                        '% du total': round(d.get('pct_total', 0), 1)
                    }
                    for t, d in team_perf.items()
                ])
                team_df.to_excel(writer, sheet_name='Budget par Équipe', index=False)
            
            # Feuille Top commandeurs
            top_cmd = analytics_data.get('top_commanders', [])
            if top_cmd:
                cmd_df = pd.DataFrame([
                    {'Contremaître': r[0], 'Nb commandes': r[1], 'Total (€)': round(r[2], 2)}
                    for r in top_cmd
                ])
                cmd_df.to_excel(writer, sheet_name='Top Commandeurs', index=False)
        
        output.seek(0)
        return output
    except Exception as e:
        st.error(f"Erreur export Excel: {e}")
        return None

def show_advanced_analytics():
    """Dashboard analytique avancé avec prédictions et alertes"""
    if not st.session_state.current_user.get("can_view_stats"):
        st.error("⛔ Accès refusé - Réservé aux gestionnaires")
        return

    st.markdown("# 📊 Dashboard Analytique Avancé")
    st.markdown("*Intelligence d'affaires pour l'optimisation des commandes*")
    
    # Filtre par année
    current_year = datetime.now().year
    available_years = list(range(current_year, current_year - 5, -1))
    col_filter, _ = st.columns([1, 3])
    with col_filter:
        selected_year = st.selectbox(
            "📅 Année",
            options=available_years,
            index=0,
            key="analytics_year_select"
        )
        st.session_state['analytics_year'] = selected_year
    
    # Récupération des données avec cache (filtré par année)
    analytics_data = get_advanced_analytics(selected_year)
    budget_alerts = get_budget_alerts()
    
    if not analytics_data:
        st.warning("📊 Données insuffisantes pour générer des analytics avancés")
        return
    
    # === ALERTES EN TEMPS RÉEL ===
    if budget_alerts:
        st.markdown("## 🚨 Alertes Automatiques")
        for alert in budget_alerts[:5]:  # Top 5 alertes
            if alert['severity'] == 'high':
                st.error(f"🔴 **{alert['message']}**")
            else:
                st.warning(f"🟡 **{alert['message']}**")
    
    # === KPIS PRINCIPAUX ===
    st.markdown("## 📈 KPIs en Temps Réel")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_orders = sum(stats['count'] for stats in analytics_data['article_stats'].values())
        st.metric(
            "📦 Articles Commandés",
            f"{total_orders:,}",
            delta=f"+{int(analytics_data.get('predictions', {}).get('next_month_articles', 0))} prévu"
        )
    
    with col2:
        total_value = sum(stats['total_value'] for stats in analytics_data['article_stats'].values())
        st.metric(
            "💰 Valeur Totale",
            f"{total_value:,.0f}€",
            delta=f"+{analytics_data.get('predictions', {}).get('next_month_value', 0):.0f}€ prévu"
        )
    
    with col3:
        active_teams = len(analytics_data['team_performance'])
        avg_order_value = total_value / max(total_orders, 1)
        st.metric(
            "👥 Équipes Actives",
            active_teams,
            delta=f"{avg_order_value:.1f}€ moy/article"
        )
    
    with col4:
        predictions = analytics_data.get('predictions', {})
        trend_icon = "📈" if predictions.get('trend_direction') == 'up' else "📉" if predictions.get('trend_direction') == 'down' else "➡️"
        confidence = predictions.get('confidence', 0)
        st.metric(
            f"{trend_icon} Tendance",
            f"{confidence:.0f}% confiance",
            delta=f"Prédiction {predictions.get('trend_direction', 'stable')}"
        )
    
    # === GRAPHIQUES INTERACTIFS ===
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("### 📊 Tendances Mensuelles")
        if analytics_data['monthly_trends']:
            months = list(analytics_data['monthly_trends'].keys())
            values = [data['value'] for data in analytics_data['monthly_trends'].values()]
            articles_count = [data['articles'] for data in analytics_data['monthly_trends'].values()]
            
            # Graphique combiné avec Plotly
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=months, y=values,
                mode='lines+markers',
                name='Valeur (€)',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            fig.add_trace(go.Bar(
                x=months, y=articles_count,
                name='Nb Articles',
                yaxis='y2',
                opacity=0.7,
                marker_color='#ff7f0e'
            ))
            
            fig.update_layout(
                title="Évolution des Commandes",
                xaxis_title="Mois",
                yaxis=dict(title="Valeur (€)", side='left'),
                yaxis2=dict(title="Nombre d'Articles", side='right', overlaying='y'),
                hovermode='x unified',
                template='plotly_white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.markdown("### 🏆 Performance par Équipe")
        if analytics_data['team_performance']:
            teams = list(analytics_data['team_performance'].keys())
            team_values = [data['total_value'] for data in analytics_data['team_performance'].values()]
            
            import plotly.express as px
            fig_pie = px.pie(
                values=team_values,
                names=teams,
                title="Répartition des Dépenses par Équipe",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # === BUDGET CONSOMMÉ PAR ÉQUIPE ===
    st.markdown("## 💰 Budget consommé par équipe")
    if analytics_data.get('team_performance'):
        team_data = []
        for equipe, d in sorted(analytics_data['team_performance'].items(), key=lambda x: x[1]['total_value'], reverse=True):
            team_data.append({
                'Équipe': equipe,
                'Budget consommé (€)': f"{d['total_value']:,.0f}",
                'Nb commandes': d['orders'],
                'Moyenne/commande (€)': f"{d['avg_order']:.0f}",
                '% du total': f"{d.get('pct_total', 0):.1f}%"
            })
        st.dataframe(pd.DataFrame(team_data), use_container_width=True, hide_index=True)
        
        # Graphique barres horizontal
        fig_team = px.bar(
            x=[d['total_value'] for d in analytics_data['team_performance'].values()],
            y=list(analytics_data['team_performance'].keys()),
            orientation='h',
            title="Budget consommé par équipe (€)",
            labels={'x': 'Montant (€)', 'y': 'Équipe'},
            color=[d['total_value'] for d in analytics_data['team_performance'].values()],
            color_continuous_scale='Teal'
        )
        fig_team.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig_team, use_container_width=True)
    
    # === ÉVOLUTION MENSUELLE PAR ÉQUIPE + TOP COMMANDEURS ===
    col_evo, col_cmd = st.columns(2)
    with col_evo:
        st.markdown("### 📅 Évolution mensuelle par équipe")
        if analytics_data.get('monthly_by_team'):
            monthly_team = analytics_data['monthly_by_team']
            months = sorted(monthly_team.keys())
            teams = set()
            for m in months:
                teams.update(monthly_team[m].keys())
            teams = sorted(teams)
            if months and teams:
                fig_evo = go.Figure()
                for team in teams:
                    values = [monthly_team.get(m, {}).get(team, 0) for m in months]
                    fig_evo.add_trace(go.Bar(name=team, x=months, y=values))
                fig_evo.update_layout(barmode='stack', title="Dépenses mensuelles par équipe (€)", height=350)
                st.plotly_chart(fig_evo, use_container_width=True)
    
    with col_cmd:
        st.markdown("### 👤 Top commandeurs (contremaîtres)")
        if analytics_data.get('top_commanders'):
            cmd_data = [{'Contremaître': r[0] or 'N/A', 'Commandes': r[1], 'Total (€)': f"{r[2]:,.0f}"} for r in analytics_data['top_commanders']]
            st.dataframe(pd.DataFrame(cmd_data), use_container_width=True, hide_index=True)
        else:
            st.caption("Aucune donnée")
    
    # === TOP ARTICLES AVEC PRÉDICTIONS ===
    st.markdown("### 🔥 Top Articles & Analyse Prédictive")
    
    tab1, tab2, tab3 = st.tabs(["📊 Top Quantité", "💰 Top Valeur", "🔮 Prédictions"])
    
    with tab1:
        if analytics_data['top_articles']:
            top_data = []
            for nom, stats in analytics_data['top_articles'][:10]:
                top_data.append({
                    'Article': nom[:50],
                    'Quantité': stats['count'],
                    'Valeur Totale': f"{stats['total_value']:.0f}€",
                    'Prix Moyen': f"{stats['avg_price']:.2f}€",
                    'Équipes': len(stats['teams'])
                })
            
            df_display = pd.DataFrame(top_data)
            st.dataframe(df_display, use_container_width=True)
    
    with tab2:
        if analytics_data['top_value_articles']:
            # Graphique en barres horizontales
            names = [item[0][:30] for item in analytics_data['top_value_articles'][:10]]
            values = [item[1]['total_value'] for item in analytics_data['top_value_articles'][:10]]
            
            fig_bar = px.bar(
                x=values, y=names,
                orientation='h',
                title="Top 10 Articles par Valeur Totale",
                labels={'x': 'Valeur (€)', 'y': 'Articles'},
                color=values,
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(height=500)
            st.plotly_chart(fig_bar, use_container_width=True)
    
    with tab3:
        predictions = analytics_data.get('predictions', {})
        if predictions:
            st.markdown("#### 🔮 Prédictions Mois Prochain")
            
            pred_col1, pred_col2, pred_col3 = st.columns(3)
            
            with pred_col1:
                st.metric(
                    "📦 Articles Prévus",
                    f"{predictions.get('next_month_articles', 0):.0f}",
                    delta=f"{predictions.get('trend_direction', 'stable')}"
                )
            
            with pred_col2:
                st.metric(
                    "💰 Valeur Prévue",
                    f"{predictions.get('next_month_value', 0):.0f}€",
                    delta=f"{predictions.get('confidence', 0):.0f}% confiance"
                )
            
            with pred_col3:
                trend_direction = predictions.get('trend_direction', 'stable')
                if trend_direction == 'up':
                    st.success("📈 Tendance à la hausse")
                elif trend_direction == 'down':
                    st.error("📉 Tendance à la baisse")
                else:
                    st.info("➡️ Tendance stable")
    
    # === EXPORT ===
    st.markdown("### 📤 Exports")
    
    excel_data = export_analytics_to_excel(analytics_data)
    if excel_data:
        st.download_button(
            label="📊 Export Excel Détaillé",
            data=excel_data.getvalue(),
            file_name=f"analytics_flux_para_{st.session_state.get('analytics_year', datetime.now().year)}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.caption("Aucune donnée à exporter pour cette période.")

# === FONCTIONS BASE DE DONNÉES ===
def init_database():
    """Initialise la base de données"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute('SET search_path TO public')
        
        # Table users avec TOUTES les colonnes nécessaires
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                equipe VARCHAR(50),
                fonction VARCHAR(100),
                couleur_preferee VARCHAR(30),
                can_add_articles BOOLEAN DEFAULT FALSE,
                can_view_stats BOOLEAN DEFAULT FALSE,
                can_view_all_orders BOOLEAN DEFAULT FALSE,
                can_move_articles BOOLEAN DEFAULT FALSE,
                can_delete_articles BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Table commandes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commandes (
                id SERIAL PRIMARY KEY,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                contremaître VARCHAR(100),
                equipe VARCHAR(50),
                articles_json TEXT,
                total_prix DECIMAL(10,2),
                nb_articles INTEGER,
                user_id INTEGER
            )
        """)
        
        # Table de persistance du panier
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_cart_sessions (
                user_id INTEGER PRIMARY KEY,
                cart_json TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table de sessions utilisateur (pour éviter les déconnexions intempestives)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                session_token VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '60 minutes')
            )
        """)
        
        # Table catalogue articles (persistance Railway)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id SERIAL PRIMARY KEY,
                reference VARCHAR(50) NOT NULL,
                nom VARCHAR(255) NOT NULL,
                description VARCHAR(255),
                prix DECIMAL(10,2) NOT NULL,
                unitee VARCHAR(50),
                UNIQUE(reference)
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Appeler la migration des permissions après création de la table
        migrate_database()
        # Migrer articles CSV -> PostgreSQL si table vide
        migrate_articles_csv_to_postgres()
        
    except Exception as e:
        st.error(f"Erreur initialisation base: {e}")

def migrate_articles_csv_to_postgres():
    """Migre les articles du CSV vers PostgreSQL si la table est vide (1ère fois)"""
    if not USE_POSTGRESQL:
        return
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return  # Déjà migré
        if not os.path.isfile(ARTICLES_CSV_PATH):
            conn.close()
            return
        df = pd.read_csv(ARTICLES_CSV_PATH, encoding='utf-8', usecols=[0, 1, 2, 3, 4])
        df.columns = ['N° Référence', 'Nom', 'Description', 'Prix', 'Unitée']
        df = df.dropna(subset=['Prix'])
        df['Prix'] = pd.to_numeric(df['Prix'], errors='coerce')
        df = df.dropna(subset=['Prix'])
        for _, row in df.iterrows():
            try:
                ref = str(row['N° Référence'])
                nom = str(row['Nom'])
                desc = str(row.get('Description', '') or '')
                prix = float(row['Prix'])
                unitee = str(row.get('Unitée', 'Par unité') or 'Par unité')
                cursor.execute(
                    "INSERT INTO articles (reference, nom, description, prix, unitee) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (reference) DO NOTHING",
                    (ref, nom, desc, prix, unitee)
                )
            except Exception:
                pass
        conn.commit()
        conn.close()
    except Exception:
        pass

def save_commande_to_db(commande_data):
    """Sauvegarde une commande en base de données"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
        
        articles_json = json.dumps(commande_data['articles'], ensure_ascii=False, default=str)
        date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        nb_articles = len(commande_data['articles'])
        
        if USE_POSTGRESQL:
            cursor.execute('''
                INSERT INTO commandes (date, contremaître, equipe, articles_json, total_prix, nb_articles, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            ''', (date_now, commande_data['utilisateur'], commande_data['equipe'], 
                  articles_json, commande_data['total'], nb_articles, commande_data['user_id']))
            commande_id = cursor.fetchone()[0]
        else:
            cursor.execute('''
                INSERT INTO commandes (date, contremaître, equipe, articles_json, total_prix, nb_articles, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (date_now, commande_data['utilisateur'], commande_data['equipe'], 
                  articles_json, commande_data['total'], nb_articles, commande_data['user_id']))
            commande_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return commande_id
        
    except Exception as e:
        st.error(f"Erreur sauvegarde commande: {e}")
        return None

def migrate_database():
    """Ajoute les nouvelles colonnes si elles n'existent pas"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Ajouter les colonnes de permissions si elles n'existent pas
            permissions_columns = [
                ('can_add_articles', 'BOOLEAN DEFAULT FALSE'),
                ('can_view_stats', 'BOOLEAN DEFAULT FALSE'),
                ('can_view_all_orders', 'BOOLEAN DEFAULT FALSE'),
                ('can_move_articles', 'BOOLEAN DEFAULT FALSE'),
                ('can_delete_articles', 'BOOLEAN DEFAULT FALSE')
            ]
            
            for column_name, column_type in permissions_columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                    conn.commit()
                except Exception as e:
                    pass  # La colonne existe déjà
                    
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Vérifier quelles colonnes existent
            cursor.execute("PRAGMA table_info(users)")
            existing_columns = [column[1] for column in cursor.fetchall()]
            
            # Ajouter les colonnes manquantes
            new_columns = [
                ('can_add_articles', 'INTEGER DEFAULT 0'),
                ('can_view_stats', 'INTEGER DEFAULT 0'),
                ('can_view_all_orders', 'INTEGER DEFAULT 0'),
                ('can_move_articles', 'INTEGER DEFAULT 0'),
                ('can_delete_articles', 'INTEGER DEFAULT 0')
            ]
            
            for column_name, column_type in new_columns:
                if column_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                    conn.commit()
        
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur migration base de données: {e}")

def migrate_add_couleur_column():
    """Ajoute la colonne couleur_preferee si elle n'existe pas"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS couleur_preferee VARCHAR(30)
            """)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            # Vérifier si la colonne existe
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'couleur_preferee' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN couleur_preferee TEXT")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        # Ignorer les erreurs si la colonne existe déjà
        pass

def migrate_add_user_id_column():
    """Ajoute la colonne user_id si elle n'existe pas"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                ALTER TABLE commandes 
                ADD COLUMN IF NOT EXISTS user_id INTEGER
            """)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            # Vérifier si la colonne existe
            cursor.execute("PRAGMA table_info(commandes)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                cursor.execute("ALTER TABLE commandes ADD COLUMN user_id INTEGER")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        # Ignorer les erreurs si la colonne existe déjà
        pass

def migrate_add_commande_tracking():
    """Ajoute les colonnes de suivi des commandes si elles n'existent pas"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Ajouter les colonnes de suivi
            tracking_columns = [
                ("statut", "VARCHAR(50) DEFAULT 'En attente'"),
                ("traitee_par", "VARCHAR(100)"),
                ("date_traitement", "TIMESTAMP"),
                ("commentaire_technicien", "TEXT"),
                ("date_livraison_prevue", "DATE"),
                ("urgence", "VARCHAR(20) DEFAULT 'Normal'")
            ]
            
            for column_name, column_type in tracking_columns:
                try:
                    cursor.execute(f"ALTER TABLE commandes ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                    conn.commit()
                except Exception:
                    pass  # La colonne existe déjà
                    
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Vérifier quelles colonnes existent
            cursor.execute("PRAGMA table_info(commandes)")
            existing_columns = [column[1] for column in cursor.fetchall()]
            
            # Ajouter les colonnes manquantes
            new_columns = [
                ('statut', 'TEXT DEFAULT "En attente"'),
                ('traitee_par', 'TEXT'),
                ('date_traitement', 'TEXT'),
                ('commentaire_technicien', 'TEXT'),
                ('date_livraison_prevue', 'TEXT'),
                ('urgence', 'TEXT DEFAULT "Normal"')
            ]
            
            for column_name, column_type in new_columns:
                if column_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE commandes ADD COLUMN {column_name} {column_type}")
                    conn.commit()
        
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur migration suivi commandes: {e}")

# Appeler la migration au démarrage
migrate_add_commande_tracking()

# === GESTION UTILISATEURS ===
def init_users_db():
    """Initialise l'utilisateur admin par défaut"""
    try:
        # Le mot de passe admin vient de la variable d'environnement ADMIN_PASSWORD
        # (à définir dans Railway). Le fallback "admin123" ne sert qu'en local.
        admin_env_password = os.environ.get("ADMIN_PASSWORD", "")
        admin_password = hashlib.sha256((admin_env_password or "admin123").encode()).hexdigest()
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Vérifier si admin existe
        cursor.execute("SELECT id, password_hash FROM users WHERE username = %s", ("admin",))
        admin_row = cursor.fetchone()
        if not admin_row:
            # Créer l'admin
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, equipe, fonction, 
                                 couleur_preferee, can_add_articles, can_view_stats, can_view_all_orders,
                                 can_move_articles, can_delete_articles) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ("admin", admin_password, "admin", "DIRECTION", "Administrateur", 
                  "DT770", True, True, True, True, True))
        elif admin_env_password and admin_row[1] != admin_password:
            # Synchroniser le hash avec ADMIN_PASSWORD si elle a changé
            cursor.execute("UPDATE users SET password_hash = %s WHERE username = %s",
                           (admin_password, "admin"))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur initialisation admin: {e}")

def authenticate_user(username, password):
    """Renvoie le dict utilisateur si les identifiants sont valides, sinon None"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, password_hash, role, equipe, fonction, 
                   can_add_articles, can_view_stats, can_view_all_orders,
                   can_move_articles, can_delete_articles
            FROM users WHERE username = %s
        """, (username,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        (uid, user, pwd_hash, role, equipe, fonction, c_add, c_stats, c_all, c_move, c_delete) = row
        
        # Vérification du mot de passe hashé
        if pwd_hash and hashlib.sha256(password.encode()).hexdigest() == pwd_hash:
            return {
                "id": uid,
                "username": user,
                "role": role,
                "equipe": equipe,
                "fonction": fonction,
                "can_add_articles": bool(c_add),
                "can_view_stats": bool(c_stats),
                "can_view_all_orders": bool(c_all),
                "can_move_articles": bool(c_move),
                "can_delete_articles": bool(c_delete)
            }
        return None
        
    except Exception as e:
        st.error(f"Erreur authentification: {e}")
        return None

def create_session_token(user_id):
    """Crée un token de session unique pour l'utilisateur"""
    import uuid
    token = str(uuid.uuid4())
    
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            # Supprimer les anciennes sessions de cet utilisateur
            cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
            # Créer une nouvelle session avec expiration 60 minutes
            cursor.execute("""
                INSERT INTO user_sessions (user_id, session_token, expires_at) 
                VALUES (%s, %s, CURRENT_TIMESTAMP + INTERVAL '60 minutes')
            """, (user_id, token))
            conn.commit()
            conn.close()
            return token
    except Exception as e:
        st.error(f"Erreur création session: {e}")
    return None

def validate_session_token(user_id, token):
    """Valide et prolonge un token de session si valide"""
    try:
        if USE_POSTGRESQL and token:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            # Vérifier si le token existe et n'est pas expiré
            cursor.execute("""
                SELECT user_id FROM user_sessions 
                WHERE user_id = %s AND session_token = %s AND expires_at > CURRENT_TIMESTAMP
            """, (user_id, token))
            result = cursor.fetchone()
            
            if result:
                # Prolonger la session de 60 minutes
                cursor.execute("""
                    UPDATE user_sessions 
                    SET last_activity = CURRENT_TIMESTAMP, 
                        expires_at = CURRENT_TIMESTAMP + INTERVAL '60 minutes'
                    WHERE user_id = %s AND session_token = %s
                """, (user_id, token))
                conn.commit()
                conn.close()
                return True
            
            conn.close()
    except Exception:
        pass
    return False

def cleanup_expired_sessions():
    """Nettoie les sessions expirées"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP")
            conn.commit()
            conn.close()
    except Exception:
        pass

def get_user_by_id(user_id):
    """Récupère un utilisateur par son ID"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, password_hash, role, equipe, fonction, 
                       can_add_articles, can_view_stats, can_view_all_orders,
                       can_move_articles, can_delete_articles
                FROM users WHERE id = %s
            """, (user_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                (uid, user, pwd_hash, role, equipe, fonction, c_add, c_stats, c_all, c_move, c_delete) = row
                return {
                    "id": uid,
                    "username": user,
                    "role": role,
                    "equipe": equipe,
                    "fonction": fonction,
                    "can_add_articles": bool(c_add),
                    "can_view_stats": bool(c_stats),
                    "can_view_all_orders": bool(c_all),
                    "can_move_articles": bool(c_move),
                    "can_delete_articles": bool(c_delete)
                }
    except Exception:
        pass
    return None

def add_user(username, password, role='user', equipe='', fonction='', email=''):
    """Ajoute un nouvel utilisateur"""
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, equipe, fonction, email)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, password_hash, role, equipe, fonction, email))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password, role, equipe, fonction, email)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, password_hash, role, equipe, fonction, email))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Erreur ajout utilisateur: {e}")
        return False

# === FONCTIONS PANIER ===
def convert_pandas_to_dict(article):
    """Convertit une série pandas en dictionnaire"""
    return {
        'Nom': str(article['Nom']),
        'Prix': float(article['Prix']),
        'Description': str(article['Description'])
    }

def _normalize_article(item: object) -> dict | None:
    """Convertit un élément du panier en dict {Nom, Prix, Description} si possible."""
    try:
        if isinstance(item, dict):
            if 'Prix' in item and 'Nom' in item:
                # S'assure des bons types
                item['Nom'] = str(item['Nom'])
                item['Prix'] = float(item['Prix'])
                if 'Description' in item:
                    item['Description'] = str(item['Description'])
                return item
            # Certains formats {nom, prix}
            if 'prix' in item and 'nom' in item:
                return {
                    'Nom': str(item['nom']),
                    'Prix': float(item['prix']),
                    'Description': str(item.get('description', '')),
                }
        elif isinstance(item, str):
            # Essaye de décoder JSON
            import json as _json
            decoded = _json.loads(item)
            return _normalize_article(decoded)
    except Exception:
        return None
    return None

def _normalize_cart(cart_obj: object) -> list[dict]:
    """Normalise la liste du panier pour garantir une liste de dicts attendue par l'UI."""
    import json as _json
    normalized: list[dict] = []
    try:
        if isinstance(cart_obj, str):
            cart_obj = _json.loads(cart_obj)
        if isinstance(cart_obj, list):
            for it in cart_obj:
                art = _normalize_article(it)
                if art is not None:
                    normalized.append(art)
    except Exception:
        pass
    return normalized

def ensure_cart_normalized() -> None:
    """Met à jour st.session_state.cart en liste d'articles normalisés."""
    cart_obj = st.session_state.get('cart', [])
    st.session_state.cart = _normalize_cart(cart_obj)

def calculate_cart_total():
    """Calcule le total du panier en normalisant la structure si besoin."""
    ensure_cart_normalized()
    return sum(float(item.get('Prix', 0)) for item in st.session_state.cart if isinstance(item, dict))

def get_last_order_articles(username):
    """Récupère les articles de la dernière commande de l'utilisateur"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT articles_json FROM commandes 
                WHERE contremaître = %s 
                ORDER BY date DESC LIMIT 1
            """, (username,))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT articles_json FROM commandes 
                WHERE contremaître = ? 
                ORDER BY date DESC LIMIT 1
            """, (username,))
        row = cursor.fetchone()
        conn.close()
        if not row or not row[0]:
            return None
        articles = json.loads(row[0])
        return articles if isinstance(articles, list) else [articles]
    except Exception:
        return None

def repeat_last_order():
    """Remplit le panier avec la dernière commande de l'utilisateur. Retourne (success, nb_articles, message)"""
    user = st.session_state.get('current_user', {})
    username = user.get('username')
    if not username:
        return False, 0, "Non connecté"
    articles = get_last_order_articles(username)
    if not articles:
        return False, 0, "Aucune commande précédente"
    nb_added = 0
    for art in articles:
        if isinstance(art, dict) and art.get('Nom'):
            if add_to_cart(art, 1):
                nb_added += 1
            else:
                break  # Budget dépassé
    return True, nb_added, f"{nb_added} article(s) ajouté(s) au panier"

def add_to_cart(article, quantity=1):
    """Ajoute un article au panier avec vérification du budget"""
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    
    # Normaliser l'article (gère pandas.Series -> dict)
    try:
        if isinstance(article, pd.Series):
            article = {
                'Nom': str(article.get('Nom', 'Article')),
                'Prix': float(article.get('Prix', 0)),
                'Description': str(article.get('Description', '')),
            }
        else:
            normalized = _normalize_article(article)
            if normalized:
                article = normalized
    except Exception:
        pass
    
    # Calculer le nouveau total si on ajoute l'article
    current_total = calculate_cart_total()
    article_price = float(article['Prix']) * quantity
    nouveau_total = current_total + article_price
    
    # Vérifier le budget
    if nouveau_total > MAX_CART_AMOUNT:
        depassement = nouveau_total - MAX_CART_AMOUNT
        
        # Messages d'erreur marrants pour dépassement budget
        messages_budget = [
            "🚨 Holà ! Votre portefeuille crie au secours !",
            "💸 Budget explosé ! Votre banquier va pleurer !",
            "🔥 Attention ! Vous brûlez votre budget !",
            "⚠️ Stop ! Vous dépassez la limite autorisée !",
            "💰 Budget dépassé ! Retirez quelques articles !",
            "🚫 Impossible ! Vous voulez ruiner l'entreprise ?",
            "📊 Erreur 1500€ ! Budget maximum atteint !",
            "🛑 Frein d'urgence ! Budget dépassé !"
        ]
        
        # Stocker l'erreur avec timestamp pour animation
        st.session_state.budget_error = {
            'message': random.choice(messages_budget),
            'details': f"Impossible d'ajouter {article['Nom']}",
            'budget_max': MAX_CART_AMOUNT,
            'nouveau_total': nouveau_total,
            'depassement': depassement,
            'timestamp': time.time()
        }
        
        # Afficher l'erreur immédiatement
        st.error(f"🚨 {st.session_state.budget_error['message']}")
        st.error(f"💰 Budget maximum: {MAX_CART_AMOUNT:.2f}€")
        st.error(f"📊 Total actuel: {current_total:.2f}€")
        st.error(f"➕ Article à ajouter: {article_price:.2f}€")
        st.error(f"🔥 Nouveau total: {nouveau_total:.2f}€")
        st.error(f"⚠️ Dépassement: {depassement:.2f}€")
        
        return False
    
    # Ajouter l'article si le budget le permet
    for _ in range(quantity):
        st.session_state.cart.append(article)
    
    # Sauvegarde panier (prod)
    user = st.session_state.get('current_user') or {}
    if user.get('id'):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cart_json = json.dumps(st.session_state.cart, ensure_ascii=False, default=str)
            cursor.execute("DELETE FROM user_cart_sessions WHERE user_id = %s", (user['id'],))
            cursor.execute("INSERT INTO user_cart_sessions (user_id, cart_json) VALUES (%s, %s)", (user['id'], cart_json))
            conn.commit()
            conn.close()
        except Exception:
            pass
    # Sauvegarde locale
    try:
        with open('temp_session.json', 'w', encoding='utf-8') as f:
            json.dump({
                'user': st.session_state.get('current_user'),
                'page': st.session_state.get('page', 'catalogue'),
                'cart': st.session_state.get('cart', [])
            }, f, ensure_ascii=False)
    except Exception:
        pass
    
    # Messages de succès marrants
    messages_succes = [
        f"✅ {article['Nom']} ajouté ! Votre équipe sera ravie !",
        f"🎯 Excellent choix ! {article['Nom']} dans le panier !",
        f"⭐ {article['Nom']} ajouté avec style !",
        f"🚀 Mission accomplie ! {article['Nom']} embarqué !",
        f"🛡️ {article['Nom']} rejoint votre arsenal !"
    ]
    
    st.success(random.choice(messages_succes))
    return True

def grouper_articles_panier(cart):
    """Groupe les articles du panier par nom"""
    grouped = {}
    
    for article in cart:
        nom = article['Nom']
        if nom in grouped:
            grouped[nom]['quantite'] += 1
        else:
            grouped[nom] = {
                'article': article,
                'quantite': 1
            }
    
    return list(grouped.values())

def remove_from_cart(article):
    """Retire un article du panier"""
    for i, item in enumerate(st.session_state.cart):
        if item['Nom'] == article['Nom']:
            st.session_state.cart.pop(i)
            # Sauvegarde panier (prod)
            user = st.session_state.get('current_user') or {}
            if user.get('id'):
                try:
                    conn = psycopg2.connect(DATABASE_URL)
                    cursor = conn.cursor()
                    cart_json = json.dumps(st.session_state.cart, ensure_ascii=False, default=str)
                    cursor.execute("DELETE FROM user_cart_sessions WHERE user_id = %s", (user['id'],))
                    cursor.execute("INSERT INTO user_cart_sessions (user_id, cart_json) VALUES (%s, %s)", (user['id'], cart_json))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
            break
    # Sauvegarde locale
    try:
        with open('temp_session.json', 'w', encoding='utf-8') as f:
            json.dump({
                'user': st.session_state.get('current_user'),
                'page': st.session_state.get('page', 'catalogue'),
                'cart': st.session_state.get('cart', [])
            }, f, ensure_ascii=False)
    except Exception:
        pass

def remove_all_from_cart(article):
    """Retire tous les exemplaires d'un article du panier"""
    st.session_state.cart = [item for item in st.session_state.cart if item['Nom'] != article['Nom']]
    # Sauvegarde panier (prod)
    user = st.session_state.get('current_user') or {}
    if user.get('id'):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cart_json = json.dumps(st.session_state.cart, ensure_ascii=False, default=str)
            cursor.execute("DELETE FROM user_cart_sessions WHERE user_id = %s", (user['id'],))
            cursor.execute("INSERT INTO user_cart_sessions (user_id, cart_json) VALUES (%s, %s)", (user['id'], cart_json))
            conn.commit()
            conn.close()
        except Exception:
            pass
    # Sauvegarde locale
    try:
        with open('temp_session.json', 'w', encoding='utf-8') as f:
            json.dump({
                'user': st.session_state.get('current_user'),
                'page': st.session_state.get('page', 'catalogue'),
                'cart': st.session_state.get('cart', [])
            }, f, ensure_ascii=False)
    except Exception:
        pass

# === FONCTIONS INTERFACE ===
def init_session_state():
    """Initialise les variables de session"""
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    else:
        try:
            ensure_cart_normalized()
        except Exception:
            st.session_state.cart = []
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    if 'budget_error' not in st.session_state:
        st.session_state.budget_error = None
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = None
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None

    # Nettoyage des sessions expirées
    cleanup_expired_sessions()
    
    # Restauration de session sécurisée (si token valide dans les 5 dernières minutes)
    if not st.session_state.get('authenticated') and USE_POSTGRESQL:
        # Vérifier s'il y a un token de session valide dans les cookies/query params
        try:
            # Streamlit ne permet pas l'accès direct aux cookies, mais on peut utiliser les query params
            query_params = st.query_params
            session_token = query_params.get('session_token')
            user_id = query_params.get('user_id')
            
            if session_token and user_id:
                user_id = int(user_id)
                if validate_session_token(user_id, session_token):
                    # Restaurer l'utilisateur depuis la base
                    user = get_user_by_id(user_id)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = user
                        st.session_state.session_token = session_token
                        st.session_state.page = "catalogue"
                        
                        # Charger le panier sauvegardé
                        try:
                            conn = psycopg2.connect(DATABASE_URL)
                            cursor = conn.cursor()
                            cursor.execute("SELECT cart_json FROM user_cart_sessions WHERE user_id = %s", (user_id,))
                            row = cursor.fetchone()
                            conn.close()
                            if row and row[0]:
                                cart = json.loads(row[0])
                                st.session_state.cart = _normalize_cart(cart)
                        except Exception:
                            pass
        except Exception:
            pass
    
    # Supprimer les fichiers de session locaux (sécurité)
    try:
        if os.path.exists('temp_session.json'):
            os.remove('temp_session.json')
    except Exception:
        pass

def show_budget_error_modal():
    """Affiche les erreurs de budget avec animation"""
    if st.session_state.budget_error:
        error = st.session_state.budget_error
        
        # Vérifier si l'erreur n'est pas trop ancienne (5 secondes)
        if time.time() - error['timestamp'] < 5:
            st.markdown(f"""
            <div class="budget-error">
                <h3>🚨 {error['message']}</h3>
                <p><strong>Détails:</strong> {error['details']}</p>
                <p><strong>Budget maximum:</strong> {error['budget_max']:.2f}€</p>
                <p><strong>Total tenté:</strong> {error['nouveau_total']:.2f}€</p>
                <p><strong>Dépassement:</strong> {error['depassement']:.2f}€</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Effacer l'erreur si elle est trop ancienne
            st.session_state.budget_error = None

def show_cart_sidebar():
    """Affiche le panier dans la sidebar"""
    st.markdown("### 🛒 Panier FLUX/PARA")
    
    if not st.session_state.cart:
        st.info("Panier vide")
        return
    
    grouped_articles = grouper_articles_panier(st.session_state.cart)
    
    for i, group in enumerate(grouped_articles):
        article = group['article']
        quantite = group['quantite']
        prix_unitaire = float(article['Prix'])
        prix_total = prix_unitaire * quantite
        
        with st.container():
            nom_court = article['Nom'][:30] + "..." if len(article['Nom']) > 30 else article['Nom']
            st.markdown(f"**{nom_court}**")
            st.markdown(f"💰 {prix_unitaire:.2f}€ × {quantite} = **{prix_total:.2f}€**")
            
            # Clé STABLE basée sur nom/référence pour que les boutons fonctionnent correctement dans la sidebar
            ref = str(article.get('N° Référence') or article.get('Référence') or "no_ref")
            nom = str(article.get('Nom') or "no_nom")
            key_suffix = re.sub(r'[^a-zA-Z0-9_]+', '_', f"{nom}_{ref}_{i}")
            col_minus, col_qty, col_plus, col_del = st.columns([1, 1, 1, 1])
            
            with col_minus:
                if st.button("➖", key=f"sidebar_minus_{key_suffix}", help="Réduire quantité"):
                    remove_from_cart(article)
                    st.rerun()
            
            with col_qty:
                st.markdown(f"<div style='text-align: center; font-size: 14px; font-weight: bold; padding: 4px;'>{quantite}</div>", unsafe_allow_html=True)
            
            with col_plus:
                if st.button("➕", key=f"sidebar_plus_{key_suffix}", help="Augmenter quantité"):
                    add_to_cart(article, 1)
                    st.rerun()
            
            with col_del:
                if st.button("🗑️", key=f"sidebar_delete_{key_suffix}", help="Supprimer"):
                    remove_all_from_cart(article)
                    st.rerun()
            
            st.divider()
    
    total = calculate_cart_total()
    budget_remaining = MAX_CART_AMOUNT - total
    
    if budget_remaining >= 0:
        st.success(f"💰 **Total: {total:.2f}€**")
        st.info(f"Budget restant: {budget_remaining:.2f}€")
    else:
        st.error(f"💰 **Total: {total:.2f}€**")
        st.error(f"Dépassement: {abs(budget_remaining):.2f}€")
    
    if st.button("🛒 Voir le panier", key="sidebar_view_cart_btn", use_container_width=True):
        st.session_state.page = "cart"
        st.rerun()
    
    if budget_remaining >= 0:
        if st.button("✅ Valider commande", key="sidebar_validate_order_btn", use_container_width=True):
            st.session_state.page = "validation"
            st.rerun()
    else:
        st.button("❌ Budget dépassé", key="sidebar_budget_exceeded_btn", disabled=True, use_container_width=True)

def show_login():
    """Page de connexion avec messages marrants"""
    st.markdown("### 🛡️ Connexion FLUX/PARA")
    
    # Messages marrants aléatoires
    messages_marrants = [
        "🎯 Prêt à équiper votre équipe comme un chef ?",
        "⚡ Connectez-vous pour accéder au meilleur matériel !",
        "🚀 Votre mission : équiper, protéger, réussir !",
        "🛡️ Sécurité d'abord, style ensuite !",
        "💪 Ensemble, on équipe mieux !",
        "🎪 Bienvenue dans le cirque... euh, l'entrepôt !",
        "🦸‍♂️ Transformez-vous en super-contremaître !",
        "🎲 Tentez votre chance... de bien vous équiper !"
    ]
    
    message_du_jour = random.choice(messages_marrants)
    st.info(message_du_jour)
    
    with st.form("login_form"):
        username = st.text_input("👤 Nom d'utilisateur")
        password = st.text_input("🔑 Mot de passe", type="password")
        login_button = st.form_submit_button("🔐 Se connecter", use_container_width=True)
        if login_button:
            if username and password:
                user = authenticate_user(username, password)
                if user:
                    # Vérifier si le mot de passe doit être changé
                    try:
                        conn = psycopg2.connect(DATABASE_URL)
                        cursor = conn.cursor()
                        cursor.execute("SELECT must_change_password FROM users WHERE username = %s", (username,))
                        res = cursor.fetchone()
                        conn.close()
                        must_change = res[0] if res else False
                    except Exception:
                        must_change = False
                    st.session_state.authenticated = True
                    st.session_state.current_user  = user
                    st.session_state.current_user['must_change_password'] = must_change
                    
                    # Créer un token de session pour éviter les déconnexions intempestives
                    session_token = create_session_token(user['id'])
                    if session_token:
                        st.session_state.session_token = session_token
                    
                    # Charger le panier sauvegardé (prod)
                    try:
                        conn = psycopg2.connect(DATABASE_URL)
                        cursor = conn.cursor()
                        cursor.execute("SELECT cart_json FROM user_cart_sessions WHERE user_id = %s", (user['id'],))
                        row = cursor.fetchone()
                        conn.close()
                        if row and row[0]:
                            cart = json.loads(row[0])
                            st.session_state.cart = _normalize_cart(cart)
                    except Exception:
                        pass
                    if must_change:
                        st.session_state.page = 'force_change_password'
                        st.rerun()
                    else:
                        st.session_state.page = "catalogue"
                        # Sauvegarde session locale pour persister au refresh en local
                        try:
                            with open('temp_session.json', 'w', encoding='utf-8') as f:
                                json.dump({
                                    'user': user,
                                    'page': st.session_state.page,
                                    'cart': st.session_state.cart
                                }, f, ensure_ascii=False)
                        except Exception:
                            pass
                        st.rerun()
                else:
                    st.error("Hmm… Ces identifiants ne me disent rien !")
            else:
                st.error("❌ Veuillez remplir tous les champs")
    
    if st.button("🔑 Mot de passe oublié ?", use_container_width=True):
        st.session_state.page = 'reset_password'
        st.rerun()

def show_register():
    """Page d'inscription avec rôles prédéfinis"""
    st.markdown("### 📝 Inscription - Nouveau compte FLUX/PARA")
    
    with st.form("register_form"):
        st.markdown("🛡️ **Rejoignez l'équipe FLUX/PARA !**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("👤 Nom d'utilisateur*", placeholder="votre.nom")
            password = st.text_input("🔒 Mot de passe*", type="password", help="Minimum 6 caractères")
            confirm_password = st.text_input("🔒 Confirmer le mot de passe*", type="password")
            
            # Sélection d'équipe
            equipes = ["DIRECTION", "FLUX", "PARA", "MAINTENANCE", "QUALITE", "LOGISTIQUE"]
            equipe = st.selectbox("👥 Équipe*", ["Sélectionnez..."] + equipes)
        
        with col2:
            # NOUVEAU: Menu déroulant avec rôles prédéfinis
            fonctions_predefinies = [
                "CONTREMAÎTRE", 
                "RTZ", 
                "GESTIONNAIRE",
                "OPÉRATEUR",
                "TECHNICIEN",
                "RESPONSABLE SÉCURITÉ",
                "CHEF D'ÉQUIPE",
                "AGENT QUALITÉ",
                "LOGISTICIEN",
                "AUTRE"
            ]
            
            fonction = st.selectbox("💼 Fonction/Poste*", 
                                  ["Sélectionnez votre poste..."] + fonctions_predefinies)
            
            # Si "AUTRE" est sélectionné, permettre la saisie libre
            if fonction == "AUTRE":
                fonction_custom = st.text_input("✏️ Précisez votre fonction:", placeholder="Ex: Apprenti, Stagiaire...")
                fonction = fonction_custom if fonction_custom else fonction
            
            couleur_preferee = st.text_input("🎨 Couleur préférée*", 
                                           placeholder="Ex: bleu, rouge, vert...",
                                           help="Question de sécurité pour récupérer votre mot de passe")
        
        st.markdown("---")
        st.markdown("**Permissions automatiques selon le poste :**")
        
        # Affichage des permissions selon la fonction
        if fonction in ["CONTREMAÎTRE", "RTZ", "GESTIONNAIRE"]:
            st.success("🎖️ **Poste à responsabilité** - Accès étendu automatiquement accordé")
            st.info("✅ Accès aux statistiques • ✅ Consultation des commandes • ✅ Gestion articles")
        elif fonction in ["CHEF D'ÉQUIPE", "RESPONSABLE SÉCURITÉ"]:
            st.info("👨‍💼 **Encadrement** - Accès limité aux statistiques")
            st.info("✅ Accès aux statistiques • ❌ Gestion articles")
        else:
            st.info("👤 **Utilisateur standard** - Accès de base au catalogue")
        
        submitted = st.form_submit_button("🚀 Créer mon compte", use_container_width=True)
        
        if submitted:
            # Validation avec les nouveaux champs
            if not all([username, password, confirm_password, fonction != "Sélectionnez votre poste...", couleur_preferee]):
                st.error("❌ Veuillez remplir tous les champs obligatoires (*)")
            elif equipe == "Sélectionnez...":
                st.error("❌ Veuillez sélectionner votre équipe")
            elif password != confirm_password:
                st.error("❌ Les mots de passe ne correspondent pas")
            elif len(password) < 6:
                st.error("❌ Le mot de passe doit contenir au moins 6 caractères")
            else:
                success, message = create_user(username, password, equipe, fonction, couleur_preferee)
                if success:
                    # Messages de succès selon la fonction
                    if fonction in ["CONTREMAÎTRE", "RTZ", "GESTIONNAIRE"]:
                        messages_succes = [
                            f"🎖️ Inscription réussie ! Bienvenue {fonction} !",
                            f"⭐ Félicitations ! Vous êtes maintenant {fonction} FLUX/PARA !",
                            f"🚀 Mission accomplie ! {fonction} activé avec succès !",
                        ]
                    else:
                        messages_succes = [
                            "🎉 Inscription réussie ! Bienvenue dans l'équipe !",
                            "⭐ Félicitations ! Vous êtes maintenant un agent FLUX/PARA !",
                            "🛡️ Bienvenue dans l'élite ! Connexion autorisée !",
                        ]
                    
                    st.success(random.choice(messages_succes))
                    
                    # Attribution automatique des permissions selon la fonction
                    assign_permissions_by_function(username, fonction)
                    
                    time.sleep(2)
                    st.session_state.page = 'login'
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    if st.button("← Retour à la connexion"):
        st.session_state.page = 'login'
        st.rerun()

def show_cart():
    """Affiche le panier complet"""
    st.markdown("### 🛒 Panier FLUX/PARA")
    
    if not st.session_state.cart:
        st.info("🛒 Votre panier est vide")
        if st.button("🛡️ Aller au catalogue"):
            st.session_state.page = "catalogue"
            st.rerun()
        return
    
    grouped_articles = grouper_articles_panier(st.session_state.cart)
    
    for group in grouped_articles:
        article = group['article']
        quantite = group['quantite']
        prix_unitaire = float(article['Prix'])
        prix_total = prix_unitaire * quantite
        
        with st.container():
            col1, col2, col3 = st.columns([4, 2, 2])
            
            with col1:
                st.markdown(f"**{article['Nom']}**")
                st.markdown(f"💰 {prix_unitaire:.2f}€ × {quantite} = **{prix_total:.2f}€**")
                
            with col2:
                st.markdown("**Quantité**")
                col_minus, col_qty, col_plus = st.columns([1, 2, 1])
                
                with col_minus:
                    if st.button("➖", key=f"minus_{article['Nom']}", use_container_width=True):
                        remove_from_cart(article)
                        st.rerun()
                
                with col_qty:
                    st.markdown(f"<div style='text-align: center; padding: 8px; background: #f0f2f6; border-radius: 4px; font-weight: bold;'>{quantite}</div>", unsafe_allow_html=True)
                
                with col_plus:
                    if st.button("➕", key=f"plus_{article['Nom']}", use_container_width=True):
                        add_to_cart(article, 1)
                        st.rerun()
                        
            with col3:
                st.markdown("**Actions**")
                if st.button("🗑️", key=f"delete_{article['Nom']}", help="Supprimer tout", use_container_width=True):
                    remove_all_from_cart(article)
                    st.rerun()
            
            st.divider()
    
    total = calculate_cart_total()
    budget_remaining = MAX_CART_AMOUNT - total
    
    if budget_remaining >= 0:
        st.success(f"### 💰 Total: {total:.2f}€")
        st.info(f"💡 Budget restant: {budget_remaining:.2f}€")
    else:
        st.error(f"### 💰 Total: {total:.2f}€")
        st.error(f"🚨 Dépassement budget: {abs(budget_remaining):.2f}€")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🛡️ Continuer mes achats", use_container_width=True):
            st.session_state.page = "catalogue"
            st.rerun()
    
    with col2:
        if st.button("🗑️ Vider le panier", use_container_width=True):
            st.session_state.cart = []
            st.toast("🗑️ Panier vidé !", icon="✅")
            st.rerun()
    
    with col3:
        if budget_remaining >= 0:
            if st.button("✅ Valider la commande", use_container_width=True):
                st.session_state.page = "validation"
                st.rerun()
        else:
            st.button("❌ Budget dépassé", disabled=True, use_container_width=True)
    
    # === SUGGESTIONS IA DANS LE PANIER ===
    user_id = st.session_state.get('current_user', {}).get('id')
    if user_id and st.session_state.cart:
        st.markdown("---")
        
        # Suggestions basées sur le panier actuel
        show_ai_suggestions_panel(user_id, st.session_state.cart)
        
        # Détection de doublons dans le panier
        # Détection de doublons supprimée (fonctionnalité gênante)
        
        # Recommandations contextuelles basées sur le dernier article ajouté
        if st.session_state.cart:
            last_article = st.session_state.cart[-1]
            recommendations = get_contextual_recommendations(last_article)
            
            if recommendations:
                st.markdown("### 💡 Compléments recommandés")
                st.markdown(f"*Basé sur votre dernier ajout: {last_article.get('Nom', '')[:30]}...*")
                
                rec_cols = st.columns(min(4, len(recommendations)))
                
                for i, rec in enumerate(recommendations[:4]):
                    with rec_cols[i]:
                        article = rec['article']
                        reason = rec['reason']
                        
                        st.markdown(f"""
                        <div style="border: 1px solid #667eea; border-radius: 10px; padding: 10px; margin: 5px 0; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));">
                            <strong>{article.get('Nom', '')[:25]}...</strong><br>
                            <small>💡 {reason}</small><br>
                            <small>💰 {article.get('Prix', 0)}€</small>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("➕", key=f"cart_rec_add_{i}_{article.get('N° Référence', '')}", 
                                   help=f"Ajouter {article.get('Nom', '')} au panier"):
                            add_to_cart(article)
                            st.success(f"✅ {article.get('Nom', '')[:20]} ajouté!")
                            st.rerun()

def generate_commande_pdf(commande_data):
    """Génère le PDF de commande pour l'utilisateur"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # En-tête
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Centré
        )
        
        story.append(Paragraph("🛡️ COMMANDE FLUX/PARA", title_style))
        story.append(Spacer(1, 20))
        
        # Informations commande
        info_data = [
            ['Date de commande:', datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Contremaître:', commande_data.get('utilisateur', 'N/A')],
            ['Équipe:', commande_data.get('equipe', 'N/A')],
            ['Fonction:', commande_data.get('fonction', 'N/A')],
            ['Date livraison souhaitée:', commande_data.get('date_livraison', 'N/A')]
        ]
        
        info_table = Table(info_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Articles commandés
        story.append(Paragraph("Articles commandés:", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        # Grouper les articles
        grouped_articles = grouper_articles_panier(commande_data['articles'])
        
        # CORRECTION: Données du tableau avec vrais N° articles du CSV
        table_data = [['N° Article', 'Article', 'Quantité', 'Prix unitaire', 'Prix total']]
        
        for group in grouped_articles:
            article = group['article']
            quantite = group['quantite']
            prix_unitaire = float(article['Prix'])
            prix_total = prix_unitaire * quantite
            
            # CORRECTION: Récupérer le vrai numéro d'article depuis le CSV
            numero_article = get_numero_article_from_csv(article['Nom'])
            
            table_data.append([
                str(numero_article),
                article['Nom'],
                str(quantite),
                f"{prix_unitaire:.2f}€",
                f"{prix_total:.2f}€"
            ])
        
        # Total
        total = commande_data['total']
        table_data.append(['', '', '', 'TOTAL:', f"{total:.2f}€"])
        
        # Créer le tableau avec 5 colonnes
        table = Table(table_data, colWidths=[1.5*inch, 3*inch, 1*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Commentaire si présent
        if commande_data.get('commentaire'):
            story.append(Spacer(1, 20))
            story.append(Paragraph("Commentaire:", styles['Heading3']))
            story.append(Paragraph(commande_data['commentaire'], styles['Normal']))
        
        # Construire le PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        st.error(f"Erreur génération PDF commande: {e}")
        return None

def generate_bon_livraison_pdf(commande_data):
    """Génère le PDF bon de livraison pour le magasin avec contrôle quantité"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # En-tête
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1
        )
        
        story.append(Paragraph("📦 BON DE LIVRAISON FLUX/PARA", title_style))
        story.append(Spacer(1, 20))
        
        # Informations livraison
        info_data = [
            ['N° Commande:', f"CMD-{commande_data['id']}"],
            ['Date commande:', datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Demandeur:', commande_data.get('utilisateur', 'N/A')],
            ['Équipe:', commande_data.get('equipe', 'N/A')],
            ['Date livraison:', commande_data.get('date_livraison', 'N/A')],
            ['Statut:', 'EN ATTENTE']
        ]
        
        info_table = Table(info_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Articles à préparer
        story.append(Paragraph("Articles à préparer:", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        # Grouper les articles
        grouped_articles = grouper_articles_panier(commande_data['articles'])
        
        # CORRECTION: Données du tableau avec vrais N° articles du CSV
        table_data = [['N° Article', 'Article', 'Qté demandée', 'Qté préparée', 'Emplacement', 'Préparé', 'Observations']]
        
        for group in grouped_articles:
            article = group['article']
            quantite = group['quantite']
            
            # CORRECTION: Récupérer le vrai numéro d'article depuis le CSV
            numero_article = get_numero_article_from_csv(article['Nom'])
            
            table_data.append([
                str(numero_article),
                article['Nom'],
                str(quantite),
                '____',  # Zone pour saisir quantité préparée
                '____',  # Emplacement à remplir
                '☐',     # Case à cocher
                '____'   # Observations
            ])
        
        # Créer le tableau avec 7 colonnes
        table = Table(table_data, colWidths=[1*inch, 2.5*inch, 0.8*inch, 0.8*inch, 1*inch, 0.6*inch, 1.3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        
        story.append(table)
        
        # Instructions pour le magasin
        story.append(Spacer(1, 30))
        story.append(Paragraph("Instructions:", styles['Heading3']))
        story.append(Paragraph("1. Vérifier la disponibilité de chaque article", styles['Normal']))
        story.append(Paragraph("2. Indiquer la quantité réellement préparée", styles['Normal']))
        story.append(Paragraph("3. Noter l'emplacement de stockage", styles['Normal']))
        story.append(Paragraph("4. Cocher la case une fois l'article préparé", styles['Normal']))
        story.append(Paragraph("5. Ajouter des observations si nécessaire", styles['Normal']))
        
        # Signature
        story.append(Spacer(1, 30))
        signature_data = [
            ['Préparé par:', '____________________', 'Date:', '____________________'],
            ['Signature:', '____________________', 'Heure:', '____________________']
        ]
        
        signature_table = Table(signature_data, colWidths=[1.5*inch, 2*inch, 1*inch, 2*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12)
        ]))
        
        story.append(signature_table)
        
        # Construire le PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        st.error(f"Erreur génération PDF bon de livraison: {e}")
        return None

def generate_bon_reception_pdf(commande_data, commande_id):
    """Génère le PDF bon de réception pour celui qui reçoit la commande"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # En-tête
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Centré
        )
        
        story.append(Paragraph("🛡️ BON DE RÉCEPTION FLUX/PARA", title_style))
        story.append(Spacer(1, 20))
        
        # Informations commande
        info_data = [
            ['N° Commande:', f"CMD-{commande_id}"],
            ['Date commande:', datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Destinataire:', commande_data.get('utilisateur', 'N/A')],
            ['Équipe:', commande_data.get('equipe', 'N/A')],
            ['Date livraison:', commande_data.get('date_livraison', 'N/A')],
            ['Statut:', 'À RÉCEPTIONNER']
        ]
        
        info_table = Table(info_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Articles à réceptionner
        story.append(Paragraph("Articles à réceptionner:", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        # Grouper les articles
        grouped_articles = grouper_articles_panier(commande_data['articles'])
        
        # Données du tableau pour réception
        table_data = [['N° Article', 'Article', 'Qté commandée', 'Qté reçue', 'État', 'Conforme', 'Observations']]
        
        for group in grouped_articles:
            article = group['article']
            quantite = group['quantite']
            
            # Récupérer le vrai numéro d'article depuis le CSV
            numero_article = get_numero_article_from_csv(article['Nom'])
            
            table_data.append([
                str(numero_article),
                article['Nom'],
                str(quantite),
                '____',  # Zone pour saisir quantité reçue
                '____',  # État de l'article (Bon/Défaut)
                '☐',     # CORRECTION: Case à cocher plus visible
                '____'   # Observations
            ])
        
        # Créer le tableau avec 7 colonnes
        table = Table(table_data, colWidths=[1*inch, 2.5*inch, 0.8*inch, 0.8*inch, 1*inch, 0.6*inch, 1.3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            # CORRECTION: Style spécial pour les cases à cocher
            ('FONTSIZE', (5, 1), (5, -1), 14),  # Colonne "Conforme" plus grande
            ('FONTNAME', (5, 1), (5, -1), 'Helvetica-Bold')  # Cases en gras
        ]))
        
        story.append(table)
        
        # Instructions pour la réception
        story.append(Spacer(1, 30))
        story.append(Paragraph("Instructions de réception:", styles['Heading3']))
        story.append(Paragraph("1. Vérifier que tous les articles commandés sont présents", styles['Normal']))
        story.append(Paragraph("2. Contrôler l'état de chaque article (défauts, dommages)", styles['Normal']))
        story.append(Paragraph("3. Indiquer la quantité réellement reçue", styles['Normal']))
        story.append(Paragraph("4. Noter l'état : BON / DÉFAUT / MANQUANT", styles['Normal']))
        story.append(Paragraph("5. Cocher 'Conforme' si l'article est acceptable", styles['Normal']))
        story.append(Paragraph("6. Signaler tout problème dans les observations", styles['Normal']))
        
        # Section validation réception
        story.append(Spacer(1, 30))
        story.append(Paragraph("Validation de la réception:", styles['Heading3']))
        
        validation_data = [
            ['Réceptionné par:', '____________________', 'Date:', '____________________'],
            ['Fonction:', '____________________', 'Heure:', '____________________'],
            ['Signature:', '____________________', 'Livraison complète:', '☐ OUI    ☐ NON'],  # CORRECTION: Cases plus espacées
            ['Observations générales:', '', '', ''],
            ['', '', '', ''],
            ['', '', '', '']
        ]
        
        validation_table = Table(validation_data, colWidths=[1.5*inch, 2*inch, 1*inch, 2*inch])
        validation_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('SPAN', (1, 3), (3, 5)),  # Fusionner cellules pour observations
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # CORRECTION: Style pour les cases OUI/NON
            ('FONTSIZE', (3, 2), (3, 2), 12),  # Cases OUI/NON plus grandes
            ('FONTNAME', (3, 2), (3, 2), 'Helvetica-Bold')
        ]))
        
        story.append(validation_table)
        
        # Construire le PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        st.error(f"Erreur génération PDF bon de réception: {e}")
        return None

def get_numero_article_from_csv(nom_article):
    """Récupère le numéro d'article depuis le CSV en fonction du nom"""
    try:
        # Charger le CSV si pas déjà fait
        if articles_df.empty:
            return "N/A"
        
        # Chercher l'article par nom exact
        article_row = articles_df[articles_df['Nom'] == nom_article]
        
        if not article_row.empty:
            # CORRECTION: Récupérer la première colonne qui contient les références (40953, 40954, etc.)
            premiere_colonne = articles_df.columns[0]  # 'Référence' dans votre cas
            numero = article_row.iloc[0][premiere_colonne]
            return str(numero) if pd.notna(numero) else "N/A"
        else:
            return "N/A"
            
    except Exception as e:
        print(f"Erreur récupération numéro article: {e}")
        return "N/A"

def show_validation():
    """Page de validation de commande avec message fixe pour PDFs"""
    st.markdown("### ✅ Validation commande FLUX/PARA")
    
    if not st.session_state.cart:
        st.warning("🛒 Votre panier est vide")
        if st.button("← Retour au catalogue"):
            st.session_state.page = "catalogue"
            st.rerun()
        return
    
    user_info = st.session_state.get('current_user', {})
    
    # Informations personnelles (non modifiables)
    st.markdown("### 👤 Informations personnelles")
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("👤 Contremaître", value=user_info.get('username', ''), disabled=True)
        st.text_input("👷‍♂️ Équipe", value=user_info.get('equipe', ''), disabled=True)
    
    with col2:
        st.text_input("🔧 Fonction", value=user_info.get('fonction', ''), disabled=True)
    
    # Informations commande
    st.markdown("### 📋 Informations commande")
    col1, col2 = st.columns(2)
    
    with col1:
        commentaire_commande = st.text_area(
            "💬 Commentaire de commande (optionnel)",
            placeholder="Précisions sur la commande, urgence, etc.",
            key="commentaire_validation"  # Clé unique pour éviter les conflits
        )
    
    with col2:
        date_livraison = st.date_input(
            "📅 Date de livraison souhaitée",
            value=datetime.now().date() + timedelta(days=7),
            min_value=datetime.now().date(),
            key="date_livraison_validation"  # Clé unique
        )
    
    # Récapitulatif de la commande
    st.markdown("### 📋 Récapitulatif de la commande")
    
    grouped_articles = grouper_articles_panier(st.session_state.cart)
    total = 0
    
    for group in grouped_articles:
        article = group['article']
        quantite = group['quantite']
        prix_unitaire = float(article['Prix'])
        prix_total = prix_unitaire * quantite
        total += prix_total
        
        st.markdown(f"• **{article['Nom']}** - {quantite}x - {prix_total:.2f}€")
    
    st.markdown(f"### 💰 Total: {total:.2f}€")
    
    # Boutons d'action
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("← Retour au panier", use_container_width=True):
            st.session_state.page = "cart"
            st.rerun()
    
    with col2:
        if st.button("🗑️ Vider panier", use_container_width=True):
            st.session_state.cart = []
            st.session_state.page = "catalogue"
            st.rerun()
    
    with col3:
        if st.button("✅ Confirmer la commande", use_container_width=True, type="primary"):
            if not user_info.get('username'):
                st.error("❌ Erreur: utilisateur non connecté")
                return
            
            # Préparer les données de commande
            commande_data = {
                'utilisateur': user_info.get('username', 'Inconnu'),
                'equipe': user_info.get('equipe', ''),
                'fonction': user_info.get('fonction', ''),
                'email': user_info.get('email', ''),
                'commentaire': commentaire_commande,
                'date_livraison': str(date_livraison),
                'articles': st.session_state.cart.copy(),
                'total': total,
                'user_id': st.session_state.current_user['id']
            }
            
            # Afficher le spinner pendant le traitement
            with st.spinner('🔄 Traitement de la commande...'):
                # 1. Sauvegarder en base de données
                commande_id = save_commande_to_db(commande_data)
                
                if commande_id:
                    # 2. Générer les PDFs
                    pdf_commande = generate_commande_pdf(commande_data)
                    pdf_reception = generate_bon_reception_pdf(commande_data, commande_id)
                    
                    if pdf_commande and pdf_reception:
                        # CORRECTION: Stocker les PDFs dans session_state
                        st.session_state.pdf_commande = pdf_commande
                        st.session_state.pdf_reception = pdf_reception
                        st.session_state.commande_id = commande_id
                        st.session_state.pdfs_generated = True
                        
                        st.success("🎉 Commande validée avec succès !")
                        st.balloons()
                        
                        # CORRECTION: Forcer le rechargement de la page
                        time.sleep(1)  # Petit délai pour voir le message de succès
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la génération des PDFs")
                else:
                    st.error("❌ Erreur lors de la sauvegarde")
    
    # CORRECTION: Afficher les boutons de téléchargement de manière persistante
    if st.session_state.get('pdfs_generated', False):
        st.markdown("---")
        st.markdown("### 📄 Télécharger vos documents")
        
        col_pdf1, col_pdf2 = st.columns(2)
        
        with col_pdf1:
            if 'pdf_commande' in st.session_state:
                st.download_button(
                    label="📄 Télécharger ma commande",
                    data=st.session_state.pdf_commande.getvalue(),
                    file_name=f"commande_FLUX_PARA_{st.session_state.commande_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        with col_pdf2:
            if 'pdf_reception' in st.session_state:
                st.download_button(
                    label="📦 Télécharger bon de réception",
                    data=st.session_state.pdf_reception.getvalue(),
                    file_name=f"bon_reception_FLUX_PARA_{st.session_state.commande_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        st.markdown("---")
        if st.button("✅ Terminer et vider panier", use_container_width=True, type="primary"):
            # Nettoyer et rediriger
            st.session_state.cart = []
            st.session_state.pdfs_generated = False
            if 'pdf_commande' in st.session_state:
                del st.session_state.pdf_commande
            if 'pdf_reception' in st.session_state:
                del st.session_state.pdf_reception
            if 'commande_id' in st.session_state:
                del st.session_state.commande_id
            st.session_state.page = "catalogue"
            st.rerun()

def show_mes_commandes():
    """Affiche les commandes de l'utilisateur connecté avec suivi d'état"""
    st.markdown("### 📊 Mes commandes")
    
    user_info = st.session_state.get('current_user')
    if not user_info:
        st.error("❌ Vous devez être connecté")
        return
    
    # Récupérer toutes les commandes de l'utilisateur
    orders = []
    
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, total_prix, statut, articles_json, 
                       traitee_par, date_traitement, commentaire_technicien, 
                       date_livraison_prevue, urgence
                FROM commandes 
                WHERE contremaître = %s 
                ORDER BY date DESC
            """, (user_info['username'],))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, total_prix, statut, articles_json, 
                       traitee_par, date_traitement, commentaire_technicien, 
                       date_livraison_prevue, urgence
                FROM commandes 
                WHERE contremaître = ? 
                ORDER BY date DESC
            """, (user_info['username'],))
        
        orders = cursor.fetchall()
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur chargement commandes: {e}")
        orders = []
    
    if not orders:
        st.info("📭 Aucune commande trouvée")
        
        # Messages marrants pour encourager à commander
        messages_encouragement = [
            "🛍️ Votre historique est vide ! Temps de faire du shopping !",
            "🎯 Aucune commande ? Votre équipe attend son équipement !",
            "🚀 Première mission : équiper votre équipe !",
            "⭐ Commencez votre aventure shopping sécurisé !",
            "🛡️ Votre arsenal est vide ! Temps de l'équiper !"
        ]
        
        st.info(random.choice(messages_encouragement))
        
        if st.button("🛍️ Aller au catalogue", use_container_width=True):
            st.session_state.page = "catalogue"
            st.rerun()
        return
    
    # Statistiques personnelles avec les nouveaux statuts
    total_commandes = len(orders)
    total_depense = sum(order[2] for order in orders)  # total_prix est à l'index 2
    moyenne_commande = total_depense / total_commandes if total_commandes > 0 else 0
    
    # Compter par statut
    statuts_count = {}
    for order in orders:
        statut = order[3] if len(order) > 3 and order[3] else "En attente"
        statuts_count[statut] = statuts_count.get(statut, 0) + 1
    
    # Afficher les métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🛍️ Mes commandes", total_commandes)
        if total_commandes > 10:
            st.caption("🏆 Champion du shopping !")
        elif total_commandes > 5:
            st.caption("⭐ Bon client !")
        else:
            st.caption("🌱 Débutant prometteur !")
    
    with col2:
        st.metric("💰 Total dépensé", f"{total_depense:.2f}€")
        if total_depense > 5000:
            st.caption("💎 VIP Platine !")
        elif total_depense > 2000:
            st.caption("🥇 Client Gold !")
        else:
            st.caption("🥉 En progression !")
    
    with col3:
        st.metric("🟡 En attente", statuts_count.get("En attente", 0))
        st.metric("🔵 En cours", statuts_count.get("En cours", 0))
    
    with col4:
        st.metric("🟢 Traitées", statuts_count.get("Traitée", 0))
        st.metric("✅ Livrées", statuts_count.get("Livrée", 0))
    
    st.markdown("---")
    
    # Afficher les commandes avec statuts colorés
    for i, order in enumerate(orders):
        (order_id, date, total, statut, articles_json, 
         traitee_par, date_traitement, commentaire_technicien, 
         date_livraison_prevue, urgence) = order + (None,) * (10 - len(order))
        
        # Définir les couleurs et emojis selon le statut
        statut = statut or "En attente"
        if statut == "En attente":
            statut_emoji = "🟡"
            progress = 25
            progress_color = "#ffc107"
        elif statut == "En cours":
            statut_emoji = "🔵"
            progress = 50
            progress_color = "#17a2b8"
        elif statut == "Traitée":
            statut_emoji = "🟢"
            progress = 75
            progress_color = "#28a745"
        elif statut == "Livrée":
            statut_emoji = "✅"
            progress = 100
            progress_color = "#6c757d"
        else:
            statut_emoji = "❓"
            progress = 0
            progress_color = "#6c757d"
        
        # Urgence
        urgence = urgence or "Normal"
        if urgence == "Urgent":
            urgence_emoji = "⚡"
        elif urgence == "Très urgent":
            urgence_emoji = "🚨"
        else:
            urgence_emoji = ""
        
        with st.expander(f"{statut_emoji} Commande #{order_id} - {date} - {total:.2f}€ {urgence_emoji}"):
            # Barre de progression
            st.markdown(f"""
            <div style="background-color: #e9ecef; border-radius: 10px; margin: 10px 0;">
                <div style="background-color: {progress_color}; width: {progress}%; padding: 8px; border-radius: 10px; text-align: center; color: white; font-weight: bold;">
                    {statut} ({progress}%)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**📅 Date commande:** {date}")
                st.write(f"**💰 Total:** {total:.2f}€")
                st.write(f"**📋 Statut:** {statut_emoji} {statut}")
                if urgence != "Normal":
                    st.write(f"**⚡ Urgence:** {urgence}")
            
            with col2:
                if traitee_par:
                    st.write(f"**🔧 Traité par:** {traitee_par}")
                if date_traitement:
                    st.write(f"**📅 Date traitement:** {date_traitement}")
                if date_livraison_prevue:
                    st.write(f"**🚚 Livraison prévue:** {date_livraison_prevue}")
                if commentaire_technicien:
                    st.write(f"**💬 Commentaire technicien:** {commentaire_technicien}")
            
            # Afficher les articles
            try:
                articles = json.loads(articles_json) if isinstance(articles_json, str) else articles_json
                if not isinstance(articles, list):
                    articles = [articles]
                    
                st.markdown("**📦 Articles commandés:**")
                for article in articles:
                    if isinstance(article, dict) and 'Nom' in article:
                        st.write(f"• {article['Nom']}")
                    elif isinstance(article, dict):
                        nom = article.get('nom', article.get('name', 'Article sans nom'))
                        st.write(f"• {nom}")
                    else:
                        st.write(f"• {str(article)}")
                        
            except json.JSONDecodeError:
                st.error("❌ Erreur de lecture des articles")
            except Exception as e:
                st.error(f"❌ Erreur affichage articles: {e}")
            
            # Messages selon le statut
            if statut == "En attente":
                st.info("⏳ Votre commande est en file d'attente. Un technicien va bientôt la prendre en charge.")
            elif statut == "En cours":
                st.info("🔧 Votre commande est actuellement en cours de traitement par l'équipe technique.")
            elif statut == "Traitée":
                st.success("🎉 Votre commande a été préparée ! Elle va bientôt être livrée.")
            elif statut == "Livrée":
                st.success("✅ Commande livrée ! Merci d'avoir utilisé FLUX/PARA Commander.")
    
    # Bouton pour nouvelle commande avec message marrant
    st.markdown("---")
    
    messages_nouvelle_commande = [
        "🚀 Prêt pour une nouvelle mission shopping ?",
        "⭐ Votre équipe a besoin de plus d'équipement ?",
        "🎯 Temps de compléter votre arsenal !",
        "🛡️ Une nouvelle aventure vous attend !",
        "💪 Continuez à équiper comme un chef !"
    ]
    
    st.info(random.choice(messages_nouvelle_commande))
    
    if st.button("🛍️ Nouvelle commande", use_container_width=True):
        st.session_state.page = "catalogue"
        st.rerun()

def show_stats():
    if not st.session_state.current_user.get("can_view_stats"):
        st.error("⛔ Accès refusé - Vous n'avez pas l'autorisation de voir les statistiques")
        return
    st.markdown("## 📊 Statistiques globales - Administration")
    st.markdown("### 🟩 Vue d'ensemble")
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from collections import Counter, defaultdict
    from datetime import datetime
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    import re

    def nom_base_article(nom):
        # Regroupe par nom sans la taille (ex: "Chaussure de sécurité JALAS Taille 37" -> "Chaussure de sécurité JALAS")
        return re.sub(r"\s*[Tt]aille\s*[0-9A-Za-z]+", "", nom).strip()

    try:
        # Récupérer toutes les commandes
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, contremaître, equipe, articles_json, total_prix
                FROM commandes
            """)
            rows = cursor.fetchall()
            conn.close()
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, contremaître, equipe, articles_json, total_prix
                FROM commandes
            """)
            rows = cursor.fetchall()
            conn.close()

        if not rows:
            st.info("Aucune commande enregistrée.")
            return

        # Construire un DataFrame
        df = pd.DataFrame(rows, columns=["id", "date", "contremaitre", "equipe", "articles_json", "total_prix"])
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["total_prix"] = pd.to_numeric(df["total_prix"], errors="coerce")

        # Statistiques globales
        nb_commandes = len(df)
        total_depense = df["total_prix"].sum()
        moyenne_commande = df["total_prix"].mean()
        total_articles = 0
        articles_counter = Counter()
        articles_counter_base = Counter()
        for articles_json in df["articles_json"]:
            try:
                articles = json.loads(articles_json) if isinstance(articles_json, str) else articles_json
                if not isinstance(articles, list):
                    articles = [articles]
                total_articles += len(articles)
                for article in articles:
                    if isinstance(article, dict):
                        nom = article.get("Nom") or article.get("nom") or article.get("name")
                        if nom:
                            articles_counter[nom] += 1
                            articles_counter_base[nom_base_article(nom)] += 1
            except Exception:
                continue

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🧾 Total commandes", nb_commandes)
        with col2:
            st.metric("💰 Montant total", f"{total_depense:.2f}€")
        with col3:
            st.metric("📊 Moyenne/commande", f"{moyenne_commande:.2f}€")
        with col4:
            st.metric("📦 Total articles", total_articles)

        # Évolution mensuelle
        st.markdown("### 📈 Évolution mensuelle")
        df["mois"] = df["date"].dt.to_period("M").astype(str)
        commandes_par_mois = df.groupby("mois")["id"].count().reset_index()
        commandes_par_mois.columns = ["Mois", "Nb commandes"]
        fig1 = px.bar(commandes_par_mois, x="Mois", y="Nb commandes", title="Nombre de commandes par mois")
        st.plotly_chart(fig1, use_container_width=True)

        ca_par_mois = df.groupby("mois")["total_prix"].sum().reset_index()
        ca_par_mois.columns = ["Mois", "Montant (€)"]
        fig2 = px.bar(ca_par_mois, x="Mois", y="Montant (€)", title="Montant total des commandes par mois")
        st.plotly_chart(fig2, use_container_width=True)

        # Répartition par équipe
        st.markdown("### 🧑‍🤝‍🧑 Répartition par équipe")
        equipe_counts = df["equipe"].value_counts()
        fig3 = px.pie(values=equipe_counts.values, names=equipe_counts.index, title="Commandes par équipe")
        st.plotly_chart(fig3, use_container_width=True)

        # Top contremaîtres
        st.markdown("### 🏅 Top contremaîtres (nb commandes)")
        top_users = df["contremaitre"].value_counts().head(5)
        st.table(top_users)
        st.markdown("### 💎 Top contremaîtres (montant)")
        top_users_montant = df.groupby("contremaitre")["total_prix"].sum().sort_values(ascending=False).head(5)
        st.table(top_users_montant)

        # Top articles
        st.markdown("### 📦 Analyse des articles les plus commandés")
        if articles_counter_base:
            top_articles_base = articles_counter_base.most_common(10)
            st.table(pd.DataFrame(top_articles_base, columns=["Article", "Quantité totale"]))
        else:
            st.info("Aucun article exploitable pour le top articles.")

        # --- Export CSV ---
        st.markdown("### 🗄️ Export des données")
        csv = df.to_csv(index=False).encode('utf-8')
        col_csv, col_pdf = st.columns([2, 3])
        with col_csv:
            st.download_button(
                label="📥 Télécharger CSV",
                data=csv,
                file_name="stats_commandes.csv",
                mime="text/csv"
            )
        # --- Rapport PDF ---
        with col_pdf:
            if st.button("📝 Générer rapport PDF", use_container_width=True):
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                styles = getSampleStyleSheet()
                story = []
                story.append(Paragraph("Statistiques globales FLUX/PARA", styles['Title']))
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"Total commandes : <b>{nb_commandes}</b>", styles['Normal']))
                story.append(Paragraph(f"Montant total : <b>{total_depense:.2f} €</b>", styles['Normal']))
                story.append(Paragraph(f"Moyenne/commande : <b>{moyenne_commande:.2f} €</b>", styles['Normal']))
                story.append(Paragraph(f"Total articles : <b>{total_articles}</b>", styles['Normal']))
                story.append(Spacer(1, 12))
                # Top utilisateurs
                story.append(Paragraph("Top contremaîtres (nb commandes) :", styles['Heading3']))
                data_users = [["Contremaître", "Nb commandes"]] + [[u, c] for u, c in top_users.items()]
                t_users = Table(data_users)
                t_users.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(t_users)
                story.append(Spacer(1, 12))
                # Top articles (par nom de base)
                story.append(Paragraph("Top articles commandés :", styles['Heading3']))
                if articles_counter_base:
                    data_articles = [["Article", "Quantité totale"]] + list(top_articles_base)
                    t_articles = Table(data_articles)
                    t_articles.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(t_articles)
                else:
                    story.append(Paragraph("Aucun article exploitable.", styles['Normal']))
                doc.build(story)
                buffer.seek(0)
                st.download_button(
                    label="📄 Télécharger rapport PDF",
                    data=buffer.getvalue(),
                    file_name="rapport_stats_flux_para.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    except Exception as e:
        st.error(f"Erreur chargement stats détaillées: {e}")

def show_historique():
    if not st.session_state.current_user.get("can_view_all_orders"):
        st.error("⛔ Accès refusé - Vous n'avez pas l'autorisation de voir toutes les commandes")
        return
    st.markdown("### 📊 Historique des commandes")
    
    # --- Récupération des commandes ---
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, contremaître, equipe, articles_json, total_prix
                FROM commandes 
                ORDER BY date DESC
            """)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, contremaître, equipe, articles_json, total_prix
                FROM commandes 
                ORDER BY date DESC
            """)
        orders = cursor.fetchall()
        conn.close()
        
        if not orders:
            st.info("Aucune commande dans l'historique")
            return
        
        for order in orders:
            order_id, date, contremaitre, equipe, articles_json, total_prix = order
            with st.expander(f"🛒 Commande #{order_id} - {contremaitre} ({equipe}) - {total_prix}€", expanded=False):
                st.write(f"📅 **Date:** {date}")
                st.write(f"👤 **Contremaître:** {contremaitre}")
                st.write(f"👷‍♂️ **Équipe:** {equipe}")
                st.write(f"💰 **Total:** {total_prix}€")
                st.markdown("#### 📦 Articles commandés:")
                try:
                    articles = json.loads(articles_json) if isinstance(articles_json, str) else articles_json
                    if not isinstance(articles, list):
                        articles = [articles]
                    for article in articles:
                        if isinstance(article, dict) and 'Nom' in article:
                            st.write(f"• {article['Nom']}")
                        elif isinstance(article, dict):
                            nom = article.get('nom', article.get('name', 'Article sans nom'))
                            st.write(f"• {nom}")
                        else:
                            st.write(f"• {str(article)}")
                except Exception as e:
                    st.error(f"❌ Erreur affichage articles: {e}")

            # === FONCTIONS ADMIN ===
            if st.session_state.current_user.get("role") == "admin":
                col_admin1, col_admin2 = st.columns(2)
                
                with col_admin1:
                    # Bouton pour modifier le contremaître
                    edit_key = f"edit_contremaitre_{order_id}"
                    if edit_key not in st.session_state:
                        st.session_state[edit_key] = False
                    
                    if not st.session_state[edit_key]:
                        if st.button(f"✏️ Modifier contremaître", key=f"edit_btn_{order_id}"):
                            st.session_state[edit_key] = True
                            st.rerun()
                    else:
                        st.markdown("**✏️ Modifier le contremaître :**")
                        users_list = get_all_users_list()
                        if users_list:
                            with st.form(f"edit_contremaitre_form_{order_id}"):
                                nouveau_contremaitre = st.selectbox(
                                    "Nouveau contremaître",
                                    users_list,
                                    index=users_list.index(contremaitre) if contremaitre in users_list else 0,
                                    key=f"new_contremaitre_{order_id}"
                                )
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    save_btn = st.form_submit_button("💾 Sauvegarder")
                                with col_cancel:
                                    cancel_btn = st.form_submit_button("❌ Annuler")
                                
                                if save_btn and nouveau_contremaitre != contremaitre:
                                    if update_commande_contremaitre(order_id, nouveau_contremaitre):
                                        st.success(f"✅ Contremaître modifié: {contremaitre} → {nouveau_contremaitre}")
                                        st.session_state[edit_key] = False
                                        st.rerun()
                                    else:
                                        st.error("❌ Erreur modification")
                                elif save_btn:
                                    st.info("Aucun changement détecté")
                                    st.session_state[edit_key] = False
                                    st.rerun()
                                
                                if cancel_btn:
                                    st.session_state[edit_key] = False
                                    st.rerun()
                        else:
                            st.error("❌ Impossible de charger la liste des utilisateurs")
                            if st.button("❌ Annuler", key=f"cancel_edit_{order_id}"):
                                st.session_state[edit_key] = False
                                st.rerun()
                
                with col_admin2:
                    # Bouton de suppression
                    if st.button(f"🗑️ Supprimer", key=f"delete_order_{order_id}"):
                        if delete_commande(order_id):
                            st.success("✅ Commande supprimée")
                            st.rerun()
                        else:
                            st.error("❌ Erreur suppression")
    except Exception as e:
        st.error(f"Erreur chargement historique: {e}")

def delete_commande(commande_id):
    """Supprime une commande (admin seulement)"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM commandes WHERE id = %s", (commande_id,))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM commandes WHERE id = ?", (commande_id,))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Erreur suppression commande: {e}")
        return False

def update_commande_contremaitre(commande_id, nouveau_contremaitre):
    """Met à jour le contremaître d'une commande (admin seulement)"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE commandes SET contremaître = %s WHERE id = %s", 
                (nouveau_contremaitre, commande_id)
            )
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE commandes SET contremaître = ? WHERE id = ?", 
                (nouveau_contremaitre, commande_id)
            )
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Erreur modification contremaître: {e}")
        return False

def get_all_users_list():
    """Récupère la liste de tous les utilisateurs pour le sélecteur"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users ORDER BY username")
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users ORDER BY username")
        
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users
        
    except Exception as e:
        st.error(f"Erreur récupération utilisateurs: {e}")
        return []

def render_mobile_navigation():
    """Navigation optimisée pour mobile avec menu hamburger"""
    user_info = st.session_state.get('current_user', {})
    
    # Menu hamburger avec expander
    with st.expander("🍔 Menu Navigation", expanded=False):
        st.markdown('<div class="mobile-nav fade-in">', unsafe_allow_html=True)
        
        # Navigation principale en 2 colonnes sur mobile
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🛡️ Catalogue", key="mobile_catalogue", use_container_width=True):
                st.session_state.page = "catalogue"
                st.rerun()
            if st.button("⚡ Commande rapide", key="mobile_commande_rapide", use_container_width=True):
                ok, nb, msg = repeat_last_order()
                if ok and nb > 0:
                    st.toast(f"⚡ {msg} !", icon="✅")
                    st.session_state.page = "cart"
                    st.rerun()
                elif ok and nb == 0:
                    st.warning("Aucun article ajouté (budget dépassé ?)")
                else:
                    st.info("📭 " + msg)
            if st.button("📊 Mes commandes", key="mobile_mes_commandes", use_container_width=True):
                st.session_state.page = "mes_commandes"
                st.rerun()
            if user_info.get("can_view_stats"):
                if st.button("📈 Statistiques", key="mobile_stats", use_container_width=True):
                    st.session_state.page = "stats"
                    st.rerun()
            if user_info.get("role") == "admin":
                if st.button("👥 Utilisateurs", key="mobile_admin_users", use_container_width=True):
                    st.session_state.page = "admin_users"
                    st.rerun()
        
        with col2:
            if st.button("🛒 Panier", key="mobile_cart", use_container_width=True):
                st.session_state.page = "cart"
                st.rerun()
            if user_info.get("can_view_all_orders"):
                if st.button("📋 Historique", key="mobile_historique", use_container_width=True):
                    st.session_state.page = "historique"
                    st.rerun()
            if user_info.get("can_add_articles"):
                if st.button("🔧 Traitement", key="mobile_traitement", use_container_width=True):
                    st.session_state.page = "traitement"
                    st.rerun()
                if st.button("➕ Articles", key="mobile_admin_articles", use_container_width=True):
                    st.session_state.page = "admin_articles"
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Bouton de déconnexion proéminent
        st.markdown("---")
        if st.button("🚪 Déconnexion", key="mobile_logout", type="primary", use_container_width=True):
            # Code de déconnexion (même que desktop)
            user_id = st.session_state.get('current_user', {}).get('id')
            try:
                if os.path.exists('temp_session.json'):
                    os.remove('temp_session.json')
            except Exception:
                pass
            if user_id and USE_POSTGRESQL:
                try:
                    conn = psycopg2.connect(DATABASE_URL)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
                    cursor.execute("DELETE FROM user_cart_sessions WHERE user_id = %s", (user_id,))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
            st.session_state.clear()
            st.session_state.authenticated = False
            st.session_state.current_user = {}
            st.session_state.cart = []
            st.session_state.page = "login"
            st.rerun()

def render_navigation():
    """Navigation adaptative (mobile/desktop)"""
    user_info = st.session_state.get('current_user', {})
    
    # Toggle pour activer le mode mobile (temporaire pour test)
    mobile_mode = st.sidebar.checkbox("📱 Mode Mobile", value=False, help="Active l'interface optimisée mobile")
    
    if mobile_mode:
        render_mobile_navigation()
        return
    
    # Navigation desktop classique
    user_info = st.session_state.get('current_user', {})
    buttons = [
        ("🛡️ Catalogue", "catalogue"),
        ("⚡ Commande rapide", "commande_rapide"),
        ("🛒 Panier", "cart"),
        ("📊 Mes commandes", "mes_commandes")
    ]
    if user_info.get("can_view_all_orders"):
        buttons.append(("📋 Historique", "historique"))
    if user_info.get("can_view_stats"):
        buttons.append(("📈 Statistiques", "stats"))
    if user_info.get("can_add_articles"):
        buttons.append(("🔧 Traitement", "traitement"))
        buttons.append(("➕ Articles", "admin_articles"))
    if user_info.get("role") == "admin":
        buttons.append(("👥 Utilisateurs", "admin_users"))
    buttons.append(("🚪 Déconnexion", "logout"))
    cols = st.columns(len(buttons))
    for i, (label, page) in enumerate(buttons):
        with cols[i]:
            if page == "commande_rapide":
                if st.button(label, use_container_width=True, type="primary"):
                    ok, nb, msg = repeat_last_order()
                    if ok and nb > 0:
                        st.toast(f"⚡ {msg} !", icon="✅")
                        st.session_state.page = "cart"
                        st.rerun()
                    elif ok and nb == 0:
                        st.warning("Aucun article ajouté (budget dépassé ?)")
                    else:
                        st.info("📭 " + msg)
            elif page == "logout":
                if st.button(label, use_container_width=True):
                    # SÉCURITÉ : Nettoyage complet des sessions
                    user_id = st.session_state.get('current_user', {}).get('id')
                    
                    # Nettoyage session locale
                    try:
                        if os.path.exists('temp_session.json'):
                            os.remove('temp_session.json')
                    except Exception:
                        pass
                    
                    # Nettoyage sessions en base de données (prod)
                    if user_id and USE_POSTGRESQL:
                        try:
                            conn = psycopg2.connect(DATABASE_URL)
                            cursor = conn.cursor()
                            # Supprimer les tokens de session de cet utilisateur
                            cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
                            # Supprimer le panier sauvegardé
                            cursor.execute("DELETE FROM user_cart_sessions WHERE user_id = %s", (user_id,))
                            conn.commit()
                            conn.close()
                        except Exception:
                            pass
                    
                    # Nettoyage Streamlit session_state
                    st.session_state.clear()
                    st.session_state.authenticated = False
                    st.session_state.current_user = {}
                    st.session_state.cart = []
                    st.session_state.page = "login"
                    st.rerun()
            else:
                if st.button(label, use_container_width=True):
                    st.session_state.page = page
                    st.rerun()

def ensure_users_permission_columns():
    """Ajoute can_move_articles et can_delete_articles si manquants (Postgres)"""
    if not USE_POSTGRESQL:
        return
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS can_move_articles BOOLEAN DEFAULT FALSE")
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS can_delete_articles BOOLEAN DEFAULT FALSE")
        conn.commit()
        conn.close()
    except Exception:
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass

def main():
    """Fonction principale de l'application"""
    # Initialisation
    init_database()
    ensure_users_permission_columns()
    init_users_db()
    init_session_state()
    
    # Afficher les erreurs de budget avec animation
    show_budget_error_modal()
    
    # Navigation selon l'état d'authentification
    if not st.session_state.get('authenticated', False):
        if st.session_state.get('page') == 'register':
            show_register()
        elif st.session_state.get('page') == 'reset_password':
            show_reset_password()
        elif st.session_state.get('page') == 'force_change_password':
            show_force_password_change()
        else:
            show_login()
    else:
        # IMPORTANT: Rafraîchir les permissions à chaque chargement de page
        refresh_current_user_permissions()
        
        # Interface utilisateur connecté
        render_navigation()
        
        # Contenu selon la page sélectionnée
        page = st.session_state.page
        
        if page == "catalogue":
            show_catalogue()
        elif page == "cart":
            show_cart()
        elif page == "validation":
            show_validation()
        elif page == "historique":
            if (st.session_state.current_user or {}).get("can_view_all_orders"):
                show_historique()
            else:
                st.warning("⛔ Accès réservé.")
        elif page == "stats":
            if (st.session_state.current_user or {}).get("can_view_stats"):
                show_advanced_analytics()
            else:
                st.warning("⛔ Accès réservé.")
        elif page == "mes_commandes":
            show_mes_commandes()
        elif page == "admin_articles":
            if (st.session_state.current_user or {}).get("can_add_articles"):
                show_admin_articles()
            else:
                st.warning("⛔ Accès réservé.")
        elif page == "traitement":
            if (st.session_state.current_user or {}).get("can_add_articles"):
                show_traitement_commandes()
            else:
                st.warning("⛔ Accès réservé.")
        elif page == "admin_users":
            if st.session_state.get('current_user', {}).get('role') == 'admin':
                show_user_admin_page()
            else:
                st.warning("⛔ Accès réservé.")
        else:
            show_catalogue()

    # En haut de main() ou dans render_navigation()
    if 'sidebar_open' not in st.session_state:
        st.session_state.sidebar_open = True

    # Bouton pour réduire/afficher la sidebar (affiché en haut de la page)
    if st.button("⬅️ Réduire la barre latérale" if st.session_state.sidebar_open else "➡️ Afficher la barre latérale", key="toggle_sidebar_btn"):
        st.session_state.sidebar_open = not st.session_state.sidebar_open
        st.rerun()

    # Afficher la sidebar UNIQUEMENT si l'utilisateur est authentifié
    if st.session_state.get('authenticated', False):
        with st.sidebar:
            if st.session_state.sidebar_open:
                show_cart_sidebar()  # ou ton contenu habituel
            else:
                st.write("🔽 Barre latérale réduite")

def show_main_app():
    """Interface principale de l'application"""
    user_info = st.session_state.get('current_user', {})
    
    if not user_info:
        st.session_state.page = 'login'
        st.rerun()
        return
    
    # Message de bienvenue marrant
    messages_app = [
        f"🎯 Salut {user_info['username']} ! Prêt pour l'action ?",
        f"⚡ {user_info['username']} ! Votre équipe compte sur vous !",
        f"🚀 Mission en cours, agent {user_info['username']} !",
        f"🛡️ {user_info['username']} ! L'aventure continue !",
        f"⭐ Bienvenue dans votre QG, {user_info['username']} !"
    ]
    
    st.success(random.choice(messages_app))
    
    # Navigation simple pour tester
    if st.button("🚪 Se déconnecter"):
        # Messages de déconnexion marrants
        messages_deconnexion = [
            "👋 À bientôt ! Votre équipe vous attend !",
            "🚀 Mission terminée ! Bon repos, agent !",
            "⭐ Déconnexion réussie ! Revenez vite !",
            "🛡️ Au revoir ! Gardez l'esprit d'équipe !",
            "🎯 À la prochaine mission !"
        ]
        
        st.info(random.choice(messages_deconnexion))
        time.sleep(1)
        st.session_state.clear()
        st.session_state.authenticated = False
        st.session_state.current_user = {}
        st.session_state.cart = []  # <-- Ajoute cette ligne
        st.session_state.page = 'login'
        st.rerun()
    
    st.markdown("### 🛡️ Application FLUX/PARA")
    st.info("Interface principale en cours de développement...")
    
    # Afficher les infos utilisateur
    with st.expander("👤 Mes informations"):
        st.write(f"**Nom:** {user_info['username']}")
        st.write(f"**Rôle:** {user_info['role']}")
        st.write(f"**Équipe:** {user_info['equipe']}")
        st.write(f"**Fonction:** {user_info['fonction']}")
        st.write(f"**Couleur préférée:** {user_info['couleur_preferee']}")

def show_admin_articles():
    user_info = st.session_state.get('current_user') or {}
    articles_df = load_articles()
    st.markdown("### 🛠️ Gestion des articles - Administration")
    tabs = st.tabs(["📋 Catalogue actuel", "➕ Ajouter article", "🔄 Déplacer", "📤 Import CSV"])

    with tabs[0]:   # 📑 Catalogue actuel
        st.markdown("#### 📋 Articles actuels")
        st.markdown("#### 🔍 Recherche dans le catalogue")
        query = st.text_input("Référence ou nom…")
        ref_col = get_ref_col(articles_df)
        df_affiche = articles_df.copy()
        if query:
            q = query.strip()
            if q:
                mask = (
                    articles_df["Nom"].astype(str).str.contains(q, case=False, na=False)
                    | articles_df[ref_col].astype(str).str.contains(q, case=False, na=False)
                )
                df_affiche = articles_df[mask]
        st.dataframe(df_affiche, use_container_width=True)

        # --- Affichage du bouton suppression selon les permissions ---
        if user_info.get("role") == "admin" or user_info.get("can_delete_articles", False):
            st.markdown("#### 🗑️ Supprimer un article")
            if df_affiche.empty:
                st.info("Aucun article correspondant.")
            else:
                # Options uniques même en cas de doublons (réf/nom identiques)
                options = [
                    (int(idx), str(row[ref_col]), str(row["Nom"]))
                    for idx, row in df_affiche.iterrows()
                ]
                selected = st.selectbox(
                    "Choisissez l'article :",
                    options,
                    format_func=lambda t: f"{t[1]} – {t[2]}"
                )
                ref_supp = selected[1]
                if st.button("🗑️ Supprimer", type="secondary"):
                    ok, msg = delete_article(ref_supp, ref_col)
                    if ok:
                        st.success(msg)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.info("🔒 Suppression réservée aux utilisateurs autorisés.")

    with tabs[1]:   # ➕ Ajouter article
        st.markdown("#### ➕ Ajouter un nouvel article au catalogue")
        st.caption("💡 **Tailles multiples** : cochez « Plusieurs tailles » et indiquez les tailles (ex: 43, 44, 45 ou S, M, L, XL) — chaque taille sera créée automatiquement.")
        # Nouvelles catégories réorganisées par zone de protection
        categories = [
            "Protection Tête", "Protection Auditive", "Protection Oculaire", "Protection Respiratoire",
            "Protection Main", "Protection Pied", "Protection Corps", "Vêtements Haute Visibilité",
            "Oxycoupage", "EPI Général", "No Touch",
            "Outils", "Éclairage", "Marquage", "Bureau", "Nettoyage", "Hygiène", "Divers"
        ]
        with st.form("ajout_article_form"):
            multi_tailles = st.checkbox("📏 Article avec plusieurs tailles (pointure, S, M, L, XL…)", value=False)
            ref = st.text_input("N° Référence* (court, ex: CHAU-S3)", max_chars=40, help="Max 50 caractères. Pour plusieurs tailles: base sans la taille (ex: CHAU-S3)")
            nom = st.text_input("Nom* (sans la taille)", help="Ex: Chaussure de sécurité S3 bruleur — la taille sera ajoutée automatiquement")
            tailles_input = st.text_input("📏 Tailles (si plusieurs) — ex: 43, 44, 45 ou S, M, L, XL", placeholder="43, 44, 45, 46", help="Remplir uniquement si « Plusieurs tailles » est coché")
            description = st.selectbox("Description* (catégorie)", categories)
            prix = st.number_input("Prix*", min_value=0.0, step=0.01, format="%.2f")
            unite = st.text_input("Unité*", value="Par unité")
            submitted = st.form_submit_button("Ajouter l'article")
            if submitted:
                if multi_tailles and (tailles_input or "").strip():
                    tailles = [t.strip() for t in tailles_input.split(",") if t.strip()]
                    if not tailles:
                        st.error("Indiquez au moins une taille (ex: 43, 44, 45)")
                    elif len(ref) + 4 > 50:
                        st.error("Référence trop longue. Utilisez une base courte (ex: CHAU-S3)")
                    else:
                        nb_ok = 0
                        for t in tailles:
                            ref_t = f"{ref}-{t}"[:50]
                            nom_t = f"{nom} Taille {t}".strip()
                            ok, msg = add_article_to_csv(ref_t, nom_t, description, prix, unite)
                            if ok:
                                nb_ok += 1
                        if nb_ok > 0:
                            st.success(f"✅ {nb_ok} article(s) ajouté(s) : {', '.join(tailles)}")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(msg)
                elif multi_tailles:
                    st.error("Indiquez les tailles (ex: 43, 44, 45 ou S, M, L, XL)")
                else:
                    ok, msg = add_article_to_csv(ref, nom, description, prix, unite)
                    if ok:
                        st.success(msg)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(msg)

    with tabs[2]:   # 🔄 Déplacer
        st.markdown("#### 🔄 Déplacer un article vers une autre catégorie")
        
        # Vérifier les permissions
        if not (user_info.get("role") == "admin" or user_info.get("can_move_articles", False)):
            st.info("🔒 Déplacement réservé aux utilisateurs autorisés.")
        elif articles_df.empty:
            st.info("Aucun article à déplacer.")
        else:
            # Sélection de l'article à déplacer
            ref_col = get_ref_col(articles_df)
            article_options = [
                (int(idx), str(row[ref_col]), str(row["Nom"]), str(row["Description"]))
                for idx, row in articles_df.iterrows()
            ]
            
            selected_article = st.selectbox(
                "Choisissez l'article à déplacer :",
                article_options,
                format_func=lambda t: f"{t[1]} - {t[2]} (actuellement: {t[3]})"
            )
            
            # Sélection de la nouvelle catégorie
            available_categories = [
                "Protection Tête", "Protection Auditive", "Protection Oculaire", "Protection Respiratoire",
                "Protection Main", "Protection Pied", "Protection Corps", "Vêtements Haute Visibilité",
                "Oxycoupage", "EPI Général", "No Touch",
                "Outils", "Éclairage", "Marquage", "Bureau", "Nettoyage", "Hygiène", "Divers"
            ]
            
            current_category = selected_article[3]
            new_category = st.selectbox(
                "Nouvelle catégorie :",
                available_categories,
                index=available_categories.index(current_category) if current_category in available_categories else 0
            )
            
            if new_category != current_category:
                if st.button("🔄 Déplacer l'article", type="primary"):
                    success, message = move_article_category(selected_article[1], new_category)
                    if success:
                        st.success(message)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.info("Sélectionnez une catégorie différente pour déplacer l'article.")

    with tabs[3]:   # 📤 Import CSV
        # ... code existant ...
        pass  # (inchangé)

def add_article_to_csv(reference, nom, description, prix, unite, *args, **kwargs):
    """
    Ajoute un article au catalogue : PostgreSQL (prod) ou CSV (local).
    Retourne (success, message).
    """
    try:
        prix_val = float(prix) if prix is not None else 0.0
    except (TypeError, ValueError):
        prix_val = 0.0
    
    if USE_POSTGRESQL:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO articles (reference, nom, description, prix, unitee)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (reference) DO UPDATE SET
                    nom = EXCLUDED.nom,
                    description = EXCLUDED.description,
                    prix = EXCLUDED.prix,
                    unitee = EXCLUDED.unitee
            """, (str(reference), str(nom), str(description or ''), prix_val, str(unite or 'Par unité')))
            conn.commit()
            conn.close()
            try:
                load_articles.clear()
            except Exception:
                pass
            st.cache_data.clear()
            return True, "✅ Article ajouté au catalogue"
        except Exception as e:
            return False, f"❌ Erreur ajout article : {e}"
    
    try:
        file_path = ARTICLES_CSV_PATH
        header = ['N° Référence', 'Nom', 'Description', 'Prix', 'Unitée']
        file_exists = os.path.isfile(file_path)
        with open(file_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(header)
            writer.writerow([str(reference), str(nom), str(description or ''), f"{prix_val:.2f}", str(unite or 'Par unité')])
        try:
            load_articles.clear()
        except Exception:
            pass
        st.cache_data.clear()
        return True, "✅ Article ajouté au catalogue"
    except Exception as e:
        return False, f"❌ Erreur ajout article : {e}"

def import_articles_from_csv(new_articles_df):
    """Importe plusieurs articles depuis un DataFrame (PostgreSQL ou CSV)"""
    try:
        global articles_df
        cols = list(new_articles_df.columns)
        
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            for _, row in new_articles_df.iterrows():
                try:
                    ref = str(row[cols[0]]) if len(cols) > 0 and pd.notna(row[cols[0]]) else ''
                    nom = str(row[cols[1]]) if len(cols) > 1 and pd.notna(row[cols[1]]) else ''
                    desc = str(row[cols[2]]) if len(cols) > 2 and pd.notna(row[cols[2]]) else ''
                    prix = float(row[cols[3]]) if len(cols) > 3 and pd.notna(row[cols[3]]) else 0.0
                    unitee = str(row[cols[4]]) if len(cols) > 4 and pd.notna(row[cols[4]]) else 'Par unité'
                    if ref and nom:
                        cursor.execute("""
                            INSERT INTO articles (reference, nom, description, prix, unitee)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (reference) DO UPDATE SET
                                nom = EXCLUDED.nom, description = EXCLUDED.description,
                                prix = EXCLUDED.prix, unitee = EXCLUDED.unitee
                        """, (ref, nom, desc, prix, unitee))
                except Exception:
                    pass
            conn.commit()
            conn.close()
        else:
            try:
                df_actuel = pd.read_csv(ARTICLES_CSV_PATH, encoding='utf-8', usecols=[0,1,2,3,4])
                df_actuel.columns = ['N° Référence', 'Nom', 'Description', 'Prix', 'Unitée']
            except FileNotFoundError:
                df_actuel = pd.DataFrame(columns=['N° Référence', 'Nom', 'Description', 'Prix', 'Unitée'])
            if len(new_articles_df.columns) >= 5:
                df_import = new_articles_df.iloc[:, :5].copy()
                df_import.columns = ['N° Référence', 'Nom', 'Description', 'Prix', 'Unitée']
            else:
                df_import = new_articles_df.copy()
            df_combine = pd.concat([df_actuel, df_import], ignore_index=True)
            df_combine = df_combine.drop_duplicates(subset=['N° Référence'], keep='last')
            df_combine.to_csv(ARTICLES_CSV_PATH, index=False, encoding='utf-8')
        
        st.cache_data.clear()
        try:
            load_articles.clear()
        except Exception:
            pass
        articles_df = load_articles()
        return True
    except Exception as e:
        st.error(f"Erreur import articles: {e}")
        return False

def show_user_management():
    """Interface améliorée de gestion des utilisateurs - AVEC SUPPRESSION"""
    st.markdown("### 👥 Gestion des utilisateurs - Administration")
    
    try:
        users = get_all_users()
        
        if not users:
            st.info("Aucun utilisateur trouvé")
            return
        
        # Vérifier si l'utilisateur connecté est admin
        current_user = st.session_state.get('current_user', {})
        is_current_admin = current_user.get('role') == 'admin'
        
        for user in users:
            if len(user) == 8:
                user_id, username, equipe, fonction, can_add_articles, can_view_stats, can_view_all_orders, role = user
                can_move_articles, can_delete_articles = False, False
            else:
                user_id, username, equipe, fonction, can_add_articles, can_view_stats, can_view_all_orders, role, can_move_articles, can_delete_articles = user
            # Récupérer le montant total des commandes de cet utilisateur
            total_montant = 0
            nb_cmds = 0
            try:
                if USE_POSTGRESQL:
                    conn = psycopg2.connect(DATABASE_URL)
                    cursor = conn.cursor()
                    cursor.execute("SELECT SUM(total_prix), COUNT(*) FROM commandes WHERE contremaître = %s", (username,))
                else:
                    conn = sqlite3.connect(DATABASE_PATH)
                    cursor = conn.cursor()
                    cursor.execute("SELECT SUM(total_prix), COUNT(*) FROM commandes WHERE contremaître = ?", (username,))
                res = cursor.fetchone()
                conn.close()
                if res:
                    total_montant = res[0] or 0
                    nb_cmds = res[1] or 0
            except Exception:
                pass
            with st.expander(f"👤 {username} - {fonction} ({equipe})", expanded=False):
                st.write(f"**ID:** {user_id}")
                st.write(f"**Équipe:** {equipe}")
                st.write(f"**Fonction:** {fonction}")
                st.write(f"**Rôle:** {role}")
                st.write(f"**Montant total commandes:** {total_montant:.2f} €  |  **Nb commandes:** {nb_cmds}")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**ID:** {user_id}")
                    st.write(f"**Équipe:** {equipe}")
                    st.write(f"**Fonction:** {fonction}")
                    st.write(f"**Rôle:** {role}")
                    
                    # Interface pour modifier les permissions
                    with st.form(f"permissions_{user_id}"):
                        st.markdown("### 🔐 Permissions")
                        
                        new_can_add = st.checkbox("📝 Peut ajouter des articles", 
                                                 value=bool(can_add_articles),
                                                 key=f"add_{user_id}")
                        
                        new_can_stats = st.checkbox("📊 Peut voir les statistiques", 
                                                   value=bool(can_view_stats),
                                                   key=f"stats_{user_id}")
                        
                        new_can_all_orders = st.checkbox("📋 Peut voir toutes les commandes", 
                                                        value=bool(can_view_all_orders),
                                                        key=f"orders_{user_id}")
                        
                        new_can_move = st.checkbox("🔄 Peut déplacer des articles", 
                                                 value=bool(can_move_articles),
                                                 key=f"move_{user_id}")
                        
                        new_can_delete = st.checkbox("🗑️ Peut supprimer des articles", 
                                                   value=bool(can_delete_articles),
                                                   key=f"delete_{user_id}")
                        
                        if st.form_submit_button("💾 Sauvegarder permissions", use_container_width=True):
                            new_permissions = {
                                'can_add_articles': new_can_add,
                                'can_view_stats': new_can_stats,
                                'can_view_all_orders': new_can_all_orders,
                                'can_move_articles': new_can_move,
                                'can_delete_articles': new_can_delete
                            }
                            
                            if update_user_permissions(user_id, new_permissions):
                                st.success("✅ Permissions mises à jour !")
                                # PATCH : si l'utilisateur modifié est l'utilisateur courant, mets à jour la session
                                current_user = st.session_state.get('current_user', {})
                                if current_user and current_user.get("id") == user_id:
                                    for k, v in new_permissions.items():
                                        st.session_state.current_user[k] = v
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ Erreur mise à jour")
                
                with col2:
                    # Actions rapides
                    st.markdown("### ⚡ Actions rapides")
                    
                    if st.button(f"👨‍💼 Chef", key=f"chef_{user_id}", use_container_width=True):
                        permissions_chef = {
                            'can_add_articles': False,
                            'can_view_stats': True,
                            'can_view_all_orders': True
                        }
                        if update_user_permissions(user_id, permissions_chef):
                            st.success("✅ Permissions CHEF appliquées")
                            time.sleep(0.5)
                            st.rerun()
                    
                    # BOUTON SUPPRESSION - SIMPLE
                    if is_current_admin and username != 'admin':
                        st.markdown("---")
                        if st.button(f"🗑️ Supprimer {username}", 
                                   key=f"delete_{user_id}", 
                                   use_container_width=True, 
                                   type="secondary"):
                            success, message = delete_user(user_id)
                            if success:
                                st.success(f"✅ {message}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                                if "constraint" in message.lower() or "foreign key" in message.lower():
                                    st.info("💡 Impossible de supprimer cet utilisateur car il a des commandes. Supprime-les d'abord dans l'historique si besoin.")
                            
    except Exception as e:
        st.error(f"Erreur chargement utilisateurs: {e}")

def send_email_notification(to_email, subject, body):
    """Envoie un email de notification (SMTP configuré via variables d'environnement)"""
    try:
        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        sender_email = os.environ.get("SMTP_USER", "")
        sender_password = os.environ.get("SMTP_PASSWORD", "")
        if not sender_email or not sender_password:
            return True  # Pas de crash si SMTP non configuré
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.warning(f"Email non envoyé ({to_email}): {e}")
        return False

def send_password_reset_email(email, new_password):
    """Envoie un email avec le nouveau mot de passe"""
    try:
        # Configuration SMTP (à adapter selon votre fournisseur)
        smtp_server = "smtp.gmail.com"  # ou votre serveur SMTP
        smtp_port = 587
        sender_email = "votre-email@gmail.com"  # À configurer
        sender_password = "votre-mot-de-passe-app"  # À configurer
        
        # Créer le message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "🔑 Réinitialisation de votre mot de passe FLUX/PARA"
        
        # Corps du message
        body = f"""
        Bonjour,
        
        Votre mot de passe pour l'application FLUX/PARA Commander a été réinitialisé.
        
        Votre nouveau mot de passe temporaire est : {new_password}
        
        ⚠️ Pour votre sécurité, nous vous recommandons de changer ce mot de passe dès votre prochaine connexion.
        
        Si vous n'avez pas demandé cette réinitialisation, contactez immédiatement l'administrateur.
        
        Cordialement,
        L'équipe FLUX/PARA
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Envoyer l'email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, email, text)
        server.quit()
        
        return True
        
    except Exception as e:
        st.error(f"Erreur envoi email: {e}")
        return False

def generate_captcha():
    """Génère un captcha simple avec opération mathématique"""
    import random
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    operation = random.choice(['+', '-', '*'])
    
    if operation == '+':
        result = a + b
        question = f"{a} + {b} = ?"
    elif operation == '-':
        result = a - b
        question = f"{a} - {b} = ?"
    else:  # multiplication
        result = a * b
        question = f"{a} × {b} = ?"
    
    return question, result

def reset_user_password(username, equipe, couleur_preferee):
    """Réinitialise le mot de passe d'un utilisateur avec question de sécurité"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT id, equipe, couleur_preferee FROM users WHERE username = %s", (username,))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, equipe, couleur_preferee FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return False, "Utilisateur non trouvé"
        user_id, user_equipe, user_couleur = user
        # ... (vérifications)
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        if USE_POSTGRESQL:
            cursor.execute("UPDATE users SET password_hash = %s WHERE username = %s", (password_hash, username))
        else:
            cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (password_hash, username))
        conn.commit()
        conn.close()
        return True, f"Votre nouveau mot de passe temporaire est : **{new_password}**"
    except Exception as e:
        return False, f"Erreur réinitialisation: {e}"

def show_reset_password():
    """Page de réinitialisation de mot de passe avec question de sécurité (SANS captcha)"""
    st.markdown("### 🔑 Réinitialisation du mot de passe")
    with st.form("reset_form"):
        st.markdown("⚠️ **Sécurité renforcée** - Répondez aux questions de sécurité pour récupérer votre mot de passe.")
        username = st.text_input("👤 Nom d'utilisateur")
        equipes = ["DIRECTION", "FLUX", "PARA", "MAINTENANCE", "QUALITE", "LOGISTIQUE"]
        equipe = st.selectbox("👷‍♂️ Votre équipe", ["Sélectionnez..."] + equipes)
        couleur_preferee = st.text_input("🎨 Votre couleur préférée", placeholder="Ex: bleu, rouge, vert...")
        submitted = st.form_submit_button("🔑 Récupérer mon mot de passe", use_container_width=True)
        if submitted:
            if not username or equipe == "Sélectionnez..." or not couleur_preferee:
                st.error("❌ Veuillez remplir tous les champs")
            else:
                success, message = reset_user_password(username, equipe, couleur_preferee)
                if success:
                    st.success("✅ Mot de passe réinitialisé avec succès !")
                    st.info(message)
                    st.warning("⚠️ Notez bien ce mot de passe temporaire et changez-le dès votre prochaine connexion")
                else:
                    st.error(f"❌ {message}")
    st.markdown("---")
    st.info("💡 **Aide:** Si vous ne vous souvenez pas de votre couleur préférée, contactez l'administrateur.")
    if st.button("← Retour à la connexion"):
        st.session_state.page = 'login'
        st.rerun()

def assign_permissions_by_function(username, fonction):
    """Attribue automatiquement les permissions selon la fonction"""
    try:
        # Définir les permissions selon la fonction
        if fonction in ["CONTREMAÎTRE", "RTZ", "GESTIONNAIRE"]:
            # Postes à responsabilité - tous les accès
            permissions = {
                'role': 'user',
                'can_add_articles': True,
                'can_view_stats': True,
                'can_view_all_orders': True
            }
        elif fonction in ["CHEF D'ÉQUIPE", "RESPONSABLE SÉCURITÉ"]:
            # Encadrement - accès aux stats uniquement
            permissions = {
                'role': 'user',
                'can_add_articles': False,
                'can_view_stats': True,
                'can_view_all_orders': False
            }
        else:
            # Utilisateur standard - accès de base
            permissions = {
                'role': 'user',
                'can_add_articles': False,
                'can_view_stats': False,
                'can_view_all_orders': False
            }
        
        # Récupérer l'ID de l'utilisateur
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        
        result = cursor.fetchone()
        if result:
            user_id = result[0]
            conn.close()
            
            # Appliquer les permissions
            update_user_permissions(user_id, permissions)
            
        return True
        
    except Exception as e:
        st.error(f"Erreur attribution permissions: {e}")
        return False

def search_articles_globally(query):
    """Recherche intelligente dans tous les articles"""
    articles_df = load_articles()
    if articles_df.empty:
        return articles_df
    
    query_lower = query.lower().strip()
    ref_col = get_ref_col(articles_df)
    
    # Recherche dans plusieurs champs
    mask = (
        articles_df['Nom'].astype(str).str.contains(query_lower, case=False, na=False) |
        articles_df[ref_col].astype(str).str.contains(query_lower, case=False, na=False) |
        articles_df['Description'].astype(str).str.contains(query_lower, case=False, na=False)
    )
    
    return articles_df[mask]

def count_articles_in_category(category):
    """Compte les articles dans une catégorie après routage automatique"""
    articles_df = load_articles()
    if articles_df.empty:
        return 0
    
    # Appliquer le même routage que dans le catalogue
    normalized_df = articles_df.copy()
    
    def categorize_article(nom, description_actuelle):
        nom_lower = str(nom).lower()
        
        # PRIORITÉ : Respecter les déplacements manuels
        valid_categories = [
            "Protection Tête", "Protection Auditive", "Protection Oculaire", "Protection Respiratoire",
            "Protection Main", "Protection Pied", "Protection Corps", "Vêtements Haute Visibilité",
            "Oxycoupage", "EPI Général", "No Touch",
            "Outils", "Éclairage", "Marquage", "Bureau", "Nettoyage", "Hygiène", "Divers"
        ]
        if str(description_actuelle) in valid_categories:
            return str(description_actuelle)
        
        # Sinon, routage automatique
        # Oxycoupage (priorité)
        if any(word in nom_lower for word in ['chaleur', 'espuna', 'alumini', 'oxycoup', 'tablier', 'cagoule', 'cache cou', 'guêtre', 'guetre', 'collier', 'allumeur', 'brosse', 'fire resistant', 'ignifug', 'sertissage']):
            return 'Oxycoupage'
        # Protection Tête
        if any(word in nom_lower for word in ['casque', 'heaume', 'protection tête', 'jugulaire']):
            return 'Protection Tête'
        # Protection Auditive
        if any(word in nom_lower for word in ['bouchon', 'oreille', 'auditif', 'antibruit']):
            return 'Protection Auditive'
        # Protection Oculaire
        if any(word in nom_lower for word in ['lunette', 'oculaire', 'visière', 'deltaplus', 'ambric', 'bollé', 'bolle', 'cobra', 'transparente', 'pacaya', 'tracpsi']):
            return 'Protection Oculaire'
        # Protection Respiratoire
        if any(word in nom_lower for word in ['masque', 'respiratoire', 'filtre', 'cartouche']):
            return 'Protection Respiratoire'
        # Protection Main
        if any(word in nom_lower for word in ['gant', 'main', 'protection main', 'anti coupure', 'lebon', 'wintersafe', 'metalfit']):
            return 'Protection Main'
        # Protection Pied (PRIORITÉ : avant hygiène pour éviter confusion avec "gel")
        if any(word in nom_lower for word in ['chaussure', 'botte', 'sabot', 'pied', 'semelle', 'uvex', 'hydroflex', 'atlas', 'klima']):
            return 'Protection Pied'
        # Vêtements de protection
        if any(word in nom_lower for word in ['veste', 'blouson', 'gilet', 'pantalon', 'combinaison', 'manchette']):
            if any(word in nom_lower for word in ['haute visibilité', 'fluo', 'réfléchissant']):
                return 'Vêtements Haute Visibilité'
            return 'Protection Corps'
        # Outils
        if any(word in nom_lower for word in ['outil', 'clé', 'tournevis', 'marteau', 'perceuse', 'scie', 'couteau', 'lame', 'retractable', 'composition maintenance', 'facom', 'trousse', 'enrouleur', 'câble', 'prises', 'mètre', 'pliant', 'mesure']):
            return 'Outils'
        # Éclairage
        if any(word in nom_lower for word in ['lampe', 'éclairage', 'torche', 'projecteur']):
            return 'Éclairage'
        # Marquage
        if any(word in nom_lower for word in ['marquage', 'étiquette', 'panneau', 'peinture', 'bombe', 'craie', 'markal', 'edding', 'pinceau', 'virole']):
            return 'Marquage'
        # Bureau
        if any(word in nom_lower for word in ['bureau', 'papier', 'stylo', 'classeur', 'agraffeuse', 'imprimante', 'carnet', 'oxford', 'spirale', 'ciseaux', 'roller', 'correction', 'tipp-ex', 'surligneur', 'stabilo', 'toner', 'bostitch', 'taille crayon', 'post it', 'recharge', 'graphite', 'agrafes', 'porte mine', 'staedtler', 'fineliner', 'pilot']):
            return 'Bureau'
        # Nettoyage
        if any(word in nom_lower for word in ['nettoyage', 'produit', 'détergent', 'désinfectant', 'sac poubelle', 'balai', 'manche', 'conteneur', 'lavette', 'microfibre', 'balayette', 'spartex', 'eau de javel', 'spray', 'tugalin', 'glasreiniger']):
            return 'Nettoyage'
        # Hygiène (éviter les semelles gel)
        if any(word in nom_lower for word in ['lotion', 'protectrice', 'lindesa', 'shampoings', 'hygiène', 'savon', 'papier toilette', 'pommade', 'lingette', 'protection peau']) or ('gel' in nom_lower and 'semelle' not in nom_lower):
            return 'Hygiène'
        # No Touch
        if any(word in nom_lower for word in ['aimant', 'neodyme', 'puissant']):
            return 'No Touch'
        # EPI Général
        if any(word in nom_lower for word in ['protection', 'sécurité', 'epi', 'équipement']):
            return 'EPI Général'
        return 'Divers'
    
    # Appliquer la recatégorisation INTELLIGENTE (respecte les déplacements manuels)
    for idx, row in normalized_df.iterrows():
        new_category = categorize_article(row['Nom'], row['Description'])
        normalized_df.loc[idx, 'Description'] = new_category
    
    return len(normalized_df[normalized_df['Description'] == category])

def display_articles_grid(articles_df):
    """Affiche les articles en grille moderne avec cartes"""
    if articles_df.empty:
        st.info("Aucun article à afficher.")
        return
    
    # Filtres avancés
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    with col_filter1:
        price_range = st.select_slider(
            "💰 Gamme de prix",
            options=["Tous", "0-10€", "10-50€", "50-100€", "100€+"],
            value="Tous"
        )
    with col_filter2:
        sort_by = st.selectbox(
            "📊 Trier par",
            ["Nom", "Prix croissant", "Prix décroissant", "Référence"]
        )
    with col_filter3:
        view_mode = st.radio(
            "👁️ Affichage",
            ["Grille", "Liste"],
            horizontal=True
        )
    
    # Appliquer les filtres
    filtered_df = articles_df.copy()
    
    # Filtre prix
    if price_range != "Tous":
        if price_range == "0-10€":
            filtered_df = filtered_df[filtered_df['Prix'] <= 10]
        elif price_range == "10-50€":
            filtered_df = filtered_df[(filtered_df['Prix'] > 10) & (filtered_df['Prix'] <= 50)]
        elif price_range == "50-100€":
            filtered_df = filtered_df[(filtered_df['Prix'] > 50) & (filtered_df['Prix'] <= 100)]
        elif price_range == "100€+":
            filtered_df = filtered_df[filtered_df['Prix'] > 100]
    
    # Tri
    if sort_by == "Prix croissant":
        filtered_df = filtered_df.sort_values('Prix')
    elif sort_by == "Prix décroissant":
        filtered_df = filtered_df.sort_values('Prix', ascending=False)
    elif sort_by == "Référence":
        ref_col = get_ref_col(filtered_df)
        filtered_df = filtered_df.sort_values(ref_col)
    else:  # Nom
        filtered_df = filtered_df.sort_values('Nom')
    
    # Affichage selon le mode
    if view_mode == "Grille":
        display_grid_view(filtered_df)
    else:
        display_list_view(filtered_df)

def display_grid_view(articles_df):
    """Affichage en grille moderne avec cartes produits"""
    ref_col = get_ref_col(articles_df)
    
    # Pagination
    items_per_page = 12
    total_items = len(articles_df)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    if total_pages > 1:
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        
        current_page = st.session_state.get('current_page', 1)
        
        with col_prev:
            if st.button("← Précédent", disabled=current_page <= 1):
                st.session_state.current_page = max(1, current_page - 1)
                st.rerun()
        
        with col_info:
            st.markdown(f"<div style='text-align: center; padding: 8px;'>Page {current_page} sur {total_pages}</div>", unsafe_allow_html=True)
        
        with col_next:
            if st.button("Suivant →", disabled=current_page >= total_pages):
                st.session_state.current_page = min(total_pages, current_page + 1)
                st.rerun()
    else:
        current_page = 1
    
    # Calculer les indices pour la pagination
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_articles = articles_df.iloc[start_idx:end_idx]
    
    # Affichage en grille 3 colonnes
    cols = st.columns(3)
    for idx, (_, article) in enumerate(page_articles.iterrows()):
        with cols[idx % 3]:
            # Carte produit moderne
            with st.container():
                st.markdown(f"""
                <div style='
                    border: 1px solid #e0e0e0; 
                    border-radius: 10px; 
                    padding: 15px; 
                    margin: 10px 0;
                    background: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                '>
                    <h4 style='margin: 0 0 10px 0; color: #1f2937;'>{article['Nom'][:40]}{'...' if len(article['Nom']) > 40 else ''}</h4>
                    <p style='margin: 5px 0; color: #6b7280; font-size: 0.9em;'>Réf: {article[ref_col]}</p>
                    <p style='margin: 5px 0; color: #6b7280; font-size: 0.9em;'>Cat: {article['Description']}</p>
                    <div style='margin: 10px 0;'>
                        <span style='font-size: 1.2em; font-weight: bold; color: #059669;'>{article['Prix']:.2f}€</span>
                        <span style='color: #6b7280; font-size: 0.9em;'> / {article['Unitée']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Boutons d'action
                col_qty, col_add = st.columns([1, 2])
                with col_qty:
                    qty = st.number_input("Qté", min_value=1, max_value=50, value=1, key=f"qty_grid_{idx}_{article[ref_col]}")
                with col_add:
                    if st.button("🛒 Ajouter", key=f"add_grid_{idx}_{article[ref_col]}", use_container_width=True):
                        success = add_to_cart(article, qty)
                        if success:
                            st.toast(f"✅ {qty}x {article['Nom'][:20]}... ajouté !", icon="✅")
                        st.rerun()

def display_list_view(articles_df):
    """Affichage en liste compacte"""
    ref_col = get_ref_col(articles_df)
    
    for idx, (_, article) in enumerate(articles_df.iterrows()):
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{article['Nom']}**")
                st.caption(f"Réf: {article[ref_col]} • {article['Description']}")
            
            with col2:
                st.markdown(f"**{article['Prix']:.2f}€**")
                st.caption(f"{article['Unitée']}")
            
            with col3:
                qty = st.number_input("", min_value=1, max_value=50, value=1, key=f"qty_list_{idx}_{article[ref_col]}", label_visibility="collapsed")
                if st.button("➕", key=f"add_list_{idx}_{article[ref_col]}", use_container_width=True):
                    add_to_cart(article, qty)
                    st.rerun()
            
            st.divider()

def show_catalogue():
    """Affiche le catalogue des articles avec IA intelligente"""
    
    # Header moderne avec statistiques en temps réel
    col_title, col_stats, col_ai = st.columns([2, 1, 1])
    
    with col_title:
        st.markdown("### 🛡️ Catalogue FLUX/PARA")
    
    with col_stats:
        # Statistiques rapides avec cache
        try:
            stats = get_cached_statistics()
            st.metric("📊 Total commandes", stats['total_orders'], delta=None)
        except:
            pass
    
    with col_ai:
        # Toggle IA
        ai_enabled = st.checkbox("🤖 Assistant IA", value=True, help="Active les suggestions intelligentes")
    
    budget_used = calculate_cart_total()
    budget_remaining = MAX_CART_AMOUNT - budget_used
    
    # Affichage du budget avec style moderne et barre de progression
    col_budget, col_search = st.columns([1, 2])
    with col_budget:
        progress_percent = min(budget_used / MAX_CART_AMOUNT, 1.0)
        if budget_remaining > 0:
            st.success(f"💰 Budget: {budget_remaining:.2f}€")
        else:
            st.error(f"🚨 Dépassé: {abs(budget_remaining):.2f}€")
        
        # Barre de progression moderne
        st.progress(progress_percent, text=f"Utilisé: {progress_percent*100:.1f}%")
    
    with col_search:
        # Barre de recherche globale moderne
        search_query = st.text_input(
            "🔍 Recherche globale", 
            placeholder="Tapez un nom, référence, marque...",
            help="Recherche dans tous les articles du catalogue"
        )
    
    # Catégories avec cache intelligent pour les compteurs
    try:
        cached_categories = get_cached_categories()
        categories = list(cached_categories.keys())
        category_counts = cached_categories
    except:
        # Fallback si le cache échoue
        categories = [
            "Protection Tête", "Protection Auditive", "Protection Oculaire", "Protection Respiratoire",
            "Protection Main", "Protection Pied", "Protection Corps", "Vêtements Haute Visibilité",
            "Oxycoupage", "EPI Général", "No Touch",
            "Outils", "Éclairage", "Marquage", "Bureau", "Nettoyage", "Hygiène", "Divers"
        ]
        category_counts = {cat: count_articles_in_category(cat) for cat in categories}
    
    # IA et détection de doublons
    user_id = st.session_state.get('current_user', {}).get('id')
    current_cart = st.session_state.get('cart', [])
    
    # Panneau de suggestions IA
    if ai_enabled and user_id:
        show_ai_suggestions_panel(user_id, current_cart)
    
    # Détection de doublons supprimée (gênante et s'accumule)
    
    
    # Recherche globale prioritaire
    if search_query and search_query.strip():
        st.markdown(f"### 🔍 Résultats pour '{search_query}'")
        search_results = search_articles_globally(search_query)
        if search_results.empty:
            st.info("Aucun article trouvé pour cette recherche.")
        else:
            display_articles_grid(search_results)
            
            # Recommandations contextuelles basées sur la recherche
            if ai_enabled and not search_results.empty:
                first_result = search_results.iloc[0].to_dict()
                recommendations = get_contextual_recommendations(first_result)
                
                if recommendations:
                    st.markdown("### 💡 Recommandations IA liées")
                    rec_cols = st.columns(min(4, len(recommendations)))
                    
                    for i, rec in enumerate(recommendations[:4]):
                        with rec_cols[i]:
                            article = rec['article']
                            reason = rec['reason']
                            
                            st.markdown(f"""
                            <div style="border: 1px solid #667eea; border-radius: 10px; padding: 10px; margin: 5px 0; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));">
                                <strong>{article.get('Nom', '')[:25]}...</strong><br>
                                <small>💡 {reason}</small><br>
                                <small>💰 {article.get('Prix', 0)}€</small>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("➕ Ajouter", key=f"rec_add_{i}_{article.get('N° Référence', '')}"):
                                add_to_cart(article)
                                st.success(f"✅ {article.get('Nom', '')[:20]} ajouté!")
                                st.rerun()
    elif not st.session_state.get('selected_category'):
        st.markdown("### 📋 Sélectionnez une catégorie")
        
        # Boutons style icône avec émojis industriels
        categories = [
            "Protection Tête", "Protection Auditive", "Protection Oculaire", "Protection Respiratoire",
            "Protection Main", "Protection Pied", "Protection Corps", "Vêtements Haute Visibilité",
            "Oxycoupage", "EPI Général", "No Touch",
            "Outils", "Éclairage", "Marquage", "Bureau", "Nettoyage", "Hygiène", "Divers"
        ]
        
        # Style pour boutons plus carrés
        st.markdown("""
        <style>
        .stButton > button {
            height: 80px;
            border-radius: 8px;
            font-size: 0.9em;
            white-space: normal;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Affichage moderne avec animations et compteurs
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        cols = st.columns(4)
        for i, category in enumerate(categories):
            with cols[i % 4]:
                emoji = get_category_emoji(category)
                count = category_counts.get(category, 0)
                if count > 0:
                    # Style dynamique selon le nombre d'articles
                    button_type = "primary" if count > 10 else "secondary"
                    if st.button(f"{emoji} {category}\n📦 {count} articles", 
                               key=f"cat_{category}", 
                               use_container_width=True,
                               type=button_type):
                        st.session_state.selected_category = category
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        category = st.session_state.selected_category
        emoji = get_category_emoji(category)
        if st.button("← Retour aux catégories", key="back_to_categories_btn"):
            st.session_state.selected_category = None
            st.rerun()
        st.markdown(f"#### {emoji} {category}")
        
        # Charger les articles
        articles_df = load_articles()
        
        # Système de regroupement automatique par mots-clés
        normalized_df = articles_df.copy()
        
        # Routage intelligent basé sur les mots-clés dans les noms
        def categorize_article(nom, description_actuelle):
            nom_lower = str(nom).lower()
            
            # PRIORITÉ : Respecter les déplacements manuels
            # Si l'article a été manuellement déplacé vers une catégorie valide, on la conserve
            valid_categories = [
                "Protection Tête", "Protection Auditive", "Protection Oculaire", "Protection Respiratoire",
                "Protection Main", "Protection Pied", "Protection Corps", "Vêtements Haute Visibilité",
                "Oxycoupage", "EPI Général", "No Touch",
                "Outils", "Éclairage", "Marquage", "Bureau", "Nettoyage", "Hygiène", "Divers"
            ]
            if str(description_actuelle) in valid_categories:
                return str(description_actuelle)
            
            # Sinon, appliquer le routage automatique pour les nouveaux articles
            # Oxycoupage (priorité car spécialisé)
            if any(word in nom_lower for word in ['chaleur', 'espuna', 'alumini', 'oxycoup', 'tablier', 
                                                  'cagoule', 'cache cou', 'guêtre', 'guetre', 'collier', 'allumeur', 
                                                  'brosse', 'fire resistant', 'ignifug', 'sertissage']):
                return 'Oxycoupage'
            
            # Protection Tête
            if any(word in nom_lower for word in ['casque', 'heaume', 'protection tête']):
                return 'Protection Tête'
            
            # Protection Auditive
            if any(word in nom_lower for word in ['bouchon', 'oreille', 'auditif', 'antibruit']):
                return 'Protection Auditive'
            
            # Protection Oculaire
            if any(word in nom_lower for word in ['lunette', 'oculaire', 'visière', 'deltaplus', 'ambric', 'bollé', 'bolle', 'cobra', 'transparente', 'pacaya', 'tracpsi']):
                return 'Protection Oculaire'
            
            # Protection Respiratoire
            if any(word in nom_lower for word in ['masque', 'respiratoire', 'filtre', 'cartouche']):
                return 'Protection Respiratoire'
            
            # Protection Main
            if any(word in nom_lower for word in ['gant', 'main', 'protection main', 'anti coupure', 'lebon', 'wintersafe', 'metalfit']):
                return 'Protection Main'
            
            # Protection Pied
            if any(word in nom_lower for word in ['chaussure', 'botte', 'sabot', 'pied', 'semelle', 'uvex', 'hydroflex', 'atlas', 'klima']):
                return 'Protection Pied'
            
            # Protection Tête (ajout jugulaire)
            if any(word in nom_lower for word in ['jugulaire']):
                return 'Protection Tête'
            
            # Vêtements de protection
            if any(word in nom_lower for word in ['veste', 'blouson', 'gilet', 'pantalon', 'combinaison', 'manchette']):
                if any(word in nom_lower for word in ['haute visibilité', 'fluo', 'réfléchissant']):
                    return 'Vêtements Haute Visibilité'
                return 'Protection Corps'
            
            # Autres catégories spécialisées (NON-EPI)
            if any(word in nom_lower for word in ['outil', 'clé', 'tournevis', 'marteau', 'perceuse', 'scie', 'couteau', 'lame', 'retractable', 'composition maintenance', 'facom', 'trousse', 'enrouleur', 'câble', 'prises']):
                return 'Outils'
            if any(word in nom_lower for word in ['lampe', 'éclairage', 'torche', 'projecteur']):
                return 'Éclairage'
            if any(word in nom_lower for word in ['marquage', 'étiquette', 'panneau', 'peinture', 'bombe', 'craie', 'markal', 'edding', 'pinceau', 'virole']):
                return 'Marquage'
            if any(word in nom_lower for word in ['bureau', 'papier', 'stylo', 'classeur', 'agraffeuse', 'imprimante', 'carnet', 'oxford', 'spirale', 'ciseaux', 'roller', 'correction', 'tipp-ex', 'surligneur', 'stabilo', 'toner', 'bostitch', 'taille crayon', 'post it', 'recharge', 'graphite', 'agrafes', 'porte mine', 'staedtler', 'fineliner', 'pilot']):
                return 'Bureau'
            if any(word in nom_lower for word in ['mètre', 'pliant', 'mesure', 'qualité']):
                return 'Outils'
            # Nettoyage et entretien
            if any(word in nom_lower for word in ['nettoyage', 'produit', 'détergent', 'désinfectant', 'sac poubelle', 'balai', 'manche', 'conteneur', 'lavette', 'microfibre', 'balayette', 'spartex', 'eau de javel', 'spray', 'tugalin', 'glasreiniger']):
                return 'Nettoyage'
            
            # Hygiène et soins personnels (éviter les semelles gel)
            if any(word in nom_lower for word in ['lotion', 'protectrice', 'lindesa', 'shampoings', 'hygiène', 'savon', 'papier toilette', 'pommade', 'lingette', 'protection peau']) or ('gel' in nom_lower and 'semelle' not in nom_lower):
                return 'Hygiène'
            
            # No Touch (articles spéciaux)
            if any(word in nom_lower for word in ['aimant', 'neodyme', 'puissant']):
                return 'No Touch'
            
            # EPI Général : seulement les vrais équipements de protection non classés ailleurs
            if any(word in nom_lower for word in ['protection', 'sécurité', 'epi', 'équipement']):
                return 'EPI Général'
            
            # Le reste va dans Divers (non-EPI)
            return 'Divers'
        
        # Appliquer la recatégorisation INTELLIGENTE (respecte les déplacements manuels)
        for idx, row in normalized_df.iterrows():
            new_category = categorize_article(row['Nom'], row['Description'])
            normalized_df.loc[idx, 'Description'] = new_category
        
        articles_category = normalized_df[normalized_df['Description'] == category]
        
        # Regrouper les articles par nom de base
        articles_groupes = {}
        for idx, article in articles_category.iterrows():
            nom_complet = article['Nom']
            
            if 'taille' in nom_complet.lower():
                # Détecter différents formats de taille : "Taille 42", "Taille 36/38", "Taille L", etc.
                taille_match = re.search(r'taille\s+([a-zA-Z0-9?/]+)', nom_complet, re.IGNORECASE)
                if taille_match:
                    taille = taille_match.group(1)
                    nom_base = re.sub(r'\s+taille\s+[a-zA-Z0-9?/]+', '', nom_complet, flags=re.IGNORECASE).strip()
                else:
                    nom_base = nom_complet
                    taille = "?"
            else:
                nom_base = nom_complet
                taille = None
            
            if nom_base not in articles_groupes:
                articles_groupes[nom_base] = {
                    'prix': float(article['Prix']),
                    'tailles': {},
                    'article_simple': None
                }
            
            if taille:
                articles_groupes[nom_base]['tailles'][taille] = {'article': article, 'index': idx}
            else:
                articles_groupes[nom_base]['article_simple'] = {'article': article, 'index': idx}
        
        # Afficher les groupes
        for nom_base, infos in articles_groupes.items():
            with st.container():
                st.markdown(f"### {nom_base}")
                st.markdown(f"💰 **{infos['prix']:.2f}€**")
                
                if infos['tailles']:
                    st.markdown("**Tailles disponibles:**")
                    
                    def sort_tailles_intelligent(item):
                        taille = item[0]
                        tailles_lettres = {'XS': 1, 'S': 2, 'M': 3, 'L': 4, 'XL': 5, 'XXL': 6, 'XXXL': 7}
                        
                        if taille in tailles_lettres:
                            return (0, tailles_lettres[taille])
                        
                        try:
                            return (1, int(taille))
                        except (ValueError, TypeError):
                            return (2, taille)
                    
                    tailles_triees = sorted(infos['tailles'].items(), key=sort_tailles_intelligent)
                    
                    for i in range(0, len(tailles_triees), 6):
                        cols = st.columns(6)
                        for j, (taille, data) in enumerate(tailles_triees[i:i+6]):
                            with cols[j]:
                                if st.button(f"🛒 {taille}", key=f"taille_{data['index']}", use_container_width=True):
                                    add_to_cart(data['article'], 1)
                                    st.toast(f"✅ Taille {taille} ajoutée !", icon="✅")
                                    st.rerun()
                else:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        quantity = st.number_input("Quantité", min_value=1, max_value=50, value=1, key=f"qty_{infos['article_simple']['index']}")
                    with col2:
                        if st.button("➕ Ajouter", key=f"add_{infos['article_simple']['index']}", use_container_width=True):
                            add_to_cart(infos['article_simple']['article'], quantity)
                            st.rerun()
                
                st.divider()

def show_orders_history():
    """Affiche l'historique des commandes avec correction du décodage des articles"""
    st.markdown("### 📋 Historique global - Administration")
    
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, contremaître, equipe, articles_json, total_prix, statut
                FROM commandes 
                ORDER BY date DESC
            """)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, contremaître, equipe, articles_json, total_prix, statut
                FROM commandes 
                ORDER BY date DESC
            """)
        
        orders = cursor.fetchall()
        conn.close()
        
        if orders:
            for order in orders:
                order_id, date, contremaitre, equipe, articles_json, total_prix, statut = order
                
                with st.expander(f"🛒 Commande #{order_id} - {contremaitre} ({equipe}) - {total_prix}€", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"📅 **Date:** {date}")
                        st.write(f"👤 **Contremaître:** {contremaitre}")
                        st.write(f"👷‍♂️ **Équipe:** {equipe}")
                        st.write(f"💰 **Total:** {total_prix}€")
                        st.write(f"📋 **Statut:** {statut}")
                        
                        st.markdown("#### 📦 Articles commandés:")
                        
                        # AFFICHAGE SIMPLE DES NOMS D'ARTICLES
                        try:
                            articles = json.loads(articles_json) if isinstance(articles_json, str) else articles_json
                            if not isinstance(articles, list):
                                articles = [articles]
                            for article in articles:
                                if isinstance(article, dict) and 'Nom' in article:
                                    st.write(f"• {article['Nom']}")
                                elif isinstance(article, dict):
                                    # Si pas de 'Nom', essayer d'autres clés
                                    nom = article.get('nom', article.get('name', 'Article sans nom'))
                                    st.write(f"• {nom}")
                                else:
                                    st.write(f"• {str(article)}")
                                
                        except json.JSONDecodeError:
                            st.error("❌ Erreur de lecture des articles")
                        except Exception as e:
                            st.error(f"❌ Erreur affichage articles: {e}")
                    
                    with col2:
                        if st.button(f"🗑️ Supprimer", key=f"delete_order_{order_id}"):
                            if delete_commande(order_id):
                                st.success("✅ Commande supprimée")
                                st.rerun()
                            else:
                                st.error("❌ Erreur suppression")
        else:
            st.info("Aucune commande dans l'historique")
            
    except Exception as e:
        st.error(f"Erreur chargement historique: {e}")

def show_validation_page():
    """Page de validation des commandes pour gestionnaires"""
    st.markdown("### ✅ Validation des commandes - Gestionnaire")
    
    # Récupérer commandes en attente
    commandes_attente = get_pending_orders()
    
    if not commandes_attente:
        st.info("📭 Aucune commande en attente de validation")
        return
    
    for commande in commandes_attente:
        order_id, date, contremaitre, equipe, articles_json, total_prix = commande
        
        with st.expander(f"🛒 Commande #{order_id} - {contremaitre} ({equipe}) - {total_prix}€"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"📅 **Date:** {date}")
                st.write(f"👤 **Contremaître:** {contremaitre}")
                st.write(f"👷‍♂️ **Équipe:** {equipe}")
                st.write(f"💰 **Total:** {total_prix}€")
                
                # Afficher articles
                articles = json.loads(articles_json)
                st.write(f"**Articles ({len(articles)}):**")
                for article in articles[:3]:  # Afficher 3 premiers
                    st.write(f"• {article['Nom']}")
                if len(articles) > 3:
                    st.write(f"... et {len(articles)-3} autres")
            
            with col2:
                if st.button(f"✅ Valider", key=f"approve_{order_id}", use_container_width=True):
                    approve_order(order_id, contremaitre, equipe, total_prix)
                    st.success("✅ Commande validée !")
                    st.rerun()
            
            with col3:
                if st.button(f"❌ Rejeter", key=f"reject_{order_id}", use_container_width=True):
                    reject_order(order_id, contremaitre)
                    st.error("❌ Commande rejetée")
                    st.rerun()

def send_approval_email(order_id, contremaitre, equipe, total_prix, articles_count):
    """Envoie email au gestionnaire pour validation"""
    try:
        # Email du gestionnaire (à configurer)
        GESTIONNAIRE_EMAIL = "gestionnaire@flux-para.com"
        
        subject = f"🛒 Nouvelle commande #{order_id} - Validation requise"
        
        body = f"""
        Bonjour,
        
        Une nouvelle commande nécessite votre validation :
        
        📋 Commande #{order_id}
        👤 Contremaître: {contremaitre}
        👷‍♂️ Équipe: {equipe}
        💰 Total: {total_prix}€
        📦 Articles: {articles_count}
        
        🔗 Connectez-vous à FLUX/PARA Commander pour valider:
        http://192.168.1.163:8502
        
        Cordialement,
        Système FLUX/PARA Commander
        """
        
        # Utiliser la fonction d'envoi email existante
        send_email_notification(GESTIONNAIRE_EMAIL, subject, body)
        return True
        
    except Exception as e:
        st.error(f"Erreur envoi email: {e}")
        return False

def approve_order(order_id, contremaitre, equipe=None, total_prix=None):
    """Valide une commande"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE commandes 
                SET statut = 'Validée', date_validation = %s
                WHERE id = %s
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), order_id))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE commandes 
                SET statut = 'Validée', date_validation = ?
                WHERE id = ?
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), order_id))
        
        conn.commit()
        conn.close()
        
        # Envoyer email de confirmation au contremaître
        send_approval_notification(contremaitre, order_id, "validée")
        
        # Notifier le technicien Denis Busoni
        send_technician_notification("denis.busoni@arcelormittal.com", order_id, contremaitre, equipe or "N/A", total_prix or 0)
        
        return True
        
    except Exception as e:
        st.error(f"Erreur validation: {e}")
        return False

def reject_order(order_id, contremaitre):
    """Rejette une commande"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE commandes 
                SET statut = 'Rejetée', date_validation = %s
                WHERE id = %s
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), order_id))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE commandes 
                SET statut = 'Rejetée', date_validation = ?
                WHERE id = ?
            """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), order_id))
        
        conn.commit()
        conn.close()
        
        # Envoyer email de rejet
        send_approval_notification(contremaitre, order_id, "rejetée")
        return True
        
    except Exception as e:
        st.error(f"Erreur rejet: {e}")
        return False

def send_technician_notification(tech_email, order_id, contremaitre, equipe, total_prix):
    """Notifie le technicien Denis Busoni qu'une commande validée l'attend"""
    try:
        subject = f"🔧 Nouvelle commande à traiter #{order_id} - FLUX/PARA"
        body = f"""
        Bonjour Denis,
        
        Une nouvelle commande validée attend votre traitement :
        
        📋 Commande #{order_id}
        👤 Contremaître: {contremaitre}
        👷‍♂️ Équipe: {equipe}
        💰 Montant: {total_prix}€
        
        📍 Action requise :
        1. Connectez-vous à l'application FLUX/PARA Commander
        2. Allez dans "🛠️ Traitement"
        3. Cliquez "▶️ Prendre en charge" pour cette commande
        
        Merci pour votre réactivité !
        
        Cordialement,
        Système FLUX/PARA Commander
        """
        
        send_email_notification(tech_email, subject, body)
        st.success(f"📧 Technicien notifié : {tech_email}")
        
    except Exception as e:
        st.warning(f"Email technicien non envoyé: {e}")

def get_pending_orders():
    """Récupère les commandes en attente de validation"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, contremaître, equipe, articles_json, total_prix
                FROM commandes 
                WHERE statut = 'En attente'
                ORDER BY date DESC
            """)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, contremaître, equipe, articles_json, total_prix
                FROM commandes 
                WHERE statut = 'En attente'
                ORDER BY date DESC
            """)
        
        orders = cursor.fetchall()
        conn.close()
        return orders
        
    except Exception as e:
        st.error(f"Erreur récupération commandes: {e}")
        return []

def send_approval_notification(contremaitre, order_id, statut):
    """Envoie email de notification au contremaître (validation/rejet)"""
    try:
        # Récupérer l'email du contremaître depuis la base
        user_email = get_user_email(contremaitre)
        
        if statut == "validée":
            subject = f"✅ Commande #{order_id} VALIDÉE"
            body = f"""
            Bonjour {contremaitre},
            
            ✅ Bonne nouvelle ! Votre commande #{order_id} a été VALIDÉE par le gestionnaire.
            
            🚀 Votre commande va être traitée et livrée prochainement.
            
            Vous pouvez consulter le statut dans l'historique de FLUX/PARA Commander.
            
            Cordialement,
            Système FLUX/PARA Commander
            """
        else:  # rejetée
            subject = f"❌ Commande #{order_id} REJETÉE"
            body = f"""
            Bonjour {contremaitre},
            
            ❌ Votre commande #{order_id} a été REJETÉE par le gestionnaire.
            
            💡 Contactez votre gestionnaire pour connaître les raisons du rejet.
            Vous pouvez créer une nouvelle commande corrigée.
            
            Cordialement,
            Système FLUX/PARA Commander
            """
        
        if user_email:
            send_email_notification(user_email, subject, body)
        return True
        
    except Exception as e:
        st.error(f"Erreur notification: {e}")
        return False

def get_user_email(username):
    """Récupère l'email d'un utilisateur"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE username = %s", (username,))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE username = ?", (username,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
        
    except Exception as e:
        return None

def delete_user(user_id):
    """Supprime un utilisateur (Postgres uniquement)"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        if user and user[0] == 'admin':
            conn.close()
            return False, "Impossible de supprimer l'administrateur principal"
        try:
            cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
            conn.commit()
        except Exception as e:
            conn.close()
            return False, f"Erreur suppression SQL : {e}"
        conn.close()
        st.cache_data.clear()
        return True, "Utilisateur supprimé avec succès"
    except Exception as e:
        st.error(f"Erreur suppression: {e}")
        return False, f"Erreur suppression: {e}"

def user_can_add_articles():
    """Vérifie si l'utilisateur actuel peut ajouter des articles"""
    user_info = st.session_state.get('current_user', {})
    
    # Admin peut toujours ajouter
    if user_info.get('role') == 'admin':
        return True
    
    # Vérifier la permission spécifique
    username = user_info.get('username')
    if not username:
        return False
    
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT can_add_articles 
            FROM users 
            WHERE username = ?
        """, (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return bool(result[0]) if result[0] is not None else False
        
        return False
        
    except Exception as e:
        return False

def user_can_view_stats():
    """Vérifie si l'utilisateur peut voir les statistiques"""
    user_info = st.session_state.get('current_user', {})
    
    # Admin peut toujours voir
    if user_info.get('role') == 'admin':
        return True
    
    # Vérifier la permission spécifique
    username = user_info.get('username')
    if not username:
        return False
    
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT can_view_stats 
            FROM users 
            WHERE username = ?
        """, (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return bool(result[0]) if result[0] is not None else False
        
        return False
        
    except Exception as e:
        return False


def user_can_view_all_orders():
    """Vérifie si l'utilisateur peut voir toutes les commandes"""
    user_info = st.session_state.get('current_user', {})
    
    if user_info.get('role') == 'admin':
        return True
    
    username = user_info.get('username')
    if not username:
        return False
    
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
        
        cursor = conn.cursor()
        
        if USE_POSTGRESQL:
            cursor.execute("SELECT can_view_all_orders FROM users WHERE username = %s", (username,))
        else:
            cursor.execute("SELECT can_view_all_orders FROM users WHERE username = ?", (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return bool(result[0]) if result[0] is not None else False
        
        return False
        
    except Exception as e:
        return False


def update_user_permissions(user_id, permissions):
    """Met à jour les permissions (Postgres ou SQLite selon config)"""
    try:
        # Postgres attend des BOOLEAN, pas des int (1/0)
        def to_bool(v):
            return bool(v) if v is not None else False
        p_add = to_bool(permissions.get('can_add_articles', False))
        p_stats = to_bool(permissions.get('can_view_stats', False))
        p_all = to_bool(permissions.get('can_view_all_orders', False))
        p_move = to_bool(permissions.get('can_move_articles', False))
        p_del = to_bool(permissions.get('can_delete_articles', False))
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users 
                SET can_add_articles = %s, 
                    can_view_stats = %s, 
                    can_view_all_orders = %s,
                    can_move_articles = %s,
                    can_delete_articles = %s
                WHERE id = %s
            """, (p_add, p_stats, p_all, p_move, p_del, user_id))
            conn.commit()
            conn.close()
            if st.session_state.get('current_user') and st.session_state.current_user.get('id') == user_id:
                reload_current_user_permissions()
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            # SQLite utilise INTEGER (0/1) pour ces colonnes
            cursor.execute("""
                UPDATE users 
                SET can_add_articles = ?, 
                    can_view_stats = ?, 
                    can_view_all_orders = ?,
                    can_move_articles = ?,
                    can_delete_articles = ?
                WHERE id = ?
            """, (int(p_add), int(p_stats), int(p_all), int(p_move), int(p_del), user_id))
            conn.commit()
            conn.close()
            if st.session_state.get('current_user') and st.session_state.current_user.get('id') == user_id:
                reload_current_user_permissions_sqlite()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erreur mise à jour permissions: {e}")
        return False

def reload_current_user_permissions():
    """Recharge les permissions de l'utilisateur connecté depuis la base"""
    if not st.session_state.get('current_user'):
        return
    
    try:
        username = st.session_state.current_user.get('username')
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, can_add_articles, can_view_stats, can_view_all_orders, 
                   can_move_articles, can_delete_articles
            FROM users WHERE username = %s
        """, (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            st.session_state.current_user['role'] = result[0]
            st.session_state.current_user['can_add_articles'] = bool(result[1])
            st.session_state.current_user['can_view_stats'] = bool(result[2])
            st.session_state.current_user['can_view_all_orders'] = bool(result[3])
            st.session_state.current_user['can_move_articles'] = bool(result[4])
            st.session_state.current_user['can_delete_articles'] = bool(result[5])
            
    except Exception as e:
        st.error(f"Erreur rechargement permissions: {e}")

def create_user(username, password, equipe, fonction, couleur_preferee="DT770", can_add_articles=0, can_view_stats=0, can_view_all_orders=0, role="user"):
    """Crée un utilisateur (Postgres uniquement) avec must_change_password à True et mot de passe initial basé sur la couleur préférée."""
    try:
        pwd_hash = hashlib.sha256(couleur_preferee.encode()).hexdigest()  # Mot de passe initial = couleur préférée hashée
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        # Ajout du champ must_change_password si besoin
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT TRUE")
            conn.commit()
        except:
            pass
        cursor.execute("""
            INSERT INTO users (username, password_hash, equipe, fonction,
             role, can_add_articles, can_view_stats, can_view_all_orders, couleur_preferee, must_change_password)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            username, pwd_hash, equipe, fonction, role,
            bool(can_add_articles), bool(can_view_stats), 
            bool(can_view_all_orders), couleur_preferee, True
        ))
        conn.commit()
        conn.close()
        st.cache_data.clear()
        st.rerun()
        return True, "✅ Utilisateur créé avec succès ! (Mot de passe initial = couleur préférée)"
    except Exception as e:
        return False, f"❌ Erreur création utilisateur : {e}"

def get_category_emoji(category):
    emoji_map = {
        # Nouvelles catégories par zone de protection - THÈME INDUSTRIEL
        'Protection Tête': '⛑️',  # Casque de chantier
        'Protection Auditive': '🔇',  # Anti-bruit
        'Protection Oculaire': '🥽',  # Lunettes de protection
        'Protection Respiratoire': '😷',  # Masque
        'Protection Main': '🧤',  # Gants
        'Protection Pied': '🥾',  # Chaussures de sécurité
        'Protection Corps': '🦺',  # Gilet de sécurité
        'Vêtements Haute Visibilité': '⚠️',  # Haute visibilité
        
        # Spécialisations métier - THÈME INDUSTRIEL
        'Oxycoupage': '🔥',  # Flamme/chaleur
        'No Touch': '⛔',  # Interdiction/spécial
        
        # Autres - THÈME INDUSTRIEL/USINE
        'Outils': '🔧',  # Clé à molette
        'Éclairage': '💡',  # Ampoule
        'Marquage': '🏭',  # Usine/marquage industriel
        'Bureau': '📋',  # Presse-papiers
        'Nettoyage': '🧹',  # Balai industriel
        'Hygiène': '🚿',  # Douche/hygiène industrielle
        'Divers': '⚙️',  # Engrenage industriel
        'EPI Général': '🛡️',  # Bouclier de protection
        
        # Anciennes catégories (compatibilité)
        'Chaussures': '👟',
        'Veste Blouson': '🧥', 
        'Gants': '🧤',
        'Casque': '⛑️',
        'Lunette': '🥽',
        'Gilet': '🦺',
        'Masque': '😷',
        'Veste Oxycoupeur': '🔥',
        'Sécurité': '🛡️',
        'Pantalon': '👖',
        'Sous Veste': '👕',
        'Protection': '🦺',
        'Outil': '🛠️',
        'Lampe': '💡',
        'Imprimante': '🖨️',
        'EPI': '🛡️'
    }
    return emoji_map.get(category, '📦')

def get_user_orders(user_id):
    """Récupère les commandes d'un utilisateur"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, total_prix, 'validée' as status, articles_json 
                FROM commandes 
                WHERE user_id = %s 
                ORDER BY date DESC
            """, (user_id,))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, total_prix, 'validée' as status, articles_json 
                FROM commandes 
                WHERE user_id = ? 
                ORDER BY date DESC
            """, (user_id,))
        
        orders = cursor.fetchall()
        conn.close()
        return orders
        
    except Exception as e:
        st.error(f"Erreur chargement commandes: {e}")
        return []

def show_my_orders() -> None:
    """Affiche les commandes de l'utilisateur connecté (admin OU contremaître)."""
    user = get_current_user()
    if not user:
        st.warning("Veuillez vous connecter.")
        return

    try:
        commandes = get_user_orders(user["id"])          # (id, date, total, statut, articles_json)
    except Exception as e:
        st.error(f"Erreur chargement commandes : {e}")
        return

    if not commandes:
        st.info("📭 Aucune commande trouvée.")
        return

    for order_id, date_cmd, total, statut, articles_json in commandes:
        with st.expander(f"🧾 Commande #{order_id} – {date_cmd} – {total:.2f} €"):
            st.write(f"**Statut :** {statut}")

            # --- décodage sûr du champ articles_json -------------------------
            try:
                contenu = json.loads(articles_json) if articles_json else []
            except Exception:
                contenu = articles_json            # déjà python ?
            if not isinstance(contenu, list):
                contenu = [contenu]                # on force une liste
            # ------------------------------------------------------------------

            st.markdown("#### 📦 Articles commandés")
            if not contenu:
                st.write("Aucun article.")
            for art in contenu:
                try:
                    nom, prix = parse_article_for_display(art)
                    ligne = f"• {nom}"
                    if prix is not None:
                        ligne += f" – {float(prix):.2f} €"
                    st.write(ligne)
                except Exception as e:
                    st.error(f"❌ Impossible d'afficher un article : {e}")

def create_missing_columns():
    """Ajoute les colonnes manquantes à la base de données"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Ajouter les colonnes de permissions si elles n'existent pas
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN can_add_articles INTEGER DEFAULT 0")
        except:
            pass
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN can_view_stats INTEGER DEFAULT 0")
        except:
            pass
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN can_view_all_orders INTEGER DEFAULT 0")
        except:
            pass
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"❌ Erreur mise à jour BDD: {e}")
        return False

def get_all_users():
    """Récupère tous les utilisateurs (version SQL directe qui fonctionne)"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        direct_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT id, username, equipe, fonction,
                   COALESCE(can_add_articles, false),
                   COALESCE(can_view_stats, false),
                   COALESCE(can_view_all_orders, false),
                   role,
                   COALESCE(can_move_articles, false),
                   COALESCE(can_delete_articles, false)
            FROM users
            ORDER BY id
        """)
        users = cursor.fetchall()
        conn.close()

        return users
        
    except Exception as e:
        st.error(f"Erreur : {e}")
        return []

def show_admin_page():
    """Page complète d'administration des utilisateurs"""
    st.markdown("# 👥 Gestion des utilisateurs - Administration")
    st.info(f"DATABASE_URL utilisée : `{os.environ.get('DATABASE_URL', 'Aucune (mode SQLite local)' )}`")
    # ... le reste de ta fonction ...

def create_new_user(username, password, equipe, fonction, can_add_articles, can_view_stats, can_view_all_orders, role):
    """Crée un nouvel utilisateur avec toutes les permissions"""
    try:
        ensure_users_table()

        pwd_hash = hashlib.sha256(password.encode()).hexdigest()

        conn   = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (username, password_hash, equipe, fonction,
             role, can_add_articles, can_view_stats, can_view_all_orders)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username,
                pwd_hash,
                equipe,
                fonction,
                role,
                int(can_add_articles),
                int(can_view_stats),
                int(can_view_all_orders),
            ),
        )

        conn.commit()
        conn.close()
        return True

    except sqlite3.IntegrityError:
        st.error("❌ Nom d'utilisateur déjà utilisé.")
    except Exception as e:
        st.error(f"❌ Erreur création utilisateur : {e}")
    return False

def delete_user(user_id):
    """Supprime un utilisateur de la base de données"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Vérifier que ce n'est pas l'admin principal
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user and user[0] == 'admin':
            conn.close()
            return False, "Impossible de supprimer l'administrateur principal"
        
        # Supprimer l'utilisateur
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return True, "Utilisateur supprimé avec succès"
        
    except Exception as e:
        return False, f"Erreur suppression: {e}"

def reload_current_user_permissions_sqlite():
    """Recharge les permissions de l'utilisateur connecté depuis SQLite"""
    if not st.session_state.get('current_user'):
        return
    
    try:
        username = st.session_state.current_user.get('username')
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, can_add_articles, can_view_stats, can_view_all_orders, 
                   can_move_articles, can_delete_articles
            FROM users WHERE username = ?
        """, (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            st.session_state.current_user['role'] = result[0]
            st.session_state.current_user['can_add_articles'] = bool(result[1])
            st.session_state.current_user['can_view_stats'] = bool(result[2])
            st.session_state.current_user['can_view_all_orders'] = bool(result[3])
            st.session_state.current_user['can_move_articles'] = bool(result[4])
            st.session_state.current_user['can_delete_articles'] = bool(result[5])
            
    except Exception as e:
        st.error(f"Erreur rechargement permissions SQLite: {e}")

# --- À placer juste au-dessus des fonctions qui accèdent à la table users ---
def ensure_users_table():
    """Crée la table users et AJOUTE les colonnes manquantes si besoin."""
    conn   = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # schéma complet
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            equipe  TEXT,
            fonction TEXT,
            role    TEXT DEFAULT 'user',
            can_add_articles    INTEGER DEFAULT 0,
            can_view_stats      INTEGER DEFAULT 0,
            can_view_all_orders INTEGER DEFAULT 0
        )
    """)

    # ── si la table existait déjà on ajoute les colonnes manquantes ──
    expected = {
        "password_hash":        "TEXT",
        "equipe":               "TEXT",
        "fonction":             "TEXT",
        "role":                 "TEXT DEFAULT 'user'",
        "can_add_articles":     "INTEGER DEFAULT 0",
        "can_view_stats":       "INTEGER DEFAULT 0",
        "can_view_all_orders":  "INTEGER DEFAULT 0",
    }

    cursor.execute("PRAGMA table_info(users)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    for col, col_type in expected.items():
        if col not in existing_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")

    conn.commit()
    conn.close()

# --- GESTION DES ARTICLES : SUPPRESSION ---------------------------------
def delete_article(reference: str, ref_col: str | None = None) -> tuple[bool, str]:
    """Supprime un article (référence) du catalogue (PostgreSQL ou CSV)."""
    if USE_POSTGRESQL:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM articles WHERE reference = %s", (str(reference),))
            if not cursor.fetchone():
                conn.close()
                return False, "Référence introuvable"
            cursor.execute("DELETE FROM articles WHERE reference = %s", (str(reference),))
            conn.commit()
            conn.close()
            try:
                load_articles.clear()
            except Exception:
                pass
            st.cache_data.clear()
            return True, "✅ Article supprimé avec succès"
        except Exception as e:
            return False, f"❌ Erreur suppression article : {e}"
    try:
        df = pd.read_csv(ARTICLES_CSV_PATH, encoding='utf-8', usecols=[0,1,2,3,4])
        df.columns = ['N° Référence', 'Nom', 'Description', 'Prix', 'Unitée']
        ref_col = ref_col or get_ref_col(df)
        if reference not in df[ref_col].astype(str).values:
            return False, "Référence introuvable"
        df = df[df[ref_col].astype(str) != str(reference)]
        df.to_csv(ARTICLES_CSV_PATH, index=False, encoding='utf-8')
        try:
            load_articles.clear()
        except Exception:
            pass
        st.cache_data.clear()
        return True, "✅ Article supprimé avec succès"
    except Exception as e:
        return False, f"❌ Erreur suppression article : {e}"

def move_article_category(reference: str, new_category: str) -> tuple[bool, str]:
    """Déplace un article vers une nouvelle catégorie (description)."""
    if USE_POSTGRESQL:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT description FROM articles WHERE reference = %s", (str(reference),))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, "Référence introuvable"
            old_category = row[0] or ""
            cursor.execute("UPDATE articles SET description = %s WHERE reference = %s", (new_category, str(reference)))
            conn.commit()
            conn.close()
            try:
                load_articles.clear()
            except Exception:
                pass
            st.cache_data.clear()
            return True, f"✅ Article déplacé de '{old_category}' vers '{new_category}'"
        except Exception as e:
            return False, f"❌ Erreur déplacement : {e}"
    try:
        df = pd.read_csv(ARTICLES_CSV_PATH, encoding='utf-8', usecols=[0,1,2,3,4])
        df.columns = ['N° Référence', 'Nom', 'Description', 'Prix', 'Unitée']
        ref_col = get_ref_col(df)
        if reference not in df[ref_col].astype(str).values:
            return False, "Référence introuvable"
        mask = df[ref_col].astype(str) == str(reference)
        old_category = df.loc[mask, 'Description'].iloc[0]
        df.loc[mask, 'Description'] = new_category
        df.to_csv(ARTICLES_CSV_PATH, index=False, encoding='utf-8')
        try:
            load_articles.clear()
        except Exception:
            pass
        st.cache_data.clear()
        return True, f"✅ Article déplacé de '{old_category}' vers '{new_category}'"
    except Exception as e:
        return False, f"❌ Erreur déplacement : {e}"

# 🔽 placez-la dans la zone « fonctions commandes », juste après get_user_orders()
def delete_order(order_id: int, current_user: dict) -> tuple[bool, str]:
    """
    Supprime une commande.
    – Un admin peut supprimer n'importe quelle commande
    – Un user ne peut supprimer que les siennes
    """
    try:
        if USE_POSTGRESQL:
            conn   = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM commandes WHERE id = %s", (order_id,))
        else:
            conn   = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM commandes WHERE id = ?", (order_id,))

        row = cursor.fetchone()
        if not row:
            conn.close()
            return False, "Commande introuvable"

        owner_id = row[0]
        if current_user["role"] != "admin" and owner_id != current_user["id"]:
            conn.close()
            return False, "⛔ Action non autorisée"

        # suppression effective
        if USE_POSTGRESQL:
            cursor.execute("DELETE FROM commandes WHERE id = %s", (order_id,))
        else:
            cursor.execute("DELETE FROM commandes WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return True, "✅ Commande supprimée avec succès"

    except Exception as e:
        return False, f"❌ Erreur suppression commande : {e}"

# ------------------------------------------------------------------
# Helper : normalise n'importe quel format d'article enregistré
# ------------------------------------------------------------------
def parse_article_for_display(raw) -> Tuple[str, Optional[float]]:
    """
    Retourne (nom, prix) quel que soit le format de `raw` :
    - dict : {'Nom': 'Casque', 'Prix': 9.9}
    - str JSON  : '{"Nom":"Casque","Prix":9.9}'
    - str brute : "Casque"
    """
    if isinstance(raw, dict):
        nom  = raw.get("Nom") or raw.get("nom") or raw.get("name") or "Article"
        prix = raw.get("Prix") or raw.get("prix") or raw.get("price")
        return nom, prix

    if isinstance(raw, str):
        # JSON ?
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                return parse_article_for_display(obj)
        except Exception:
            pass
        # Chaîne python ?
        try:
            obj = ast.literal_eval(raw)
            if isinstance(obj, dict):
                return parse_article_for_display(obj)
        except Exception:
            pass
        return raw, None               # juste le texte

    return str(raw), None

# helper pour récupérer l'utilisateur courant (facilement ré-utilisable)
def get_current_user():
    return st.session_state.get("current_user") or {}

# ─── constants de permission (clé bool en BDD / session) ──────────
PERM_ADD_ARTICLES     = "can_add_articles"
PERM_VIEW_STATS       = "can_view_stats"
PERM_VIEW_ALL_ORDERS  = "can_view_all_orders"

def has_perm(user: dict | None, perm: str) -> bool:
    """True si l'utilisateur est admin OU possède explicitement la permission."""
    return bool(user) and (user.get("role") == "admin" or user.get(perm, 0))

def build_sidebar():
    user = get_current_user()
    st.sidebar.page_link("catalogue", label="📕 Catalogue")
    st.sidebar.page_link("cart",      label="🛒 Panier")
    st.sidebar.page_link("orders",    label="📦 Mes commandes")
    if has_perm(user, PERM_VIEW_STATS):
        st.sidebar.page_link("stats", label="📊 Statistiques")
    if user and user["role"] == "admin":
        st.sidebar.page_link("users", label="👤 Utilisateurs")

# ------------------------------------------------------------------
# Quelle est la colonne "référence" dans le CSV ?
# ------------------------------------------------------------------
def get_ref_col(df: pd.DataFrame) -> str:
    """Retourne le nom de la colonne Référence réellement présente."""
    possibles = ["Référence", "N° Référence", "Reference", "Ref"]
    for col in possibles:
        if col in df.columns:
            return col
    # dernier recours : on prend la première colonne
    return df.columns[0]

def show_user_admin_page() -> None:
    st.markdown("## 👥 Gestion des utilisateurs – Administration")
    st.write("---")

    # ------ FORMULAIRE DE CRÉATION ---------------------------------
    with st.expander("➕ Créer un nouvel utilisateur", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("Nom d'utilisateur*", key="new_username")
            new_password = st.text_input("Mot de passe*", type="password", key="new_password")
            equipes = ["DIRECTION", "FLUX", "PARA", "MAINTENANCE", "QUALITE", "LOGISTIQUE", "AUTRE"]
            new_equipe = st.selectbox("Équipe", equipes, key="new_equipe_select")
            if new_equipe == "AUTRE":
                new_equipe = st.text_input("Précisez l'équipe", key="new_equipe_autre")
            fonctions = ["contremaître", "RTZ", "technicien", "opérateur", "gestionnaire", "AUTRE"]
            new_fonction = st.selectbox("Fonction", fonctions, key="new_fonction_select")
            if new_fonction == "AUTRE":
                new_fonction = st.text_input("Précisez la fonction", key="new_fonction_autre")
            new_couleur = st.text_input("Couleur préférée*", key="new_couleur_preferee")
        with col2:
            st.markdown("### Permissions")
            p_add   = st.checkbox("Peut ajouter des articles", key="p_add")
            p_stats = st.checkbox("Peut voir les statistiques", key="p_stats")
            p_all   = st.checkbox("Peut voir toutes les commandes", key="p_all")
            role    = st.selectbox("Rôle", ["user", "contremaitre", "admin"], key="role_select")
        if st.button("Créer l'utilisateur", use_container_width=True, key="btn_create_user"):
            if not new_username or not new_password or not new_couleur:
                st.error("Veuillez remplir tous les champs obligatoires.")
            else:
                if user_exists(new_username):
                    st.error("❌ Ce nom d'utilisateur existe déjà.")
                else:
                    ok, msg = create_user(
                        new_username,
                        new_password,
                        new_equipe,
                        new_fonction,
                        couleur_preferee=new_couleur,
                        can_add_articles=int(p_add),
                        can_view_stats=int(p_stats),
                        can_view_all_orders=int(p_all),
                        role=role
                    )
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

    # ------ LISTE & ÉDITION ----------------------------------------
    st.markdown("### 📄 Utilisateurs existants")
    for user_data in get_all_users():
        if len(user_data) == 8:
            uid, uname, equipe, fonction, p_add, p_stats, p_all, role = user_data
            p_move, p_delete = False, False
        else:
            uid, uname, equipe, fonction, p_add, p_stats, p_all, role, p_move, p_delete = user_data
        with st.expander(f"👤 {uname} – {role.upper()} ({equipe})", expanded=False):
            st.write(f"ID : {uid}")
            st.write(f"Fonction : {fonction}")
            st.write("#### ✏️ Modifier")

            role_options = ["user", "contremaitre", "admin"]
            role_safe = role if role in role_options else "admin"
            e_role   = st.selectbox(
                "Rôle",
                role_options,
                index=role_options.index(role_safe),
                key=f"role_{uid}",
            )
            c1, c2, c3 = st.columns(3)
            with c1:
                e_add = st.checkbox(
                    "Ajouter articles",
                    value=bool(p_add),
                    key=f"add_{uid}",
                )
                e_move = st.checkbox(
                    "🔄 Déplacer articles",
                    value=bool(p_move),
                    key=f"move_{uid}",
                )
            with c2:
                e_stats = st.checkbox(
                    "Voir stats",
                    value=bool(p_stats),
                    key=f"stats_{uid}",
                )
                e_delete = st.checkbox(
                    "🗑️ Supprimer articles",
                    value=bool(p_delete),
                    key=f"delete_{uid}",
                )
            with c3:
                e_all = st.checkbox(
                    "Toutes commandes",
                    value=bool(p_all),
                    key=f"all_{uid}",
                )

            b_save, b_del = st.columns(2)
            with b_save:
                if st.button(
                    "💾 Sauvegarder",
                    key=f"save_{uid}",
                    use_container_width=True,
                ):
                    permissions = {
                        'can_add_articles': int(e_add),
                        'can_view_stats': int(e_stats),
                        'can_view_all_orders': int(e_all),
                        'can_move_articles': int(e_move),
                        'can_delete_articles': int(e_delete)
                    }
                    ok = update_user_permissions(uid, permissions)
                    if ok:
                        st.success("✅ Permissions mises à jour !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la mise à jour")

            with b_del:
                if uname != "admin" and st.button(
                    f"🗑️ Supprimer {uname}",
                    key=f"del_{uid}",
                    use_container_width=True,
                ):
                    success, msg = delete_user(uid)
                    if success:
                        st.warning("Utilisateur supprimé.")
                        st.rerun()
                    else:
                        st.error(msg)
                        if "constraint" in msg.lower() or "foreign key" in msg.lower():
                            st.info("💡 Impossible de supprimer cet utilisateur car il a des commandes. Supprime-les d'abord dans l'historique si besoin.")

st.markdown(
    """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    """,
    unsafe_allow_html=True
)

# --- Liste globale des équipes ---
EQUIPES = ["DIRECTION", "FLUX", "PARA", "MAINTENANCE", "QUALITE", "LOGISTIQUE", "FINISSAGE"]

# --- Fonction pour vérifier l'existence d'un utilisateur (insensible à la casse) ---
def user_exists(username):
    """Vérifie si un utilisateur existe (Postgres uniquement)"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE LOWER(username) = %s", (username.lower(),))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    except Exception:
        return False

def to_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return val == 1
    if isinstance(val, str):
        return val == "1"
    return False

def refresh_current_user_permissions():
    """Recharge les permissions de l'utilisateur courant (Postgres uniquement)"""
    user_info = st.session_state.get('current_user', {})
    username = user_info.get('username')
    if not username:
        return
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, can_add_articles, can_view_stats, can_view_all_orders
            FROM users WHERE username = %s
        """, (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            st.session_state.current_user['role'] = result[0]
            st.session_state.current_user['can_add_articles'] = bool(result[1])
            st.session_state.current_user['can_view_stats'] = bool(result[2])
            st.session_state.current_user['can_view_all_orders'] = bool(result[3])
            
    except Exception as e:
        st.error(f"Erreur rafraîchissement permissions : {e}")

def show_force_password_change():
    st.markdown("### 🔒 Changement de mot de passe obligatoire")
    st.warning("Pour des raisons de sécurité, vous devez définir un nouveau mot de passe.")
    with st.form("force_change_pwd_form"):
        new_pwd = st.text_input("Nouveau mot de passe", type="password")
        confirm_pwd = st.text_input("Confirmer le mot de passe", type="password")
        submitted = st.form_submit_button("Changer le mot de passe")
        if submitted:
            if not new_pwd or not confirm_pwd:
                st.error("Veuillez remplir les deux champs.")
            elif new_pwd != confirm_pwd:
                st.error("Les mots de passe ne correspondent pas.")
            elif len(new_pwd) < 6:
                st.error("Le mot de passe doit contenir au moins 6 caractères.")
            else:
                user = st.session_state.get('current_user', {})
                try:
                    conn = psycopg2.connect(DATABASE_URL)
                    cursor = conn.cursor()
                    pwd_hash = hashlib.sha256(new_pwd.encode()).hexdigest()
                    cursor.execute("UPDATE users SET password_hash = %s, must_change_password = FALSE WHERE id = %s", (pwd_hash, user['id']))
                    conn.commit()
                    conn.close()
                    st.success("Mot de passe changé avec succès !")
                    st.session_state.current_user['must_change_password'] = False
                    st.session_state.page = 'catalogue'
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors du changement de mot de passe : {e}")

def update_commande_status(commande_id, nouveau_statut, technicien_nom=None, commentaire=None, date_livraison_prevue=None):
    """Met à jour le statut d'une commande"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Préparer la requête selon les paramètres fournis
            if technicien_nom and commentaire:
                cursor.execute("""
                    UPDATE commandes 
                    SET statut = %s, traitee_par = %s, date_traitement = %s, 
                        commentaire_technicien = %s, date_livraison_prevue = %s
                    WHERE id = %s
                """, (nouveau_statut, technicien_nom, datetime.now(), commentaire, date_livraison_prevue, commande_id))
            elif technicien_nom:
                cursor.execute("""
                    UPDATE commandes 
                    SET statut = %s, traitee_par = %s, date_traitement = %s
                    WHERE id = %s
                """, (nouveau_statut, technicien_nom, datetime.now(), commande_id))
            else:
                cursor.execute("""
                    UPDATE commandes 
                    SET statut = %s
                    WHERE id = %s
                """, (nouveau_statut, commande_id))
                
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            if technicien_nom and commentaire:
                cursor.execute("""
                    UPDATE commandes 
                    SET statut = ?, traitee_par = ?, date_traitement = ?, 
                        commentaire_technicien = ?, date_livraison_prevue = ?
                    WHERE id = ?
                """, (nouveau_statut, technicien_nom, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                     commentaire, date_livraison_prevue, commande_id))
            elif technicien_nom:
                cursor.execute("""
                    UPDATE commandes 
                    SET statut = ?, traitee_par = ?, date_traitement = ?
                    WHERE id = ?
                """, (nouveau_statut, technicien_nom, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), commande_id))
            else:
                cursor.execute("""
                    UPDATE commandes 
                    SET statut = ?
                    WHERE id = ?
                """, (nouveau_statut, commande_id))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Erreur mise à jour statut commande: {e}")
        return False

def get_commandes_by_status(statut=None):
    """Récupère les commandes par statut"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            if statut:
                cursor.execute("""
                    SELECT id, date, contremaître, equipe, articles_json, total_prix, 
                           statut, traitee_par, date_traitement, commentaire_technicien, 
                           date_livraison_prevue, urgence
                    FROM commandes 
                    WHERE statut = %s
                    ORDER BY date DESC
                """, (statut,))
            else:
                cursor.execute("""
                    SELECT id, date, contremaître, equipe, articles_json, total_prix, 
                           statut, traitee_par, date_traitement, commentaire_technicien, 
                           date_livraison_prevue, urgence
                    FROM commandes 
                    ORDER BY date DESC
                """)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            if statut:
                cursor.execute("""
                    SELECT id, date, contremaître, equipe, articles_json, total_prix, 
                           statut, traitee_par, date_traitement, commentaire_technicien, 
                           date_livraison_prevue, urgence
                    FROM commandes 
                    WHERE statut = ?
                    ORDER BY date DESC
                """, (statut,))
            else:
                cursor.execute("""
                    SELECT id, date, contremaître, equipe, articles_json, total_prix, 
                           statut, traitee_par, date_traitement, commentaire_technicien, 
                           date_livraison_prevue, urgence
                    FROM commandes 
                    ORDER BY date DESC
                """)
        
        orders = cursor.fetchall()
        conn.close()
        return orders
        
    except Exception as e:
        st.error(f"Erreur récupération commandes: {e}")
        return []


def get_commande_details(commande_id):
    """Récupère les détails complets d'une commande pour l'édition"""
    try:
        conn = sqlite3.connect('commandes.db')
        cursor = conn.cursor()
        
        # D'abord vérifier si les nouvelles colonnes existent, sinon les créer
        cursor.execute("PRAGMA table_info(commandes)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Ajouter les colonnes manquantes si nécessaire
        if 'commentaire' not in columns:
            cursor.execute("ALTER TABLE commandes ADD COLUMN commentaire TEXT")
        if 'traitee_par' not in columns:
            cursor.execute("ALTER TABLE commandes ADD COLUMN traitee_par TEXT")
        if 'date_traitement' not in columns:
            cursor.execute("ALTER TABLE commandes ADD COLUMN date_traitement TEXT")
        if 'commentaire_technicien' not in columns:
            cursor.execute("ALTER TABLE commandes ADD COLUMN commentaire_technicien TEXT")
        if 'date_livraison_prevue' not in columns:
            cursor.execute("ALTER TABLE commandes ADD COLUMN date_livraison_prevue TEXT")
        if 'urgence' not in columns:
            cursor.execute("ALTER TABLE commandes ADD COLUMN urgence TEXT DEFAULT 'Normal'")
        
        conn.commit()
        
        cursor.execute("""
            SELECT id, date, contremaître, equipe, articles_json, total_prix, 
                   commentaire, statut, traitee_par, date_traitement, 
                   commentaire_technicien, date_livraison_prevue, urgence
            FROM commandes WHERE id = ?
        """, (commande_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'date': result[1],
                'contremaitre': result[2],
                'equipe': result[3],
                'articles': json.loads(result[4]) if result[4] else [],
                'total_prix': result[5],
                'commentaire': result[6] or '',
                'statut': result[7] or 'En attente',
                'traitee_par': result[8] or '',
                'date_traitement': result[9] or '',
                'commentaire_technicien': result[10] or '',
                'date_livraison_prevue': result[11] or '',
                'urgence': result[12] or 'Normal'
            }
        return None
        
    except Exception as e:
        st.error(f"Erreur récupération commande: {e}")
        return None

def update_commande_articles(commande_id, nouveaux_articles, nouveau_total, commentaire_modification):
    """Met à jour les articles d'une commande et ajoute un commentaire de modification"""
    try:
        conn = sqlite3.connect('commandes.db')
        cursor = conn.cursor()
        
        # Mettre à jour les articles et le total
        cursor.execute("""
            UPDATE commandes 
            SET articles_json = ?, total_prix = ?, commentaire_technicien = ?
            WHERE id = ?
        """, (json.dumps(nouveaux_articles), nouveau_total, commentaire_modification, commande_id))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Erreur mise à jour commande: {e}")
        return False

def show_edit_commande_form(commande_id, commande_data):
    """Affiche le formulaire d'édition d'une commande pour les techniciens"""
    st.markdown("### ✏️ Édition de la commande")
    
    with st.form(f"edit_commande_{commande_id}"):
        st.markdown(f"**📋 Commande #{commande_id}** - {commande_data['contremaitre']} ({commande_data['equipe']})")
        
        # Charger les articles disponibles
        articles_df = load_articles()
        
        # Articles actuels de la commande
        articles_actuels = commande_data['articles']
        
        st.markdown("**📦 Articles actuels :**")
        
        # Créer une liste modifiable des articles
        nouveaux_articles = []
        articles_supprimes = []
        total_modifie = 0
        
        # Afficher et permettre modification des articles existants
        for i, article in enumerate(articles_actuels):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"• {article['Nom']}")
            
            with col2:
                quantite_actuelle = 1  # Quantité par défaut
                # Essayer de récupérer la quantité si elle existe
                if isinstance(article, dict) and 'quantite' in article:
                    quantite_actuelle = article['quantite']
                
                nouvelle_quantite = st.number_input(
                    "Qté", 
                    min_value=0, 
                    value=quantite_actuelle,
                    key=f"qty_existing_{commande_id}_{i}"
                )
            
            with col3:
                prix_unitaire = float(article['Prix'])
                st.write(f"{prix_unitaire:.2f}€")
            
            with col4:
                supprimer = st.checkbox(
                    "🗑️", 
                    key=f"delete_existing_{commande_id}_{i}",
                    help="Supprimer cet article"
                )
            
            # Ajouter à la nouvelle liste si pas supprimé et quantité > 0
            if not supprimer and nouvelle_quantite > 0:
                article_modifie = article.copy()
                article_modifie['quantite'] = nouvelle_quantite
                nouveaux_articles.extend([article_modifie] * nouvelle_quantite)
                total_modifie += prix_unitaire * nouvelle_quantite
            elif supprimer:
                articles_supprimes.append(article['Nom'])
        
        st.markdown("---")
        st.markdown("**➕ Ajouter de nouveaux articles :**")
        
        # Permettre d'ajouter de nouveaux articles
        nombre_nouveaux = st.number_input(
            "Nombre d'articles à ajouter", 
            min_value=0, 
            max_value=10, 
            value=0,
            key=f"nb_new_{commande_id}"
        )
        
        for i in range(nombre_nouveaux):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                article_selectionne = st.selectbox(
                    f"Article {i+1}",
                    options=articles_df['Nom'].tolist(),
                    key=f"new_article_{commande_id}_{i}"
                )
            
            with col2:
                quantite_nouvelle = st.number_input(
                    "Quantité",
                    min_value=1,
                    value=1,
                    key=f"new_qty_{commande_id}_{i}"
                )
            
            # Récupérer les détails de l'article sélectionné
            if article_selectionne:
                article_info = articles_df[articles_df['Nom'] == article_selectionne].iloc[0].to_dict()
                prix_unitaire = float(article_info['Prix'])
                
                # Ajouter à la liste
                for _ in range(quantite_nouvelle):
                    nouveaux_articles.append(article_info)
                    total_modifie += prix_unitaire
        
        st.markdown("---")
        st.markdown(f"**💰 Nouveau total : {total_modifie:.2f}€**")
        
        # Commentaire de modification
        commentaire_modification = st.text_area(
            "💬 Commentaire sur les modifications (obligatoire)",
            placeholder="Expliquez les raisons des modifications...",
            key=f"comment_modif_{commande_id}"
        )
        
        # Boutons de soumission
        col_submit, col_cancel = st.columns(2)
        
        with col_submit:
            submitted = st.form_submit_button("💾 Sauvegarder les modifications")
        
        with col_cancel:
            cancelled = st.form_submit_button("❌ Annuler")
        
        if submitted:
            if not commentaire_modification.strip():
                st.error("⚠️ Un commentaire est obligatoire pour justifier les modifications !")
            else:
                # Construire le commentaire complet
                commentaire_complet = f"[MODIFICATION] {commentaire_modification}"
                if articles_supprimes:
                    commentaire_complet += f"\n[SUPPRIMÉS] {', '.join(articles_supprimes)}"
                
                if update_commande_articles(commande_id, nouveaux_articles, total_modifie, commentaire_complet):
                    st.success("✅ Commande modifiée avec succès !")
                    st.session_state[f'edit_mode_{commande_id}'] = False
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de la modification")
        
        if cancelled:
            st.session_state[f'edit_mode_{commande_id}'] = False
            st.rerun()

def show_traitement_commandes():
    """Page de traitement des commandes pour les techniciens"""
    st.markdown("### 🔧 Traitement des commandes - Technicien")
    
    user_info = st.session_state.get('current_user', {})
    if not user_info.get("can_add_articles") and user_info.get("role") != "admin":
        st.error("⛔ Accès refusé - Réservé aux techniciens et administrateurs")
        return
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        statut_filtre = st.selectbox(
            "📋 Filtrer par statut",
            ["Toutes", "En attente", "En cours", "Traitée", "Livrée"],
            key="statut_filter"
        )
    
    with col2:
        urgence_filtre = st.selectbox(
            "⚡ Filtrer par urgence", 
            ["Toutes", "Normal", "Urgent", "Très urgent"],
            key="urgence_filter"
        )
    
    with col3:
        equipe_filtre = st.selectbox(
            "👥 Filtrer par équipe",
            ["Toutes", "FLUX", "PARA", "MAINTENANCE", "DIRECTION", "QUALITE", "LOGISTIQUE"],
            key="equipe_filter"
        )
    
    # Récupérer les commandes
    if statut_filtre == "Toutes":
        commandes = get_commandes_by_status()
    else:
        commandes = get_commandes_by_status(statut_filtre)
    
    if not commandes:
        st.info("📭 Aucune commande trouvée")
        return
    
    # Statistiques rapides
    st.markdown("### 📊 Statistiques")
    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
    
    # Compter par statut
    statuts_count = {}
    for cmd in commandes:
        statut = cmd[6] if len(cmd) > 6 and cmd[6] else "En attente"
        statuts_count[statut] = statuts_count.get(statut, 0) + 1
    
    with col_stats1:
        st.metric("🟡 En attente", statuts_count.get("En attente", 0))
    with col_stats2:
        st.metric("🔵 En cours", statuts_count.get("En cours", 0))
    with col_stats3:
        st.metric("🟢 Traitées", statuts_count.get("Traitée", 0))
    with col_stats4:
        st.metric("✅ Livrées", statuts_count.get("Livrée", 0))
    
    st.markdown("---")
    st.markdown("### 📦 Commandes à traiter")
    
    # Afficher les commandes
    for commande in commandes:
        (order_id, date, contremaitre, equipe, articles_json, total_prix, 
         statut, traitee_par, date_traitement, commentaire_technicien, 
         date_livraison_prevue, urgence) = commande + (None,) * (12 - len(commande))
        
        # Appliquer les filtres
        if urgence_filtre != "Toutes" and urgence != urgence_filtre:
            continue
        if equipe_filtre != "Toutes" and equipe != equipe_filtre:
            continue
        
        # Définir la couleur selon le statut
        statut = statut or "En attente"
        if statut == "En attente":
            statut_color = "🟡"
            color_css = "background-color: #fff3cd; border-left: 4px solid #ffc107;"
        elif statut == "En cours":
            statut_color = "🔵"
            color_css = "background-color: #d1ecf1; border-left: 4px solid #17a2b8;"
        elif statut == "Traitée":
            statut_color = "🟢"
            color_css = "background-color: #d4edda; border-left: 4px solid #28a745;"
        elif statut == "Livrée":
            statut_color = "✅"
            color_css = "background-color: #e2e6ea; border-left: 4px solid #6c757d;"
        else:
            statut_color = "❓"
            color_css = "background-color: #f8f9fa; border-left: 4px solid #6c757d;"
        
        # Urgence
        urgence = urgence or "Normal"
        if urgence == "Urgent":
            urgence_emoji = "⚡"
        elif urgence == "Très urgent":
            urgence_emoji = "🚨"
        else:
            urgence_emoji = "📋"
        
        with st.container():
            st.markdown(f"""
            <div style="{color_css} padding: 10px; border-radius: 5px; margin: 10px 0;">
                <h4>{statut_color} Commande #{order_id} - {urgence_emoji} {urgence}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col_info, col_actions = st.columns([2, 1])
            
            with col_info:
                # Informations principales
                col_date, col_total = st.columns(2)
                with col_date:
                    st.write(f"**📅 Date:** {date}")
                with col_total:
                    st.write(f"**💰 Total:** {total_prix}€")
                
                col_contremaitre, col_equipe = st.columns(2)
                with col_contremaitre:
                    st.write(f"**👤 Contremaître:** {contremaitre}")
                with col_equipe:
                    st.write(f"**👷‍♂️ Équipe:** {equipe}")
                
                st.write(f"**📋 Statut:** {statut_color} {statut}")
                
                # Compteur d'articles
                try:
                    nb_articles = len(json.loads(articles_json) if articles_json else [])
                    st.write(f"**📦 Articles:** {nb_articles} article(s)")
                except:
                    st.write(f"**📦 Articles:** Information non disponible")
                
                if traitee_par:
                    st.write(f"**🔧 Traité par:** {traitee_par}")
                if date_traitement:
                    st.write(f"**📅 Date traitement:** {date_traitement}")
                if commentaire_technicien:
                    st.write(f"**💬 Commentaire:** {commentaire_technicien}")
                
                # Afficher les articles avec détails complets
                with st.expander(f"📦 Détails de la commande ({len(json.loads(articles_json) if articles_json else [])} articles)", expanded=False):
                    try:
                        articles = json.loads(articles_json) if isinstance(articles_json, str) else articles_json
                        if not isinstance(articles, list):
                            articles = [articles]
                        
                        # Debug pour comprendre le format
                        # st.write(f"**Debug - Format articles:** {type(articles)} - Nombre: {len(articles)}")
                        # if articles:
                        #     st.write(f"**Debug - Premier article:** {articles[0]}")
                        
                        # Grouper les articles identiques avec approche plus robuste
                        from collections import defaultdict
                        grouped = defaultdict(int)
                        articles_details = {}
                        
                        for article in articles:
                            # Gérer différents formats d'articles
                            if isinstance(article, dict):
                                # Priorité aux clés possibles pour le nom
                                nom = (article.get('Nom') or 
                                      article.get('nom') or 
                                      article.get('name') or 
                                      article.get('Article') or 
                                      f"Article {len(grouped) + 1}")
                                grouped[nom] += 1
                                if nom not in articles_details:
                                    articles_details[nom] = article
                            else:
                                # Si l'article n'est pas un dict, le convertir
                                nom = str(article)
                                grouped[nom] += 1
                                articles_details[nom] = {'Nom': nom, 'Prix': 0}
                        
                        # Créer un tableau des articles
                        if grouped:
                            st.markdown("**📋 Liste des articles :**")
                            
                            # En-tête du tableau
                            col_art, col_qty, col_prix, col_total = st.columns([3, 1, 1, 1])
                            with col_art:
                                st.markdown("**Article**")
                            with col_qty:
                                st.markdown("**Qté**")
                            with col_prix:
                                st.markdown("**Prix unit.**")
                            with col_total:
                                st.markdown("**Total**")
                            
                            st.markdown("---")
                            
                            # Afficher chaque article
                            total_commande = 0
                            for nom, quantite in grouped.items():
                                article_detail = articles_details[nom]
                                
                                # Récupérer le prix avec différentes clés possibles
                                prix_unitaire = 0
                                if isinstance(article_detail, dict):
                                    prix_str = (article_detail.get('Prix') or 
                                              article_detail.get('prix') or 
                                              article_detail.get('price') or 0)
                                    try:
                                        prix_unitaire = float(prix_str)
                                    except (ValueError, TypeError):
                                        prix_unitaire = 0
                                
                                total_article = prix_unitaire * quantite
                                total_commande += total_article
                                
                                col_art, col_qty, col_prix, col_total = st.columns([3, 1, 1, 1])
                                with col_art:
                                    st.write(f"• {nom}")
                                with col_qty:
                                    st.write(f"×{quantite}")
                                with col_prix:
                                    st.write(f"{prix_unitaire:.2f}€")
                                with col_total:
                                    st.write(f"{total_article:.2f}€")
                            
                            st.markdown("---")
                            st.markdown(f"**💰 Total calculé: {total_commande:.2f}€**")
                            
                            # Boutons pour générer les PDF
                            st.markdown("**📄 Génération de documents PDF :**")
                            col_pdf_commande, col_pdf_reception = st.columns(2)
                            
                            with col_pdf_commande:
                                if st.button(f"📄 Bon de commande PDF", key=f"pdf_commande_{order_id}"):
                                    # Préparer les données pour le PDF
                                    commande_data = {
                                        'id': order_id,
                                        'utilisateur': contremaitre,
                                        'equipe': equipe,
                                        'articles': articles,
                                        'total': total_prix,
                                        'date': date
                                    }
                                    
                                    try:
                                        pdf_buffer = generate_commande_pdf(commande_data)
                                        if pdf_buffer:
                                            st.download_button(
                                                label="💾 Télécharger le bon de commande",
                                                data=pdf_buffer,
                                                file_name=f"bon_commande_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                                mime="application/pdf",
                                                key=f"download_commande_{order_id}"
                                            )
                                            st.success("✅ PDF généré avec succès !")
                                        else:
                                            st.error("❌ Erreur lors de la génération du PDF")
                                    except Exception as pdf_e:
                                        st.error(f"❌ Erreur génération PDF: {pdf_e}")
                            
                            with col_pdf_reception:
                                if st.button(f"📋 Bon de réception PDF", key=f"pdf_reception_{order_id}"):
                                    # Préparer les données pour le PDF de réception
                                    commande_data = {
                                        'id': order_id,
                                        'utilisateur': contremaitre,
                                        'equipe': equipe,
                                        'articles': articles,
                                        'total': total_prix,
                                        'date': date
                                    }
                                    
                                    try:
                                        pdf_buffer = generate_bon_reception_pdf(commande_data, order_id)
                                        if pdf_buffer:
                                            st.download_button(
                                                label="💾 Télécharger le bon de réception",
                                                data=pdf_buffer,
                                                file_name=f"bon_reception_{order_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                                mime="application/pdf",
                                                key=f"download_reception_{order_id}"
                                            )
                                            st.success("✅ PDF de réception généré !")
                                        else:
                                            st.error("❌ Erreur lors de la génération du PDF de réception")
                                    except Exception as pdf_e:
                                        st.error(f"❌ Erreur génération PDF réception: {pdf_e}")
                        else:
                            st.warning("⚠️ Aucun article trouvé dans cette commande")
                            # Affichage debug en cas de problème
                            with st.expander("🔍 Debug - Données brutes"):
                                st.write("**Articles bruts:**")
                                st.json(articles[:3] if len(articles) > 3 else articles)
                            
                    except Exception as e:
                        st.error(f"❌ Erreur affichage articles: {e}")
                        with st.expander("🔍 Debug - Informations détaillées"):
                            st.write("**Articles JSON bruts:**", articles_json[:200] if articles_json else "Aucun")
                            try:
                                articles_parsed = json.loads(articles_json) if articles_json else []
                                st.write(f"**Articles parsés:** {type(articles_parsed)}")
                                if articles_parsed:
                                    st.write(f"**Premier élément:** {articles_parsed[0]}")
                            except Exception as debug_e:
                                st.write(f"**Erreur parsing:** {debug_e}")
            
            with col_actions:
                st.markdown("**🔧 Actions**")

                # Bouton d'édition de la commande
                edit_key = f"edit_mode_{order_id}"
                if edit_key not in st.session_state:
                    st.session_state[edit_key] = False

                if not st.session_state[edit_key]:
                    if st.button(f"✏️ Éditer commande", key=f"edit_{order_id}"):
                        st.session_state[edit_key] = True
                        st.rerun()
                else:
                    # Afficher le formulaire d'édition
                    commande_details = get_commande_details(order_id)
                    if commande_details:
                        show_edit_commande_form(order_id, commande_details)
                    return  # Sortir pour afficher seulement l'édition

                
                # Boutons selon le statut actuel
                if statut == "En attente":
                    if st.button(f"▶️ Prendre en charge", key=f"start_{order_id}"):
                        if update_commande_status(order_id, "En cours", user_info['username']):
                            st.success("✅ Commande prise en charge !")
                            st.rerun()
                
                elif statut == "En cours":
                    # Vérifier si on affiche le formulaire de traitement
                    form_key = f"show_complete_form_{order_id}"
                    if form_key not in st.session_state:
                        st.session_state[form_key] = False
                    
                    if not st.session_state[form_key]:
                        if st.button(f"✅ Marquer comme traitée", key=f"complete_{order_id}"):
                            st.session_state[form_key] = True
                            st.rerun()
                    else:
                        st.markdown("**💬 Finaliser le traitement :**")
                        with st.form(f"complete_form_{order_id}"):
                            commentaire = st.text_area(
                                "💬 Commentaire technicien", 
                                placeholder="Ex: Article en rupture, remplacé par réf. 12345, livraison différée...",
                                help="Ce commentaire sera visible par le contremaître dans ses commandes",
                                key=f"comment_{order_id}"
                            )
                            date_livraison = st.date_input("📅 Date livraison prévue", key=f"delivery_{order_id}")
                            
                            col_submit, col_cancel = st.columns(2)
                            with col_submit:
                                submitted = st.form_submit_button("✅ Confirmer traitement")
                            with col_cancel:
                                cancelled = st.form_submit_button("❌ Annuler")
                            
                            if submitted:
                                if update_commande_status(order_id, "Traitée", user_info['username'], 
                                                        commentaire, str(date_livraison)):
                                    st.success("✅ Commande marquée comme traitée !")
                                    st.session_state[form_key] = False
                                    st.rerun()
                            
                            if cancelled:
                                st.session_state[form_key] = False
                                st.rerun()
                elif statut == "Traitée":
                    col_deliver, col_comment = st.columns(2)
                    
                    with col_deliver:
                        if st.button(f"🚚 Marquer comme livrée", key=f"deliver_{order_id}"):
                            if update_commande_status(order_id, "Livrée"):
                                st.success("✅ Commande livrée !")
                                st.rerun()
                    
                    with col_comment:
                        update_comment_key = f"update_comment_{order_id}"
                        if update_comment_key not in st.session_state:
                            st.session_state[update_comment_key] = False
                        
                        if not st.session_state[update_comment_key]:
                            if st.button(f"💬 Ajouter commentaire", key=f"add_comment_{order_id}"):
                                st.session_state[update_comment_key] = True
                                st.rerun()
                        else:
                            with st.form(f"update_comment_form_{order_id}"):
                                new_comment = st.text_area(
                                    "💬 Nouveau commentaire", 
                                    value=commentaire_technicien or "",
                                    placeholder="Ex: Problème résolu, article livré en urgence...",
                                    key=f"new_comment_{order_id}"
                                )
                                
                                col_save, col_cancel_comment = st.columns(2)
                                with col_save:
                                    save_comment = st.form_submit_button("💾 Sauvegarder")
                                with col_cancel_comment:
                                    cancel_comment = st.form_submit_button("❌ Annuler")
                                
                                if save_comment:
                                    if update_commande_status(order_id, "Traitée", user_info['username'], new_comment):
                                        st.success("💬 Commentaire mis à jour !")
                                        st.session_state[update_comment_key] = False
                                        st.rerun()
                                
                                if cancel_comment:
                                    st.session_state[update_comment_key] = False
                                    st.rerun()
                
                # Bouton pour changer l'urgence
                if st.button(f"⚡ Changer urgence", key=f"urgency_{order_id}"):
                    with st.form(f"urgency_form_{order_id}"):
                        nouvelle_urgence = st.selectbox(
                            "Niveau d'urgence", 
                            ["Normal", "Urgent", "Très urgent"],
                            index=["Normal", "Urgent", "Très urgent"].index(urgence),
                            key=f"new_urgency_{order_id}"
                        )
                        urgency_submitted = st.form_submit_button("💾 Sauvegarder")
                        
                        if urgency_submitted:
                            # Ici on devrait ajouter une fonction pour mettre à jour l'urgence
                            st.success("⚡ Urgence mise à jour !")
                            st.rerun()
            
            st.divider()

if __name__ == "__main__":
    main()

