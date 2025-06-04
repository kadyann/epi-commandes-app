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
import base64
import re
import hashlib
import csv          # 📥 nécessaire pour écrire dans le catalogue
import ast
from typing import Tuple, Optional

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

st.markdown("""
<style>
@media (max-width: 768px) {
    section[data-testid="stSidebar"] {
        display: none !important;
    }
}
</style>
""", unsafe_allow_html=True)

# === VARIABLES GLOBALES ===
MAX_CART_AMOUNT = 1500.0  # Budget maximum par commande

# Configuration base de données
if 'DATABASE_URL' in os.environ:
    DATABASE_URL = os.environ['DATABASE_URL']
    USE_POSTGRESQL = True
else:
    DATABASE_PATH = 'commandes.db'
    USE_POSTGRESQL = False

# === CHARGEMENT DES DONNÉES ===
@st.cache_data(ttl=60)
def load_articles():
    """Charge les articles depuis le CSV - AVEC VALIDATION DES COLONNES"""
    try:
        # Essayer UTF-8 d'abord
        df = pd.read_csv('articles.csv', encoding='utf-8')
        print(f"📋 CSV lu avec succès : {len(df)} articles")
        
        # VALIDATION ET NETTOYAGE DES COLONNES ✅
        required_columns = ['N° Référence', 'Nom', 'Description', 'Prix', 'Unitée']
        
        # Vérifier que toutes les colonnes existent
        if not all(col in df.columns for col in required_columns):
            st.error(f"❌ Colonnes manquantes dans le CSV. Trouvées: {list(df.columns)}")
            return create_sample_articles()
        
        # Nettoyer la colonne Prix - supprimer les lignes avec des prix non numériques
        df = df.dropna(subset=['Prix'])
        df['Prix'] = pd.to_numeric(df['Prix'], errors='coerce')
        df = df.dropna(subset=['Prix'])  # Supprimer les lignes où Prix ne peut pas être converti
        
        # Supprimer les lignes avec des données corrompues
        df = df[df['Prix'] > 0]  # Prix doit être positif
        df = df[df['Nom'].str.len() > 2]  # Nom doit avoir au moins 3 caractères
        
        print(f"✅ CSV nettoyé : {len(df)} articles valides")
        return df
        
    except FileNotFoundError:
        st.warning("📁 Fichier articles.csv non trouvé, création d'articles d'exemple")
        return create_sample_articles()
    except UnicodeDecodeError:
        try:
            df = pd.read_csv('articles.csv', encoding='latin-1')
            print(f"📋 CSV lu (latin-1) : {len(df)} articles")
            # Même validation ici
            return df
        except Exception as e:
            st.error(f"❌ Erreur lecture : {e}")
            return create_sample_articles()
    except Exception as e:
        st.error(f"❌ Erreur inattendue : {e}")
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

