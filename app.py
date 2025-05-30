import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime, timedelta
import io
import time
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import json
import random
import psycopg2

# Imports ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# Configuration de la page
st.set_page_config(
    page_title="🛒 Bienvenue dans Commande Articles et EPI",
    page_icon="🛒",
    layout="wide"
)

# Configuration base de données (nettoyer la logique)
if 'DATABASE_URL' in os.environ:
    # Production Railway avec PostgreSQL
    DATABASE_URL = os.environ['DATABASE_URL']
    USE_POSTGRESQL = True
else:
    # Développement local avec SQLite
    DATABASE_PATH = 'commandes.db'
    USE_POSTGRESQL = False

# === FONCTIONS BASE DE DONNÉES CORRIGÉES ===

def init_database():
    """Créer la base de données et les tables"""
    if USE_POSTGRESQL:
        # PostgreSQL (Railway)
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commandes (
                id SERIAL PRIMARY KEY,
                date TEXT NOT NULL,
                contremaître TEXT NOT NULL,
                equipe TEXT NOT NULL,
                articles_json TEXT NOT NULL,
                total_prix REAL NOT NULL,
                nb_articles INTEGER NOT NULL,
                statut TEXT DEFAULT 'validée'
            )
        ''')
    else:
        # SQLite (Local)
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS commandes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                contremaître TEXT NOT NULL,
                equipe TEXT NOT NULL,
                articles_json TEXT NOT NULL,
                total_prix REAL NOT NULL,
                nb_articles INTEGER NOT NULL,
                statut TEXT DEFAULT 'validée'
            )
        ''')
    
    conn.commit()
    conn.close()