# === FONCTIONS BASE DE DONNÉES ===
def init_database():
    """Initialise la base de données"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Table users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'user',
                    equipe VARCHAR(50),
                    fonction VARCHAR(100),
                    couleur_preferee VARCHAR(30)
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
            
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Table users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    equipe TEXT,
                    fonction TEXT,
                    couleur_preferee TEXT
                )
            """)
            
            # Table commandes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commandes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    contremaître TEXT,
                    equipe TEXT,
                    articles_json TEXT,
                    total_prix REAL,
                    nb_articles INTEGER,
                    user_id INTEGER
                )
            """)
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur initialisation base: {e}")

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
                ('can_view_all_orders', 'BOOLEAN DEFAULT FALSE')
            ]
            
            for column_name, column_type in permissions_columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                    conn.commit()
                except:
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
                ('can_view_all_orders', 'INTEGER DEFAULT 0')
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

# === GESTION UTILISATEURS ===
def init_users_db():
    """Initialise les utilisateurs par défaut"""
    # Migration pour ajouter la couleur préférée
    migrate_add_couleur_column()
    
    # Créer l'utilisateur admin par défaut
    admin_password = hashlib.sha256("admin123".encode()).hexdigest()
    
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Vérifier si admin existe
            cursor.execute("SELECT id FROM users WHERE username = %s", ("admin",))
            if cursor.fetchone():
                # Mettre à jour admin existant
                cursor.execute("""
                    UPDATE users SET couleur_preferee = %s WHERE username = %s
                """, ("DT770", "admin"))
            else:
                # Créer nouvel admin
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, equipe, fonction, couleur_preferee) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, ("admin", admin_password, "admin", "DIRECTION", "Administrateur", "DT770"))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Vérifier si admin existe
            cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
            if cursor.fetchone():
                # Mettre à jour admin existant
                cursor.execute("""
                    UPDATE users SET couleur_preferee = ? WHERE username = ?
                """, ("DT770", "admin"))
            else:
                # Créer nouvel admin
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, equipe, fonction, couleur_preferee) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ("admin", admin_password, "admin", "DIRECTION", "Administrateur", "DT770"))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur initialisation admin: {e}")

def authenticate_user(username, password):
    """
    Renvoie le dict utilisateur si les identifiants sont valides, sinon None
    """
    ensure_users_table()
    if USE_POSTGRESQL:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, password_hash, role, equipe, fonction, can_add_articles, can_view_stats, can_view_all_orders
            FROM users WHERE username = %s
        """, (username,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        (uid, user, pwd_hash, role, equipe, fonction, c_add, c_stats, c_all) = row
        # Vérification du mot de passe hashé
        if pwd_hash and hashlib.sha256(password.encode()).hexdigest() == pwd_hash:
            pass_ok = True
        else:
            pass_ok = False
    else:
        conn   = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, password_hash, role, equipe, fonction, can_add_articles, can_view_stats, can_view_all_orders
            FROM users WHERE username = ?
        """, (username,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        (uid, user, pwd_hash, role, equipe, fonction, c_add, c_stats, c_all) = row
        if pwd_hash and hashlib.sha256(password.encode()).hexdigest() == pwd_hash:
            pass_ok = True
        else:
            pass_ok = False
    if not pass_ok:
        return None
    return {
        "id": uid,
        "username": user,
        "role": role,
        "equipe": equipe,
        "fonction": fonction,
        "can_add_articles": bool(c_add),
        "can_view_stats":   bool(c_stats),
        "can_view_all_orders": bool(c_all)
    }

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

def calculate_cart_total():
    """Calcule le total du panier"""
    return sum(float(item['Prix']) for item in st.session_state.cart)

def add_to_cart(article, quantity=1):
    """Ajoute un article au panier avec vérification du budget"""
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    
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
            break

def remove_all_from_cart(article):
    """Retire tous les exemplaires d'un article du panier"""
    st.session_state.cart = [item for item in st.session_state.cart if item['Nom'] != article['Nom']]

# === FONCTIONS INTERFACE ===
def init_session_state():
    """Initialise les variables de session"""
    if 'cart' not in st.session_state:
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
            
            col_minus, col_qty, col_plus, col_del = st.columns([1, 1, 1, 1])
            
            with col_minus:
                if st.button("➖", key=f"sidebar_minus_{i}_{article['Nom']}", help="Réduire quantité"):
                    remove_from_cart(article)
                    st.rerun()
            
            with col_qty:
                st.markdown(f"<div style='text-align: center; font-size: 14px; font-weight: bold; padding: 4px;'>{quantite}</div>", unsafe_allow_html=True)
            
            with col_plus:
                if st.button("➕", key=f"sidebar_plus_{i}_{article['Nom']}", help="Augmenter quantité"):
                    add_to_cart(article, 1)
                    st.rerun()
            
            with col_del:
                if st.button("🗑️", key=f"sidebar_delete_{i}_{article['Nom']}", help="Supprimer"):
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
    
    if st.button("🛒 Voir le panier", use_container_width=True):
        st.session_state.page = "cart"
        st.rerun()
    
    if budget_remaining >= 0:
        if st.button("✅ Valider commande", use_container_width=True):
            st.session_state.page = "validation"
            st.rerun()
    else:
        st.button("❌ Budget dépassé", disabled=True, use_container_width=True)

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
                    st.session_state.authenticated = True
                    st.session_state.current_user  = user
                    st.session_state.page          = "catalogue"   # ou page d'accueil
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
    """Affiche les commandes de l'utilisateur connecté"""
    st.markdown("### 📊 Mes commandes")
    
    user_info = st.session_state.get('current_user')
    if not user_info:
        st.error("❌ Vous devez être connecté")
        return
    
    # Migrer la table pour ajouter user_id
    migrate_add_user_id_column()
    
    orders = []
    
    try:
        # Essayer avec contremaître (système actuel)
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, total_prix, 'validée' as status, articles_json 
                FROM commandes 
                WHERE contremaître = %s 
                ORDER BY date DESC
            """, (user_info['username'],))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, total_prix, 'validée' as status, articles_json 
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
    
    # Statistiques personnelles avec messages marrants
    total_commandes = len(orders)
    total_depense = sum(order[2] for order in orders)  # total_prix est à l'index 2
    moyenne_commande = total_depense / total_commandes if total_commandes > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
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
        st.metric("📊 Moyenne/commande", f"{moyenne_commande:.2f}€")
        if moyenne_commande > 1000:
            st.caption("🎯 Précision chirurgicale !")
        elif moyenne_commande > 500:
            st.caption("⚖️ Équilibré !")
        else:
            st.caption("🐭 Petites commandes !")
    
    st.markdown("---")
    
    # Afficher les commandes avec messages marrants
    for i, order in enumerate(orders):
        order_id, date, total, status, articles_json = order
        
        # Émojis selon le montant
        if total > 1000:
            emoji = "💎"
        elif total > 500:
            emoji = "🥇"
        elif total > 200:
            emoji = "⭐"
        else:
            emoji = "🛍️"
        
        with st.expander(f"{emoji} Commande #{order_id} - {date} - {total:.2f}€"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**📅 Date:** {date}")
                st.write(f"**💰 Total:** {total:.2f}€")
            
            with col2:
                st.write(f"**📋 Statut:** {status}")
                
                # Messages marrants selon le statut
                if status == "validée":
                    st.success("✅ Mission accomplie !")
                elif status == "en_cours":
                    st.info("⏳ En préparation...")
                elif status == "expédiée":
                    st.info("🚚 En route vers vous !")
            
            # Afficher les articles
            try:
                articles = json.loads(articles_json) if isinstance(articles_json, str) else articles_json
                if not isinstance(articles, list):
                    articles = [articles]
                for article in articles:
                    if isinstance(article, dict) and 'Nom' in article:
                        st.write(f"• {article['Nom']}")
                    elif isinstance(article, dict):
                        st.write(f"• {article.get('nom', article.get('name', 'Article sans nom'))}")
                    else:
                        st.write(f"• {str(article)}")
            except json.JSONDecodeError:
                st.error("❌ Erreur de lecture des articles")
            except Exception as e:
                st.error(f"❌ Erreur affichage articles: {e}")
    
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

def render_navigation():
    user_info = st.session_state.get('current_user', {})
    buttons = [
        ("🛡️ Catalogue", "catalogue"),
        ("🛒 Panier", "cart"),
        ("📊 Mes commandes", "mes_commandes")
    ]
    if user_info.get("can_view_all_orders"):
        buttons.append(("📋 Historique", "historique"))
    if user_info.get("can_view_stats"):
        buttons.append(("📈 Statistiques", "stats"))
    if user_info.get("can_add_articles"):
        buttons.append(("➕ Articles", "admin_articles"))
    if user_info.get("role") == "admin":
        buttons.append(("👥 Utilisateurs", "admin_users"))
    buttons.append(("🚪 Déconnexion", "logout"))
    cols = st.columns(len(buttons))
    for i, (label, page) in enumerate(buttons):
        with cols[i]:
            if page == "logout":
                if st.button(label, use_container_width=True):
                    st.session_state.authenticated = False
                    st.session_state.current_user = {}
                    st.session_state.cart = []
                    st.session_state.page = "login"
                    st.rerun()
            else:
                if st.button(label, use_container_width=True):
                    st.session_state.page = page
                    st.rerun()

def main():
    """Fonction principale de l'application"""
    # Initialisation
    init_database()
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
                show_stats()
            else:
                st.warning("⛔ Accès réservé.")
        elif page == "mes_commandes":
            show_mes_commandes()
        elif page == "admin_articles":
            if (st.session_state.current_user or {}).get("can_add_articles"):
                show_admin_articles()
            else:
                st.warning("⛔ Accès réservé.")
        elif page == "admin_users":
            if st.session_state.get('current_user', {}).get('role') == 'admin':
                show_admin_page()
            else:
                st.warning("⛔ Accès réservé.")
        else:
            show_catalogue()

    # En haut de main() ou dans render_navigation()
    if 'sidebar_open' not in st.session_state:
        st.session_state.sidebar_open = True

    # Bouton pour réduire/afficher la sidebar (affiché en haut de la page)
    if st.button("⬅️ Réduire la barre latérale" if st.session_state.sidebar_open else "➡️ Afficher la barre latérale"):
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
    st.markdown("### 🛠️ Gestion des articles - Administration")
    tabs = st.tabs(["📋 Catalogue actuel", "➕ Ajouter article", "📤 Import CSV"])

    with tabs[0]:   # 📑 Catalogue actuel
        st.markdown("#### 📋 Articles actuels")
        st.markdown("#### 🔍 Recherche dans le catalogue")
        query = st.text_input("Référence ou nom…")
        ref_col = get_ref_col(articles_df)
        df_affiche = articles_df
        if query:
            df_affiche = articles_df[
                articles_df["Nom"].str.contains(query, case=False, na=False)
                | articles_df[ref_col].astype(str).str.contains(query)
            ]
        st.dataframe(df_affiche, use_container_width=True)

        # --- Affichage du bouton suppression pour admin, gestionnaire, technicien ---
        if user_info.get("role") == "admin" or user_info.get("fonction", "").lower() in ["technicien", "gestionnaire"]:
            st.markdown("#### 🗑️ Supprimer un article")
            if df_affiche.empty:
                st.info("Aucun article correspondant.")
            else:
                label_options = (
                    df_affiche[ref_col].astype(str) + " – " + df_affiche["Nom"]
                ).tolist()
                choix = st.selectbox("Choisissez l'article :", label_options)
                ref_supp = choix.split(" – ")[0]
                if st.button("🗑️ Supprimer", type="secondary"):
                    ok, msg = delete_article(ref_supp, ref_col)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.info("🔒 Suppression réservée aux administrateurs, gestionnaires et techniciens.")

def add_article_to_csv(reference: str,
                       nom: str,
                       description: str,
                       prix: str,
                       unite: str,
                       categorie: str = "Autre") -> tuple[bool, str]:
    """
    Ajoute une ligne au fichier catalogue (CSV séparateur ';').
    L'appel courant de l'interface transmet 5 arguments ; la catégorie est
    optionnelle et positionnée en dernier.
    Retourne (success, message).
    """
    try:
        file_path = "catalogue.csv"
        header    = ['reference', 'nom', 'description', 'prix', 'unite', 'categorie']

        # Création du fichier s'il n'existe pas encore
        file_exists = os.path.isfile(file_path)
        with open(file_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=';')
            if not file_exists:
                writer.writerow(header)

            writer.writerow([reference, nom, description, prix, unite, categorie])

        return True, "✅ Article ajouté au catalogue"

    except Exception as e:
        return False, f"❌ Erreur ajout article : {e}"

def import_articles_from_csv(new_articles_df):
    """Importe plusieurs articles depuis un DataFrame"""
    try:
        global articles_df
        
        # Charger le CSV actuel
        try:
            df_actuel = pd.read_csv('articles.csv')
        except FileNotFoundError:
            df_actuel = pd.DataFrame(columns=['Référence', 'Nom', 'Prix', 'Catégorie', 'Description'])
        
        # Fusionner les DataFrames
        df_combine = pd.concat([df_actuel, new_articles_df], ignore_index=True)
        
        # Supprimer les doublons basés sur la référence
        df_combine = df_combine.drop_duplicates(subset=['Référence'], keep='last')
        
        # Sauvegarder
        df_combine.to_csv('articles.csv', index=False)
        
        # Recharger le cache
        st.cache_data.clear()
        articles_df = load_articles()
        
        return True
        
    except Exception as e:
        st.error(f"Erreur import articles: {e}")
        return False

def show_admin_users():
    st.markdown("# 👥 Gestion des utilisateurs - Administration")
    users = get_all_users()
    current_user = st.session_state.get("current_user", {})
    is_admin = (current_user or {}).get("role") == "admin"
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ➕ Créer un nouvel utilisateur")
        # ... création ...
    if is_admin:
        with col2:
            st.markdown("### 🗑️ Supprimer un utilisateur")
            # ... suppression ...
    else:
        with col2:
            st.info("Seul l'administrateur peut supprimer des utilisateurs.")

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
            user_id, username, equipe, fonction, can_add_articles, can_view_stats, can_view_all_orders, role = user
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
                        
                        if st.form_submit_button("💾 Sauvegarder permissions", use_container_width=True):
                            new_permissions = {
                                'can_add_articles': new_can_add,
                                'can_view_stats': new_can_stats,
                                'can_view_all_orders': new_can_all_orders
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
                            
    except Exception as e:
        st.error(f"Erreur chargement utilisateurs: {e}")

def get_all_users():
    """Récupère tous les utilisateurs"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, equipe, fonction, 
                       COALESCE(can_add_articles, false), 
                       COALESCE(can_view_stats, false), 
                       COALESCE(can_view_all_orders, false), 
                       role 
                FROM users
            """)
            users = cursor.fetchall()
            conn.close()
            return users
        else:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, equipe, fonction, 
                       COALESCE(can_add_articles, 0), 
                       COALESCE(can_view_stats, 0), 
                       COALESCE(can_view_all_orders, 0), 
                       role 
                FROM users
            """)
            users = cursor.fetchall()
            conn.close()
            return users
    except Exception as e:
        st.error(f"Erreur chargement utilisateurs: {e}")
        return []

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
        # Vérifier que l'utilisateur existe avec l'équipe et couleur correspondantes
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
        
        # Vérifier que l'équipe correspond
        if user_equipe and user_equipe.lower() != equipe.lower():
            conn.close()
            return False, "Équipe incorrecte pour cet utilisateur"
        
        # Vérifier que la couleur correspond (si elle existe)
        if user_couleur and user_couleur.lower() != couleur_preferee.lower():
            conn.close()
            return False, "Couleur préférée incorrecte"
        elif not user_couleur:
            conn.close()
            return False, "Aucune couleur préférée enregistrée pour cet utilisateur. Contactez l'administrateur."
        
        # Générer un nouveau mot de passe temporaire
        import string
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        # Mettre à jour le mot de passe
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
    """Page de réinitialisation de mot de passe avec question de sécurité"""
    st.markdown("### 🔑 Réinitialisation du mot de passe")
    
    # Générer un nouveau captcha si nécessaire
    if 'captcha_question' not in st.session_state or 'captcha_answer' not in st.session_state:
        question, answer = generate_captcha()
        st.session_state.captcha_question = question
        st.session_state.captcha_answer = answer
    
    with st.form("reset_form"):
        st.markdown("⚠️ **Sécurité renforcée** - Répondez aux questions de sécurité pour récupérer votre mot de passe.")
        
        username = st.text_input("👤 Nom d'utilisateur")
        
        # Sélection d'équipe
        equipes = ["DIRECTION", "FLUX", "PARA", "MAINTENANCE", "QUALITE", "LOGISTIQUE"]
        equipe = st.selectbox("👷‍♂️ Votre équipe", ["Sélectionnez..."] + equipes)
        
        # Question de sécurité
        couleur_preferee = st.text_input("🎨 Votre couleur préférée", placeholder="Ex: bleu, rouge, vert...")
        
        # Captcha
        st.markdown("🤖 **Vérification anti-robot**")
        st.write(f"**Question:** {st.session_state.captcha_question}")
        captcha_response = st.number_input("Votre réponse:", min_value=-100, max_value=100, value=0, step=1)
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("🔑 Récupérer mon mot de passe", use_container_width=True)
        with col2:
            refresh_captcha = st.form_submit_button("🔄 Nouveau captcha", use_container_width=True)
        
        if refresh_captcha:
            # Générer un nouveau captcha
            question, answer = generate_captcha()
            st.session_state.captcha_question = question
            st.session_state.captcha_answer = answer
            st.rerun()
        
        if submitted:
            # Validation des champs
            if not username or equipe == "Sélectionnez..." or not couleur_preferee:
                st.error("❌ Veuillez remplir tous les champs")
            elif captcha_response != st.session_state.captcha_answer:
                st.error("❌ Réponse au captcha incorrecte")
                # Générer un nouveau captcha après échec
                question, answer = generate_captcha()
                st.session_state.captcha_question = question
                st.session_state.captcha_answer = answer
            else:
                success, message = reset_user_password(username, equipe, couleur_preferee)
                if success:
                    st.success("✅ Mot de passe réinitialisé avec succès !")
                    st.info(message)
                    st.warning("⚠️ Notez bien ce mot de passe temporaire et changez-le dès votre prochaine connexion")
                    # Nettoyer le captcha
                    del st.session_state.captcha_question
                    del st.session_state.captcha_answer
                else:
                    st.error(f"❌ {message}")
                    # Générer un nouveau captcha après échec
                    question, answer = generate_captcha()
                    st.session_state.captcha_question = question
                    st.session_state.captcha_answer = answer
    
    st.markdown("---")
    st.info("💡 **Aide:** Si vous ne vous souvenez pas de votre couleur préférée, contactez l'administrateur.")
    
    if st.button("← Retour à la connexion"):
        # Nettoyer le captcha
        if 'captcha_question' in st.session_state:
            del st.session_state.captcha_question
        if 'captcha_answer' in st.session_state:
            del st.session_state.captcha_answer
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

def show_catalogue():
    """Affiche le catalogue des articles"""
    st.markdown("### 🛡️ Catalogue FLUX/PARA")
    
    budget_used = calculate_cart_total()
    budget_remaining = MAX_CART_AMOUNT - budget_used
    
    if budget_remaining > 0:
        st.success(f"💰 Budget disponible: {budget_remaining:.2f}€ (secteur FLUX/PARA)")
    else:
        st.error(f"🚨 Budget FLUX/PARA dépassé de {abs(budget_remaining):.2f}€ !")
    
    with st.sidebar:
        show_cart_sidebar()
    
    categories = [
        "Chaussures", "Veste Blouson", "Gants", "Casque", "Lunette", "Gilet", "Masque",
        "Veste Oxycoupeur", "Sécurité", "Pantalon", "Sous Veste", "Protection",
        "Oxycoupage", "Outil", "Lampe", "Marquage"
    ]
    
    if not st.session_state.get('selected_category'):
        st.markdown("### 📋 Sélectionnez une catégorie")
        cols = st.columns(3)
        for i, category in enumerate(categories):
            with cols[i % 3]:
                emoji = get_category_emoji(category)
                if st.button(f"{emoji} {category}", key=f"cat_{category}", use_container_width=True):
                    st.session_state.selected_category = category
                    st.rerun()
    else:
        category = st.session_state.selected_category
        emoji = get_category_emoji(category)
        if st.button("← Retour aux catégories"):
            st.session_state.selected_category = None
            st.rerun()
        st.markdown(f"#### {emoji} {category}")
        articles_category = articles_df[articles_df['Description'] == category]
        
        # Regrouper les articles par nom de base
        articles_groupes = {}
        for idx, article in articles_category.iterrows():
            nom_complet = article['Nom']
            
            if 'taille' in nom_complet.lower():
                taille_match = re.search(r'taille\s+([a-zA-Z0-9?]+)', nom_complet, re.IGNORECASE)
                if taille_match:
                    taille = taille_match.group(1)
                    nom_base = re.sub(r'\s+taille\s+[a-zA-Z0-9?]+', '', nom_complet, flags=re.IGNORECASE).strip()
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
                    approve_order(order_id, contremaitre)
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

def approve_order(order_id, contremaitre):
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
    current_user = st.session_state.get("current_user", {})
    if current_user.get("role") != "admin":
        return False, "Action réservée à l'administrateur."
    # ... suppression réelle ...

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
    """Met à jour toutes les permissions d'un utilisateur"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
        
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET can_add_articles = ?, 
                can_view_stats = ?, 
                can_view_all_orders = ?
            WHERE id = ?
        """, (
            permissions['can_add_articles'],
            permissions['can_view_stats'], 
            permissions['can_view_all_orders'],
            user_id
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Erreur mise à jour permissions: {e}")
        return False

def create_user(username, password, equipe, fonction, couleur_preferee="DT770", can_add_articles=0, can_view_stats=0, can_view_all_orders=0, role="user"):
    try:
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, equipe, fonction,
                 role, can_add_articles, can_view_stats, can_view_all_orders)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    username,
                    pwd_hash,
                    equipe,
                    fonction,
                    role,
                    bool(can_add_articles),
                    bool(can_view_stats),
                    bool(can_view_all_orders),
                ),
            )
        else:
            conn = sqlite3.connect("users.db")
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
        return True, "✅ Utilisateur créé avec succès !"
    except Exception as e:
        st.error(f"❌ Erreur création utilisateur : {e}")
        return False, f"❌ Erreur création utilisateur : {e}"

def get_category_emoji(category):
    emoji_map = {
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
        'Oxycoupage': '🔧',
        'Outil': '🛠️',
        'Lampe': '💡',
        'Marquage': '✏️'
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
    """Récupère tous les utilisateurs"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # D'abord créer les colonnes si elles n'existent pas
        create_missing_columns()
        
        cursor.execute("""
            SELECT id, username, equipe, fonction, 
                   COALESCE(can_add_articles, 0), 
                   COALESCE(can_view_stats, 0), 
                   COALESCE(can_view_all_orders, 0), 
                   role 
            FROM users
        """)
        
        users = cursor.fetchall()
        conn.close()
        return users
        
    except Exception as e:
        st.error(f"Erreur chargement utilisateurs: {e}")
        return []

def show_admin_page():
    """Page complète d'administration des utilisateurs"""
    st.markdown("# 👥 Gestion des utilisateurs - Administration")
    
    # Deux colonnes principales
    col1, col2 = st.columns(2)
    
    # === CRÉATION D'UTILISATEUR ===
    with col1:
        with st.expander("➕ Créer un nouvel utilisateur", expanded=True):
            with st.form("create_user_form"):
                username = st.text_input("👤 Nom d'utilisateur*")
                password = st.text_input("🔐 Mot de passe*", type="password")
                equipe = st.selectbox("👥 Équipe*", EQUIPES, index=0)
                fonction = st.selectbox("💼 Fonction*", ["contremaitre", "RTZ", "technicien", "chef d'équipe", "responsable sécurité", "autre"], index=0)

                # Logique automatique de permissions selon la fonction
                if fonction.lower() in ["contremaître", "contremaitre", "rtz", "gestionnaire"]:
                    default_add = True
                    default_stats = True
                    default_all = True
                elif fonction.lower() in ["chef d'équipe", "responsable sécurité"]:
                    default_add = False
                    default_stats = True
                    default_all = False
                else:
                    default_add = False
                    default_stats = False
                    default_all = False

                st.markdown("### 🔐 Permissions (automatiques selon la fonction)")
                can_add_articles = st.checkbox("📝 Peut ajouter des articles", value=default_add, key="add_perm")
                can_view_stats = st.checkbox("📊 Peut voir les statistiques", value=default_stats, key="stats_perm")
                can_view_all_orders = st.checkbox("📋 Peut voir toutes les commandes", value=default_all, key="all_perm")
                
                role = st.selectbox("🎭 Rôle:", ["user", "admin"])
                
                if st.form_submit_button("✅ Créer l'utilisateur", use_container_width=True):
                    if username and password and equipe and fonction:
                        if user_exists(username):
                            st.error("Ce nom d'utilisateur existe déjà.")
                        else:
                            c_add = int(can_add_articles)
                            c_stats = int(can_view_stats)
                            c_all = int(can_view_all_orders)
                            equipe_up = equipe.upper()
                            success, msg = create_user(username, password, equipe_up, fonction, "DT770", c_add, c_stats, c_all, role)
                        if success:
                            st.success(f"✅ Utilisateur {username} créé !")
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("❌ Veuillez remplir tous les champs obligatoires")
    
    # === SUPPRESSION D'UTILISATEUR ===
    with col2:
        with st.expander("🗑️ Supprimer un utilisateur", expanded=True):
            users = get_all_users()
            if users:
                for user in users:
                    user_id, username, equipe, fonction, can_add_articles, can_view_stats, can_view_all_orders, role = user
                    if username == 'admin':
                        continue  # Ne pas supprimer l'admin principal
                    st.markdown(f"**{username}** ({equipe}, {fonction}, rôle: {role})")
                    if st.button(f"🗑️ Supprimer {username}", key=f"delete_user_{user_id}", use_container_width=True):
                        success, message = delete_user(user_id)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    st.divider()
            else:
                st.info("Aucun utilisateur trouvé")
    
    # === LISTE DES UTILISATEURS ===
    st.markdown("---")
    show_user_management()

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

def update_user_permissions(user_id, permissions):
    """Met à jour toutes les permissions d'un utilisateur"""
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users 
            SET can_add_articles = ?, 
                can_view_stats = ?, 
                can_view_all_orders = ?
            WHERE id = ?
        """, (
            permissions['can_add_articles'],
            permissions['can_view_stats'], 
            permissions['can_view_all_orders'],
            user_id
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Erreur mise à jour permissions: {e}")
        return False

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
    """Supprime un article (référence) du fichier CSV puis invalide le cache."""
    try:
        df = pd.read_csv("articles.csv")
        ref_col = ref_col or get_ref_col(df)
        if reference not in df[ref_col].astype(str).values:
            return False, "Référence introuvable"
        df = df[df[ref_col].astype(str) != str(reference)]
        df.to_csv("articles.csv", index=False)
        st.cache_data.clear()
        return True, "✅ Article supprimé avec succès"
    except Exception as e:
        return False, f"❌ Erreur suppression article : {e}"

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
    with st.expander("➕ Créer un nouvel utilisateur", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            new_username = st.text_input("Nom d'utilisateur*")
            new_password = st.text_input("Mot de passe*", type="password")
            new_equipe   = st.text_input("Équipe", value="para")
            new_fonction = st.text_input("Fonction", value="contremaître")

        with col2:
            st.markdown("### Permissions")
            p_add   = st.checkbox("Peut ajouter des articles")
            p_stats = st.checkbox("Peut voir les statistiques")
            p_all   = st.checkbox("Peut voir toutes les commandes")
            role    = st.selectbox("Rôle", ["user", "contremaitre", "admin"])

        if st.button("Créer l'utilisateur", use_container_width=True):
            ok, msg = create_new_user(
                new_username,
                new_password,
                new_equipe,
                new_fonction,
                role,
                p_add,
                p_stats,
                p_all,
            )
            (st.success if ok else st.error)(msg)
            if ok:
                st.rerun()

    # ------ LISTE & ÉDITION ----------------------------------------
    st.markdown("### 📄 Utilisateurs existants")
    for (
        uid,
        uname,
        role,
        equipe,
        fonction,
        p_add,
        p_stats,
        p_all,
    ) in get_all_users():
        with st.expander(f"👤 {uname} – {role.upper()} ({equipe})", expanded=False):
            st.write(f"ID : {uid}")
            st.write(f"Fonction : {fonction}")
            st.write("#### ✏️ Modifier")

            e_role   = st.selectbox(
                "Rôle",
                ["user", "contremaitre", "admin"],
                index=["user", "contremaitre", "admin"].index(role),
                key=f"role_{uid}",
            )
            c1, c2, c3 = st.columns(3)
            with c1:
                e_add = st.checkbox(
                    "Ajouter articles",
                    value=bool(p_add),
                    key=f"add_{uid}",
                )
            with c2:
                e_stats = st.checkbox(
                    "Voir stats",
                    value=bool(p_stats),
                    key=f"stats_{uid}",
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
                        'can_view_all_orders': int(e_all)
                    }
                    ok = update_user_permissions(uid, permissions)
                    if ok:
                        # PATCH : si l'utilisateur modifie ses propres droits, on met à jour la session
                        if 'current_user' in st.session_state and st.session_state.current_user.get('id') == uid:
                            st.session_state.current_user['can_add_articles'] = bool(permissions['can_add_articles'])
                            st.session_state.current_user['can_view_stats'] = bool(permissions['can_view_stats'])
                            st.session_state.current_user['can_view_all_orders'] = bool(permissions['can_view_all_orders'])
                        st.success("✅ Permissions mises à jour !")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la mise à jour")

            with b_del:
                if st.button(
                    f"🗑️ Supprimer {uname}",
                    key=f"del_{uid}",
                    use_container_width=True,
                ):
                    delete_user(uid)
                    st.warning("Utilisateur supprimé.")
                    st.rerun()

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
    if USE_POSTGRESQL:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE LOWER(username) = %s", (username.lower(),))
        exists = cursor.fetchone() is not None
        conn.close()
    else:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE LOWER(username) = ?", (username.lower(),))
        exists = cursor.fetchone() is not None
        conn.close()
    return exists

def to_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, int):
        return val == 1
    if isinstance(val, str):
        return val == "1"
    return False

def refresh_current_user_permissions():
    """Recharge les permissions de l'utilisateur courant depuis la base."""
    user_info = st.session_state.get('current_user', {})
    username = user_info.get('username')
    if not username:
        return
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, can_add_articles, can_view_stats, can_view_all_orders
                FROM users WHERE username = %s
            """, (username,))
        else:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, can_add_articles, can_view_stats, can_view_all_orders
                FROM users WHERE username = ?
            """, (username,))
        result = cursor.fetchone()
        conn.close()
        if result:
            st.session_state.current_user['role'] = result[0]
            st.session_state.current_user['can_add_articles'] = to_bool(result[1])
            st.session_state.current_user['can_view_stats'] = to_bool(result[2])
            st.session_state.current_user['can_view_all_orders'] = to_bool(result[3])
    except Exception as e:
        st.error(f"Erreur rafraîchissement permissions : {e}")

if __name__ == "__main__":
    main()

show_admin_users()