def save_commande_to_db(contremaître, equipe, cart_items, total_prix):
    """Sauvegarder une commande dans la base de données"""
    import pandas as pd
    
    if USE_POSTGRESQL:
        # PostgreSQL (Railway)
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
    else:
        # SQLite (Local)
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
    
    # Conversion ultra-sûre des articles
    cart_safe = []
    for item in cart_items:
        item_safe = {}
        for key, value in item.items():
            try:
                if value is None or (hasattr(pd, 'isna') and pd.isna(value)):
                    item_safe[key] = ""
                elif isinstance(value, (str, int, float, bool)):
                    item_safe[key] = value
                elif hasattr(value, 'item'):
                    item_safe[key] = value.item()
                else:
                    item_safe[key] = str(value)
                    
                if key == 'Prix':
                    item_safe[key] = float(item_safe[key])
                    
            except Exception:
                item_safe[key] = str(value)
        
        cart_safe.append(item_safe)
    
    # Sérialisation JSON
    try:
        articles_json = json.dumps(cart_safe, ensure_ascii=False, default=str)
    except Exception as e:
        articles_json = json.dumps(str(cart_safe), ensure_ascii=False)
    
    date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    nb_articles = len(cart_safe)
    
    if USE_POSTGRESQL:
        # PostgreSQL - Syntaxe %s et RETURNING
        cursor.execute('''
            INSERT INTO commandes (date, contremaître, equipe, articles_json, total_prix, nb_articles)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        ''', (date_now, contremaître, equipe, articles_json, total_prix, nb_articles))
        commande_id = cursor.fetchone()[0]
    else:
        # SQLite - Syntaxe ? et lastrowid
        cursor.execute('''
            INSERT INTO commandes (date, contremaître, equipe, articles_json, total_prix, nb_articles)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date_now, contremaître, equipe, articles_json, total_prix, nb_articles))
        commande_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return commande_id

def get_all_commandes():
    """Récupérer toutes les commandes"""
    if USE_POSTGRESQL:
        # PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
    else:
        # SQLite
        conn = sqlite3.connect(DATABASE_PATH)
    
    df = pd.read_sql_query("SELECT * FROM commandes ORDER BY date DESC", conn)
    conn.close()
    return df

def get_statistics():
    """Calculer les statistiques des commandes"""
    try:
        df_commandes = get_all_commandes()
        
        if len(df_commandes) == 0:
            return {
                'total_commandes': 0,
                'total_depense': 0,
                'df_equipes': pd.DataFrame(),
                'df_contremaitres': pd.DataFrame(),
                'df_mensuel': pd.DataFrame()
            }
        
        # Statistiques globales
        total_commandes = len(df_commandes)
        total_depense = df_commandes['total_prix'].sum()
        
        # Groupement par équipe
        df_equipes = df_commandes.groupby('equipe')['total_prix'].agg(['sum', 'count']).reset_index()
        df_equipes.columns = ['equipe', 'total_prix', 'nb_commandes']
        df_equipes = df_equipes.sort_values('total_prix', ascending=False)
        
        # Groupement par contremaître
        df_contremaitres = df_commandes.groupby('contremaître')['total_prix'].agg(['sum', 'count']).reset_index()
        df_contremaitres.columns = ['contremaître', 'total_prix', 'nb_commandes']
        df_contremaitres = df_contremaitres.sort_values('total_prix', ascending=False)
        
        # Évolution mensuelle
        df_commandes['mois'] = pd.to_datetime(df_commandes['date']).dt.to_period('M')
        df_mensuel = df_commandes.groupby('mois')['total_prix'].sum().reset_index()
        df_mensuel['mois'] = df_mensuel['mois'].astype(str)
        
        return {
            'total_commandes': total_commandes,
            'total_depense': total_depense,
            'df_equipes': df_equipes,
            'df_contremaitres': df_contremaitres,
            'df_mensuel': df_mensuel
        }
        
    except Exception as e:
        return {
            'total_commandes': 0,
            'total_depense': 0,
            'df_equipes': pd.DataFrame(),
            'df_contremaitres': pd.DataFrame(), 
            'df_mensuel': pd.DataFrame()
        }

# Initialiser la base de données au démarrage
init_database()

# === PUIS LE RESTE DU CODE (variables, constantes, etc.) ===

# Variables de session
if 'cart' not in st.session_state:
    st.session_state.cart = []
    
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None

if 'show_search' not in st.session_state:
    st.session_state.show_search = False

# Configuration
MAX_CART_AMOUNT = 1500.0  # Budget maximum autorisé

# Force le rechargement CSS avec un timestamp
css_version = int(time.time())

# CSS simplifié sans les styles email
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 3rem 0;
    margin-bottom: 2rem;
    border-radius: 0 0 20px 20px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.pdf-section {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    text-align: center;
    box-shadow: 0 5px 15px rgba(168, 237, 234, 0.3);
}

.success-message {
    background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
}

.category-card {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    padding: 2rem;
    border-radius: 20px;
    margin: 1rem 0;
    box-shadow: 0 8px 32px rgba(240, 147, 251, 0.3);
    transition: all 0.3s ease;
    border: none;
    cursor: pointer;
    text-align: center;
}

.category-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 45px rgba(240, 147, 251, 0.4);
}

.category-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.category-title {
    font-size: 1.5rem;
    font-weight: bold;
    color: white;
    margin-bottom: 0.5rem;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.category-count {
    color: rgba(255, 255, 255, 0.9);
    font-size: 1rem;
}

.article-card {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 5px 15px rgba(168, 237, 234, 0.3);
    transition: all 0.2s ease;
    border-left: 4px solid #667eea;
}

.article-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(168, 237, 234, 0.4);
}

.article-name {
    font-size: 1.2rem;
    font-weight: bold;
    color: #2d3748;
    margin-bottom: 0.5rem;
}

.article-description {
    color: #4a5568;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
}

.article-price {
    color: #667eea;
    font-weight: bold;
    font-size: 1.1rem;
}

.search-section {
    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    padding: 2rem;
    border-radius: 15px;
    margin: 2rem 0;
    text-align: center;
    box-shadow: 0 5px 15px rgba(252, 182, 159, 0.3);
}

.cart-summary {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    padding: 1.5rem;
    border-radius: 15px;
    margin: 1rem 0;
    box-shadow: 0 5px 15px rgba(168, 237, 234, 0.3);
}

.bounce-in {
    animation: bounceIn 0.6s ease-out;
}

@keyframes bounceIn {
    0% { transform: scale(0); opacity: 0; }
    50% { transform: scale(1.05); opacity: 1; }
    100% { transform: scale(1); }
}

/* Optimisations mobile */
@media (max-width: 768px) {
    .main-header h1 {
        font-size: 1.8rem !important;
    }
    
    .category-card {
        margin-bottom: 1rem !important;
        padding: 1rem !important;
    }
    
    .article-card {
        margin-bottom: 0.8rem !important;
        padding: 0.8rem !important;
    }
    
    .stButton > button {
        width: 100% !important;
        padding: 0.75rem !important;
        font-size: 0.9rem !important;
    }
    
    .css-1d391kg {
        padding: 1rem !important;
    }
}

/* Amélioration des emails sur mobile */
.email-section {
    background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
}

.mobile-friendly-input input {
    font-size: 16px !important;
}
</style>
""", unsafe_allow_html=True)

# Lire et nettoyer les données
@st.cache_data
def load_and_clean_data():
    articles_df = pd.read_csv('articles.csv')
    
    # Nettoyer les données
    df_clean = articles_df[~articles_df['Nom'].str.contains('Nom|N° Référence', na=False)]
    df_clean = df_clean.dropna(subset=['Nom', 'Prix', 'Catégorie'])
    df_clean = df_clean.drop_duplicates(subset=['Nom', 'Catégorie'], keep='first')
    df_clean = df_clean[~df_clean['Catégorie'].str.contains('Catégorie|Article', na=False)]
    df_clean['Prix'] = pd.to_numeric(df_clean['Prix'], errors='coerce')
    df_clean = df_clean.dropna(subset=['Prix'])
    
    return df_clean

articles_df = load_and_clean_data()

# Fonctions utilitaires
def calculate_cart_total():
    return sum(float(item['Prix']) for item in st.session_state.cart if item['Prix'] != 0)

def convert_pandas_to_dict(article):
    """Convertir un article pandas en dictionnaire Python natif"""
    article_dict = {}
    for key, value in article.items():
        if pd.isna(value):  # Gestion des valeurs NaN
            article_dict[key] = ""
        elif isinstance(value, (pd.Series, pd.DataFrame)):
            article_dict[key] = str(value)
        else:
            # Conversion en types Python natifs
            if key == 'Prix':
                article_dict[key] = float(value)
            else:
                article_dict[key] = str(value)
    
    return article_dict

def add_to_cart(article):
    current_total = calculate_cart_total()
    new_total = current_total + float(article['Prix'])
    
    if new_total > MAX_CART_AMOUNT:
        # Messages rigolos aléatoires
        messages_rigolos = [
            "🤯 Eh mais tu vas bouffer la baraque !",
            "😱 Stop ! Tu vas ruiner l'entreprise !",
            "🚨 Alerte ! Le comptable va faire une crise cardiaque !",
            "🤑 Calme-toi Jeff Bezos !",
            "😵 Tu te crois à Disneyland ?!",
            "🛑 Freine tes ardeurs champion !",
            "💸 Tu veux pas acheter l'usine tant qu'on y est ?",
            "🎯 C'est pas Koh Lanta ici !",
            "🚫 Le patron va te passer un savon !",
            "😂 Tu confonds avec ton compte perso ou quoi ?"
        ]
        
        message_rigolo = random.choice(messages_rigolos)
        
        # Popup rigolo avec Streamlit
        st.error(f"❌ {message_rigolo}")
        st.error(f"💰 Budget maximum: {MAX_CART_AMOUNT}€")
        st.error(f"🧮 Total actuel: {current_total:.2f}€ + Article: {article['Prix']}€ = {new_total:.2f}€")
        
        # Animation CSS pour le popup
        st.markdown("""
        <div style="
            background: linear-gradient(45deg, #ff6b6b, #ffa500);
            color: white;
            padding: 1rem;
            border-radius: 15px;
            text-align: center;
            margin: 1rem 0;
            animation: shake 0.5s ease-in-out;
            border: 3px solid #ff4757;
        ">
            <h3>🚨 BUDGET EXPLOSION DÉTECTÉE ! 🚨</h3>
            <p>Redescends sur terre mon pote ! 😄</p>
        </div>
        
        <style>
        @keyframes shake {
            0% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            50% { transform: translateX(5px); }
            75% { transform: translateX(-5px); }
            100% { transform: translateX(0); }
        }
        </style>
        """, unsafe_allow_html=True)
        
    else:
        # Utiliser la fonction de conversion
        article_dict = convert_pandas_to_dict(article)
        st.session_state.cart.append(article_dict)
        st.success(f"✅ {article_dict['Nom']} ajouté au panier!")

def remove_from_cart(index):
    if 0 <= index < len(st.session_state.cart):
        removed_item = st.session_state.cart.pop(index)
        st.warning(f"❌ {removed_item['Nom']} retiré du panier!")

def clear_cart():
    st.session_state.cart = []
    st.info("🛒 Panier vidé !")

def add_multiple_to_cart(article, quantity):
    """Ajouter plusieurs exemplaires d'un article au panier"""
    current_total = calculate_cart_total()
    article_price = float(article['Prix'])
    new_total = current_total + (article_price * quantity)
    
    if new_total > MAX_CART_AMOUNT:
        # Messages encore plus rigolos pour les gros dépassements
        messages_gros_depassement = [
            f"🤯 {quantity}x ?! Tu veux ouvrir ton propre magasin ?!",
            f"😱 {quantity} articles ! Tu te crois dans un supermarché ?",
            f"🚨 {quantity}x ! Arrête le massacre !",
            f"🤑 {quantity} pièces ! T'es millionnaire en secret ?",
            f"😵 {quantity}x ! Le comptable vient de s'évanouir !",
            f"🛑 {quantity} articles ! Tu collectionnes ou tu travailles ?",
            f"💸 {quantity}x ! Tu veux ruiner la boîte !",
            f"😂 {quantity} pièces ! C'est Noël en avance ?"
        ]
        
        message_rigolo = random.choice(messages_gros_depassement)
        
        st.error(f"❌ {message_rigolo}")
        st.error(f"💰 Budget maximum: {MAX_CART_AMOUNT}€")
        st.error(f"🧮 Total actuel: {current_total:.2f}€ + {quantity}x{article_price}€ = {new_total:.2f}€")
        
        # Popup encore plus animé pour les gros dépassements
        st.markdown(f"""
        <div style="
            background: linear-gradient(45deg, #ff4757, #ff3838);
            color: white;
            padding: 1.5rem;
            border-radius: 20px;
            text-align: center;
            margin: 1rem 0;
            animation: bounce 1s ease-in-out infinite;
            border: 4px solid #ff1744;
            box-shadow: 0 0 20px rgba(255, 23, 68, 0.5);
        ">
            <h2>🚨 ALERTE ROUGE ! 🚨</h2>
            <h3>{quantity}x articles ! Sérieusement ?! 😅</h3>
            <p>Reviens sur terre champion ! 🌍</p>
        </div>
        
        <style>
        @keyframes bounce {{
            0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }}
            40% {{ transform: translateY(-10px); }}
            60% {{ transform: translateY(-5px); }}
        }}
        </style>
        """, unsafe_allow_html=True)
        
    else:
        # Ajouter chaque article individuellement (pour le détail)
        article_dict = convert_pandas_to_dict(article)
        
        for i in range(quantity):
            st.session_state.cart.append(article_dict.copy())
        
        st.success(f"✅ {quantity}x {article_dict['Nom']} ajoutés au panier!")
        st.info(f"💰 Nouveau total : {new_total:.2f}€")

def add_multiple_to_cart_optimized(article, quantity):
    """Version optimisée qui groupe les articles identiques"""
    current_total = calculate_cart_total()
    article_price = float(article['Prix'])
    new_total = current_total + (article_price * quantity)
    
    if new_total > MAX_CART_AMOUNT:
        st.error(f"❌ Budget dépassé ! {new_total:.2f}€ > {MAX_CART_AMOUNT}€")
        return
    
    article_dict = convert_pandas_to_dict(article)
    
    # Chercher si l'article existe déjà dans le panier
    found = False
    for cart_item in st.session_state.cart:
        if cart_item['Nom'] == article_dict['Nom']:
            # Ajouter la quantité à l'article existant
            if 'Quantité' in cart_item:
                cart_item['Quantité'] += quantity
            else:
                cart_item['Quantité'] = quantity + 1
            found = True
            break
    
    if not found:
        # Ajouter nouvel article avec quantité
        article_dict['Quantité'] = quantity
        st.session_state.cart.append(article_dict)
    
    st.success(f"✅ {quantity}x {article_dict['Nom']} ajoutés!")
    st.info(f"💰 Nouveau total : {new_total:.2f}€")

# Ajouter les fonctions groupement JUSTE APRÈS add_multiple_to_cart()

def group_articles_by_base_name(articles_df):
    """Grouper les articles par nom de base (sans taille)"""
    import re
    grouped_articles = {}
    
    for idx, article in articles_df.iterrows():
        # Extraire le nom de base (enlever les tailles courantes)
        nom_original = article['Nom']
        
        # Patterns de tailles à enlever
        taille_patterns = [
            r'\s+Taille\s+\w+', r'\s+T\.\s*\w+', r'\s+Size\s+\w+',
            r'\s+XS\b', r'\s+S\b', r'\s+M\b', r'\s+L\b', r'\s+XL\b', r'\s+XXL\b', r'\s+XXXL\b',
            r'\s+\d+\b', r'\s+\d+/\d+\b'  # Tailles numériques
        ]
        
        nom_base = nom_original
        taille_detectee = ""
        
        # Détecter et extraire la taille
        for pattern in taille_patterns:
            match = re.search(pattern, nom_original, re.IGNORECASE)
            if match:
                taille_detectee = match.group().strip()
                nom_base = re.sub(pattern, '', nom_original, flags=re.IGNORECASE).strip()
                break
        
        # Si pas de taille détectée, garder tel quel
        if not taille_detectee:
            taille_detectee = "Unique"
            nom_base = nom_original
        
        # Grouper
        if nom_base not in grouped_articles:
            grouped_articles[nom_base] = {
                'nom_base': nom_base,
                'categorie': article['Catégorie'],
                'variants': []
            }
        
        grouped_articles[nom_base]['variants'].append({
            'taille': taille_detectee,
            'prix': article['Prix'],
            'nom_complet': nom_original,
            'unite': article.get('Unité', 'unité'),
            'article_original': article
        })
    
    return grouped_articles

def display_grouped_articles(category_articles):
    """Afficher les articles groupés par nom de base"""
    grouped = group_articles_by_base_name(category_articles)
    
    for nom_base, group_data in grouped.items():
        variants = group_data['variants']
        
        # Si un seul variant, affichage normal
        if len(variants) == 1:
            variant = variants[0]
            article = variant['article_original']
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                padding: 1rem;
                border-radius: 15px;
                margin: 1rem 0;
                color: white;
                box-shadow: 0 5px 15px rgba(240, 147, 251, 0.3);
            ">
                <h4 style="margin: 0 0 0.5rem 0;">{variant['nom_complet']}</h4>
                <p style="margin: 0; opacity: 0.9;">{variant['prix']}€ / {variant['unite']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Contrôles normaux
            col_qty, col_btn = st.columns([1, 2])
            
            with col_qty:
                qty_key = f"qty_{nom_base.replace(' ', '_')}"
                quantity = st.number_input(
                    "Quantité", 
                    min_value=0, 
                    max_value=50, 
                    value=0,
                    step=1,
                    key=qty_key
                )
            
            with col_btn:
                if st.button(f"🛒 Ajouter au panier", key=f"add_{nom_base.replace(' ', '_')}"):
                    if quantity > 0:
                        add_multiple_to_cart(article, quantity)
                    else:
                        st.warning("⚠️ Veuillez sélectionner une quantité > 0")
        
        else:
            # Multiples variants = affichage groupé
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1rem;
                border-radius: 15px;
                margin: 1rem 0;
                color: white;
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
            ">
                <h4 style="margin: 0 0 0.5rem 0;">👕 {nom_base}</h4>
                <p style="margin: 0; opacity: 0.9;">📏 {len(variants)} tailles disponibles</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Sélection de taille et quantité
            col_size, col_qty, col_btn = st.columns([2, 1, 2])
            
            with col_size:
                taille_options = [f"{v['taille']} - {v['prix']}€" for v in variants]
                taille_selectionnee = st.selectbox(
                    "Choisir taille",
                    taille_options,
                    key=f"size_{nom_base.replace(' ', '_')}"
                )
                
                # Retrouver le variant sélectionné
                selected_variant = None
                for v in variants:
                    if f"{v['taille']} - {v['prix']}€" == taille_selectionnee:
                        selected_variant = v
                        break
            
            with col_qty:
                quantity = st.number_input(
                    "Quantité",
                    min_value=0,
                    max_value=50,
                    value=0,
                    step=1,
                    key=f"qty_grouped_{nom_base.replace(' ', '_')}"
                )
            
            with col_btn:
                if st.button(f"🛒 Ajouter", key=f"add_grouped_{nom_base.replace(' ', '_')}"):
                    if quantity > 0 and selected_variant:
                        add_multiple_to_cart(selected_variant['article_original'], quantity)
                    else:
                        st.warning("⚠️ Sélectionnez une taille et une quantité > 0")

# Fonctions PDF et Email
def generate_pdfs():
    """Générer 2 PDFs : commande + réception"""
    # PDF 1 : Commande (pour commanditaire)
    buffer_commande = generate_pdf_commande()
    
    # PDF 2 : Réception (pour réceptionnaire) 
    buffer_reception = generate_pdf_reception()
    
    return buffer_commande, buffer_reception

def generate_pdf_commande():
    """PDF pour la personne qui passe commande"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Titre principal
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=30, alignment=1)
    title = Paragraph("🛒 COMMANDE D'ÉQUIPEMENTS DE PROTECTION", title_style)
    story.append(title)
    
    # Informations équipe
    if hasattr(st.session_state, 'contremaître') or hasattr(st.session_state, 'equipe'):
        info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=12, alignment=1, spaceAfter=20)
        
        info_text = []
        if hasattr(st.session_state, 'contremaître') and st.session_state.contremaître:
            info_text.append(f"👨‍💼 Contremaître: {st.session_state.contremaître}")
        if hasattr(st.session_state, 'equipe') and st.session_state.equipe:
            info_text.append(f"👷‍♂️ Équipe: {st.session_state.equipe}")
        
        if info_text:
            info_paragraph = Paragraph("<br/>".join(info_text), info_style)
            story.append(info_paragraph)
    
    # Date
    date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], fontSize=12, alignment=1)
    date_text = Paragraph(f"📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style)
    story.append(date_text)
    story.append(Spacer(1, 20))
    
    # Tableau des articles NORMAL
    data = [['Article', 'Catégorie', 'Prix (€)', 'Unité']]
    total = 0
    
    for item in st.session_state.cart:
        price = float(item['Prix'])
        data.append([
            item['Nom'],
            item['Catégorie'],
            f"{price:.2f}",
            item.get('Unité', 'unité')
        ])
        total += price
    
    # Ligne total
    data.append(['', '', f"TOTAL: {total:.2f}€", ''])
    
    # Style du tableau
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    doc.build(story)
    
    buffer.seek(0)
    return buffer

def generate_pdf_reception():
    """PDF pour la personne qui réceptionne (avec checkboxes)"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Titre principal SANS carrés noirs
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=30, alignment=1)
    title = Paragraph("BON DE RÉCEPTION - ÉQUIPEMENTS EPI", title_style)
    story.append(title)
    
    # Informations équipe
    if hasattr(st.session_state, 'contremaître') or hasattr(st.session_state, 'equipe'):
        info_style = ParagraphStyle('InfoStyle', parent=styles['Normal'], fontSize=12, alignment=1, spaceAfter=20)
        
        info_text = []
        if hasattr(st.session_state, 'contremaître') and st.session_state.contremaître:
            info_text.append(f"Contremaître: {st.session_state.contremaître}")
        if hasattr(st.session_state, 'equipe') and st.session_state.equipe:
            info_text.append(f"Équipe: {st.session_state.equipe}")
        
        if info_text:
            info_paragraph = Paragraph("<br/>".join(info_text), info_style)
            story.append(info_paragraph)
    
    # Date 
    date_style = ParagraphStyle('DateStyle', parent=styles['Normal'], fontSize=12, alignment=1)
    date_text = Paragraph(f"Date commande: {datetime.now().strftime('%d/%m/%Y %H:%M')}", date_style)
    story.append(date_text)
    story.append(Spacer(1, 20))
    
    # Instructions SANS carrés noirs
    instruction_style = ParagraphStyle('InstructionStyle', parent=styles['Normal'], fontSize=14, alignment=1, spaceAfter=20)
    instruction = Paragraph("<b>INSTRUCTIONS:</b> Cochez les cases lors de la réception des articles", instruction_style)
    story.append(instruction)
    story.append(Spacer(1, 20))
    
    # Tableau SIMPLE sans symboles
    data = [['Coché', 'Article', 'Catégorie', 'Prix (€)', 'Quantité', 'Reçu']]
    total = 0
    
    for item in st.session_state.cart:
        price = float(item['Prix'])
        data.append([
            '',  # Colonne vide pour cocher
            item['Nom'],
            item['Catégorie'], 
            f"{price:.2f}",
            '1',
            ''   # Colonne vide pour "Reçu"
        ])
        total += price
    
    # Ligne total
    data.append(['', '', '', f"TOTAL: {total:.2f}€", '', ''])
    
    # Style du tableau
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.lightblue),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgreen),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 2, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 30))
    
    # Section signature SANS carrés noirs
    signature_style = ParagraphStyle('SignatureStyle', parent=styles['Normal'], fontSize=12, spaceAfter=10)
    
    story.append(Paragraph("<b>RÉCEPTION EFFECTUÉE PAR:</b>", signature_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Nom: ________________________________", signature_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("Date: ________________________________", signature_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("Signature: ________________________________", signature_style))
    
    doc.build(story)
    
    buffer.seek(0)
    return buffer

# En-tête principal
st.markdown("""
<div class="main-header">
    <h1 style="color: white; font-weight: 800; font-size: 2.2rem; margin-bottom: 0.5rem; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">🛒 Bienvenue dans Commande Articles et EPI</h1>
    <p style="text-align: center; color: white; font-family: 'Inter', sans-serif; margin: 0; font-size: 1.2rem; font-weight: 500;">
        🛡️ **Votre solution complète pour les équipements de protection individuelle**
    </p>
</div>
""", unsafe_allow_html=True)

# Section informations équipe
st.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);">
    <h3 style="color: white; margin: 0 0 1rem 0; font-family: 'Inter', sans-serif; font-weight: 600;">👥 Informations de l'équipe</h3>
</div>
""", unsafe_allow_html=True)

# Listes prédéfinies
contremaîtres_list = [
    "Sélectionner un contremaître...",
    "PINTO",
    "CASAIS", 
    "WROBEL",
    "ORLANDI",
    "KADRI",
    "SHOM"
]

equipes_list = [
    "Sélectionner une équipe...",
    "PFI1",
    "PFI2",
    "PFI3", 
    "PFI4",
    "PFI5",
    "PFI6"
]

# Champs déroulants pour contremaître et équipe
col1, col2 = st.columns(2)
with col1:
    contremaître = st.selectbox(
        "👨‍💼 Nom du contremaître", 
        contremaîtres_list,
        key="contremaître_select"
    )
with col2:
    equipe = st.selectbox(
        "👷‍♂️ Équipe", 
        equipes_list,
        key="equipe_select"
    )

# Sauvegarder dans session_state seulement si une option valide est sélectionnée
if contremaître and contremaître != "Sélectionner un contremaître...":
    st.session_state.contremaître = contremaître
    
if equipe and equipe != "Sélectionner une équipe...":
    st.session_state.equipe = equipe

# Sidebar pour le panier (identique à avant mais condensé)
with st.sidebar:
    cart_count = len(st.session_state.cart)
    current_total = calculate_cart_total()
    
    st.markdown(f"""
    <div class="cart-header">
        <h2 style="margin: 0; font-size: 1.5rem;">🛒 PANIER</h2>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
            📦 {cart_count} article{'s' if cart_count != 1 else ''}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Afficher les infos équipe si renseignées
    if (hasattr(st.session_state, 'contremaître') and st.session_state.contremaître) or \
       (hasattr(st.session_state, 'equipe') and st.session_state.equipe):
        st.markdown("### 👥 Équipe sélectionnée")
        if hasattr(st.session_state, 'contremaître') and st.session_state.contremaître:
            st.markdown(f"**👨‍💼 Contremaître:** {st.session_state.contremaître}")
        if hasattr(st.session_state, 'equipe') and st.session_state.equipe:
            st.markdown(f"**👷‍♂️ Équipe:** {st.session_state.equipe}")
        st.markdown("---")
    
    if st.session_state.cart:
        # Affichage du total et gestion du panier (code existant)
        if current_total > MAX_CART_AMOUNT * 0.9:
            st.markdown(f"""
            <div class="cart-warning">
                ⚠️ ATTENTION<br>
                {current_total:.2f}€ / {MAX_CART_AMOUNT}€<br>
                <small>Limite presque atteinte!</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="cart-total">
                💰 TOTAL<br>
                {current_total:.2f}€ / {MAX_CART_AMOUNT}€
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🗑️ Vider le panier", key="clear_cart"):
            clear_cart()
            st.rerun()
        
        st.markdown("---")
        
        # Articles du panier (condensé)
        st.markdown("### 🛒 Panier")
        
        total = 0
        for i, item in enumerate(st.session_state.cart):
            qty = item.get('Quantité', 1)
            item_total = float(item['Prix']) * qty
            total += item_total
            
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{item['Nom']}**")
                if qty > 1:
                    st.markdown(f"*{qty}x {item['Prix']}€ = {item_total:.2f}€*")
                else:
                    st.markdown(f"*{item['Prix']}€*")
            
            with col2:
                if qty > 1:
                    new_qty = st.number_input(
                        "Qté", 
                        min_value=1, 
                        value=qty, 
                        key=f"cart_qty_{i}",
                        help="Modifier quantité"
                    )
                    if new_qty != qty:
                        st.session_state.cart[i]['Quantité'] = new_qty
                        st.rerun()
            
            with col3:
                if st.button("🗑️", key=f"remove_{i}", help="Supprimer"):
                    remove_from_cart(i)
                    st.rerun()
        
        st.markdown(f"### 💰 **Total: {total:.2f}€**")
        
        # Section finalisation commande dans col2 (panier)
        if st.session_state.cart:
            st.markdown("### 📋 Finaliser la commande")
            
            # Boutons PDF
            col_pdf1, col_pdf2 = st.columns(2)
            
            with col_pdf1:
                if st.button("📄 Générer PDF Commande", type="primary"):
                    if st.session_state.contremaître and st.session_state.equipe:
                        try:
                            # Générer le PDF
                            pdf_buffer = generate_pdf_commande()
                            
                            # 🆕 ENREGISTRER DANS LA BASE DE DONNÉES
                            total_prix = calculate_cart_total()
                            commande_id = save_commande_to_db(
                                st.session_state.contremaître,
                                st.session_state.equipe, 
                                st.session_state.cart,
                                total_prix
                            )
                            
                            # Téléchargement du PDF
                            st.download_button(
                                label="⬇️ Télécharger le PDF",
                                data=pdf_buffer.getvalue(),
                                file_name=f"commande_{st.session_state.contremaître}_{st.session_state.equipe}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                mime="application/pdf"
                            )
                            
                            st.success(f"✅ PDF généré et commande #{commande_id} enregistrée !")
                            st.info("💡 Vous pouvez maintenant vider le panier ou continuer vos achats")
                            
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la génération : {str(e)}")
                    else:
                        st.warning("⚠️ Veuillez remplir le contremaître et l'équipe avant de générer le PDF")
            
            with col_pdf2:
                if st.button("📋 Générer PDF Réception", type="secondary"):
                    if st.session_state.contremaître and st.session_state.equipe:
                        try:
                            # Générer le PDF de réception
                            pdf_buffer = generate_pdf_reception()
                            
                            # Téléchargement (pas besoin de re-sauvegarder si déjà fait pour la commande)
                            st.download_button(
                                label="⬇️ Télécharger PDF Réception",
                                data=pdf_buffer.getvalue(),
                                file_name=f"reception_{st.session_state.contremaître}_{st.session_state.equipe}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                mime="application/pdf"
                            )
                            
                        except Exception as e:
                            st.error(f"❌ Erreur : {str(e)}")
    else:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: #718096; font-family: 'Poppins', sans-serif;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🛒</div>
            <h3 style="margin: 0;">Votre panier est vide</h3>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.8;">Ajoutez des articles pour commencer !</p>
        </div>
        """, unsafe_allow_html=True)

# Interface principale avec navigation par catégories
col1, col2 = st.columns([3, 1])

with col2:
    st.markdown("### 🧭 Navigation")
    
    page = st.selectbox(
        "📍 Aller à :",
        ["🛒 Catalogue", "📊 Historique", "📈 Statistiques"],
        key="page_select"
    )

with col1:
    # Navigation entre les pages  
    if page == "🛒 Catalogue":
        # Recherche avancée (optionnelle)
        if st.session_state.show_search:
            st.markdown("""
            <div class="search-section">
                <h3>🔍 Recherche avancée</h3>
                <p style="color: #718096; margin: 0;">Trouvez rapidement l'article que vous cherchez</p>
            </div>
            """, unsafe_allow_html=True)
            
            query = st.text_input("", placeholder="🔍 Tapez le nom d'un article...", label_visibility="collapsed")
            
            if query:
                query_lower = query.lower()
                filtered_articles = articles_df[
                    articles_df['Nom'].str.lower().str.contains(query_lower, na=False) |
                    articles_df['Description'].str.lower().str.contains(query_lower, na=False)
                ]
                
                st.markdown(f"""
                <div style="margin: 1rem 0; padding: 1rem; background: rgba(102, 126, 234, 0.1); border-radius: 10px; border-left: 4px solid #667eea;">
                    <strong style="color: #667eea;">📊 {len(filtered_articles)} articles trouvés</strong>
                </div>
                """, unsafe_allow_html=True)
                
                for _, article in filtered_articles.head(10).iterrows():
                    st.markdown(f"""
                    <div class="article-card">
                        <div class="article-name">{article['Nom']}</div>
                        <div class="article-description">{article['Description']}</div>
                        <div class="article-price">{article['Prix']} € / {article['Unité']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"➕ Ajouter au panier", key=f"search_{article['Référence']}"):
                        add_to_cart(article)
                        st.rerun()

        # Affichage principal : Catégories ou Articles d'une catégorie
        if st.session_state.selected_category is None and not st.session_state.show_search:
            # Vue des catégories - Design moderne
            st.markdown("""
            <div style="text-align: center; margin: 3rem 0;">
                <h1 style="color: white; font-family: 'Inter', sans-serif; font-weight: 800; font-size: 2.5rem; margin-bottom: 1rem; text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);">
                    🛡️ Équipements de Protection Individuelle
                </h1>
                <p style="color: rgba(255, 255, 255, 0.9); font-family: 'Inter', sans-serif; margin: 0; font-size: 1.2rem; font-weight: 400;">
                    Découvrez notre gamme complète d'EPI professionnels
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            categories = sorted(articles_df['Catégorie'].unique())
            
            # Définir des icônes EPI pour chaque catégorie
            category_icons = {
                'Bourses/Pochettes': '🎒',
                'Casques': '⛑️', 
                'Chaussures': '🥾',
                'Gants': '🧤',
                'Outils': '🔧',
                'Lunette': '🥽',
                'Pointure': '👢',
                'Veste Blouson': '🦺',
                'Jugulaire': '⛑️',
                'Fort Métal Peinture': '🎨',
                'Lampe': '🔦'
            }
            
            # Afficher les catégories en grille
            cols = st.columns(2)
            
            for i, category in enumerate(categories):
                article_count = len(articles_df[articles_df['Catégorie'] == category])
                icon = category_icons.get(category, '🛡️')
                
                with cols[i % 2]:
                    # Créer une carte avec bouton Streamlit fonctionnel
                    st.markdown(f"""
                    <div class="category-card">
                        <div class="category-icon">{icon}</div>
                        <div class="category-title">{category}</div>
                        <div class="category-count">{article_count} article{'s' if article_count != 1 else ''}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Bouton fonctionnel en pleine largeur
                    if st.button(f"🔍 Explorer {category}", key=f"cat_{category}", help=f"Voir les {article_count} articles de {category}"):
                        st.session_state.selected_category = category
                        st.rerun()

        elif st.session_state.selected_category and not st.session_state.show_search:
            # Vue des articles d'une catégorie
            category = st.session_state.selected_category
            category_articles = articles_df[articles_df['Catégorie'] == category]
            
            # BOUTON RETOUR EN HAUT - TRÈS VISIBLE 🔝
            st.markdown("""
            <div style="background: #f0f0f0; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; text-align: center;">
            """, unsafe_allow_html=True)
            
            if st.button("🏠 ⬅️ RETOUR AUX CATÉGORIES", key="back_to_categories_top", 
                       type="primary", help="Cliquez pour retourner aux catégories"):
                st.session_state.selected_category = None
                st.session_state.show_search = False
                st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="text-align: center; margin: 2rem 0;">
                <h2 style="color: #2d3748; font-family: 'Poppins', sans-serif; font-weight: 600; margin-bottom: 0.5rem;">
                    📁 {category}
                </h2>
                <p style="color: #718096; font-family: 'Poppins', sans-serif; margin: 0;">
                    {len(category_articles)} articles dans cette catégorie
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # AFFICHAGE GROUPÉ DES ARTICLES
            display_grouped_articles(category_articles)

    elif page == "📊 Historique":
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <h2 style="color: #2d3748; font-family: 'Poppins', sans-serif; font-weight: 600;">
                📊 Historique des Commandes
            </h2>
            <p style="color: #718096; font-family: 'Poppins', sans-serif;">
                Consultez toutes les commandes passées
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            df_commandes = get_all_commandes()
            
            if len(df_commandes) > 0:
                # Filtres
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    filtre_equipe = st.selectbox(
                        "👷‍♂️ Filtrer par équipe",
                        ["Toutes"] + list(df_commandes['equipe'].unique())
                    )
                
                with col2:
                    filtre_contremaître = st.selectbox(
                        "👨‍💼 Filtrer par contremaître", 
                        ["Tous"] + list(df_commandes['contremaître'].unique())
                    )
                
                with col3:
                    periode = st.selectbox(
                        "📅 Période",
                        ["Tout", "30 derniers jours", "7 derniers jours", "Aujourd'hui"]
                    )
                
                # Appliquer les filtres
                df_filtered = df_commandes.copy()
                
                if filtre_equipe != "Toutes":
                    df_filtered = df_filtered[df_filtered['equipe'] == filtre_equipe]
                
                if filtre_contremaître != "Tous":
                    df_filtered = df_filtered[df_filtered['contremaître'] == filtre_contremaître]
                
                if periode != "Tout":
                    aujourd_hui = datetime.now()
                    if periode == "Aujourd'hui":
                        df_filtered = df_filtered[df_filtered['date'].str.startswith(aujourd_hui.strftime('%Y-%m-%d'))]
                    elif periode == "7 derniers jours":
                        il_y_a_7_jours = (aujourd_hui - timedelta(days=7)).strftime('%Y-%m-%d')
                        df_filtered = df_filtered[df_filtered['date'] >= il_y_a_7_jours]
                    elif periode == "30 derniers jours":
                        il_y_a_30_jours = (aujourd_hui - timedelta(days=30)).strftime('%Y-%m-%d')
                        df_filtered = df_filtered[df_filtered['date'] >= il_y_a_30_jours]
                
                # Affichage résultats
                st.markdown(f"**📋 {len(df_filtered)} commandes trouvées**")
                
                # Tableau des commandes
                for _, commande in df_filtered.iterrows():
                    with st.expander(f"🛒 Commande #{commande['id']} - {commande['date'][:16]} - {commande['total_prix']:.2f}€"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.markdown(f"**👨‍💼 Contremaître:** {commande['contremaître']}")
                            st.markdown(f"**👷‍♂️ Équipe:** {commande['equipe']}")
                        
                        with col2:
                            st.markdown(f"**💰 Total:** {commande['total_prix']:.2f}€")
                            st.markdown(f"**📦 Articles:** {commande['nb_articles']}")
                        
                        with col3:
                            st.markdown(f"**📅 Date:** {commande['date'][:16]}")
                            st.markdown(f"**✅ Statut:** {commande['statut']}")
                        
                        # Détail des articles
                        if st.button(f"👀 Voir détails", key=f"details_{commande['id']}"):
                            articles = json.loads(commande['articles_json'])
                            st.markdown("**📋 Articles commandés :**")
                            for article in articles:
                                st.markdown(f"- **{article['Nom']}** - {article['Prix']}€ ({article['Catégorie']})")
                
            else:
                st.info("📭 Aucune commande enregistrée pour le moment.")
            
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement : {str(e)}")

    elif page == "📈 Statistiques":
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <h2 style="color: #2d3748; font-family: 'Poppins', sans-serif; font-weight: 600;">
                📈 Statistiques et Bilans
            </h2>
            <p style="color: #718096; font-family: 'Poppins', sans-serif;">
                Analysez les dépenses et tendances
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            stats = get_statistics()
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="📋 Total Commandes",
                    value=stats['total_commandes']
                )
            
            with col2:
                st.metric(
                    label="💰 Total Dépensé", 
                    value=f"{stats['total_depense']:.2f}€"
                )
            
            with col3:
                if stats['total_commandes'] > 0:
                    moyenne = stats['total_depense'] / stats['total_commandes']
                    st.metric(
                        label="📊 Moyenne/Commande",
                        value=f"{moyenne:.2f}€"
                    )
            
            with col4:
                # Calculer la période réelle basée sur les données
                if stats['total_commandes'] > 0:
                    # Récupérer la première et dernière commande
                    df_commandes = get_all_commandes()
                    if len(df_commandes) > 0:
                        premiere_date = df_commandes['date'].min()[:4]  # Année de la première commande
                        derniere_date = df_commandes['date'].max()[:4]  # Année de la dernière commande
                        
                        if premiere_date == derniere_date:
                            periode_text = premiere_date
                        else:
                            periode_text = f"{premiere_date}-{derniere_date}"
                    else:
                        periode_text = str(datetime.now().year)
                else:
                    periode_text = str(datetime.now().year)
                
                st.metric(
                    label="📅 Période",
                    value=periode_text
                )
            
            st.markdown("---")
            
            # Graphiques
            if len(stats['df_equipes']) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 👷‍♂️ Dépenses par Équipe")
                    fig_equipes = px.bar(
                        stats['df_equipes'], 
                        x='equipe', 
                        y='total_prix',
                        title="Montant total par équipe",
                        color='total_prix',
                        color_continuous_scale='viridis'
                    )
                    st.plotly_chart(fig_equipes, use_container_width=True)
                
                with col2:
                    st.markdown("### 👨‍💼 Dépenses par Contremaître") 
                    fig_contremaitres = px.pie(
                        stats['df_contremaitres'],
                        values='total_prix',
                        names='contremaître', 
                        title="Répartition par contremaître"
                    )
                    st.plotly_chart(fig_contremaitres, use_container_width=True)
            
            # Évolution mensuelle
            if len(stats['df_mensuel']) > 0:
                st.markdown("### 📈 Évolution Mensuelle")
                fig_mensuel = px.line(
                    stats['df_mensuel'],
                    x='mois',
                    y='total_prix', 
                    title="Évolution des dépenses mensuelles",
                    markers=True
                )
                st.plotly_chart(fig_mensuel, use_container_width=True)
            
            # Tableaux détaillés
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Top Équipes")
                st.dataframe(stats['df_equipes'], use_container_width=True)
            
            with col2:
                st.markdown("### 📊 Top Contremaîtres") 
                st.dataframe(stats['df_contremaitres'], use_container_width=True)
                
            # Export
            if st.button("📤 Exporter les statistiques Excel"):
                # Créer un fichier Excel avec les stats
                st.info("🚧 Fonctionnalité d'export en développement...")
                
        except Exception as e:
            st.error(f"❌ Erreur lors du calcul des statistiques : {str(e)}")

# Ajouter une fonction de test (temporaire)
def test_database_connection():
    """Tester la connexion à la base de données"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            conn.close()
            return f"✅ PostgreSQL connecté: {version[0][:50]}..."
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version();")
            version = cursor.fetchone()
            conn.close()
            return f"✅ SQLite connecté: {version[0]}"
    except Exception as e:
        return f"❌ Erreur connexion: {str(e)}"

# Dans votre sidebar, ajouter temporairement :
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔧 Debug")
    if st.button("🗄️ Test DB"):
        result = test_database_connection()
        if "✅" in result:
            st.success(result)
        else:
            st.error(result)