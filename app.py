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
    """Charge les articles depuis le fichier CSV avec gestion d'erreurs robuste"""
    try:
        # Essayer plusieurs méthodes de lecture
        try:
            # Méthode 1: Lecture standard avec gestion d'erreurs
            df = pd.read_csv('articles.csv', on_bad_lines='skip', encoding='utf-8')
        except:
            try:
                # Méthode 2: Avec séparateur point-virgule
                df = pd.read_csv('articles.csv', sep=';', on_bad_lines='skip', encoding='utf-8')
            except:
                try:
                    # Méthode 3: Avec engine python (plus lent mais plus robuste)
                    df = pd.read_csv('articles.csv', engine='python', on_bad_lines='skip', encoding='utf-8')
                except:
                    # Méthode 4: Lecture ligne par ligne pour identifier le problème
                    st.warning("⚠️ Problème détecté dans le CSV, nettoyage en cours...")
                    df = read_csv_safe('articles.csv')
        
        # Vérifier que les colonnes essentielles existent
        required_columns = ['Nom', 'Prix', 'Description']
        
        # Si les colonnes n'existent pas, essayer de les mapper
        if 'Nom' not in df.columns:
            # Mapper les colonnes du CSV actuel
            column_mapping = {
                'N° Référence': 'Référence',
                'Nom': 'Nom', 
                'Description': 'Description',
                'Prix': 'Prix',
                'Unitée': 'Unité'
            }
            df = df.rename(columns=column_mapping)
        
        # Nettoyer les données
        df = df.dropna(subset=['Nom', 'Prix'])
        df['Prix'] = pd.to_numeric(df['Prix'], errors='coerce')
        df = df.dropna(subset=['Prix'])
        
        # Ajouter la colonne Description si elle manque
        if 'Description' not in df.columns:
            df['Description'] = df['Nom']
        
        st.success(f"✅ {len(df)} articles chargés avec succès")
        return df
        
    except Exception as e:
        st.error(f"❌ Erreur lecture CSV: {e}")
        st.info("🔄 Utilisation d'articles d'exemple...")
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

# === CSS MODERNE ===
st.markdown("""
<style>
:root {
    --primary-color: #2563eb;
    --primary-dark: #1d4ed8;
    --secondary-color: #f8fafc;
    --text-color: #1e293b;
    --border-color: #e2e8f0;
    --success-color: #10b981;
    --error-color: #ef4444;
    --border-radius: 0.5rem;
    --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
}

.stApp {
    background-color: var(--secondary-color);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stButton > button {
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: var(--border-radius);
    padding: 0.5rem 1rem;
    font-weight: 500;
    transition: all 0.2s;
    box-shadow: var(--shadow);
    width: 100%;
}

.stButton > button:hover {
    background: var(--primary-dark);
    transform: translateY(-1px);
}

/* Animation pour erreurs budget */
@keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
}

.budget-error {
    animation: shake 0.5s ease-in-out;
    border: 2px solid var(--error-color);
    border-radius: var(--border-radius);
    padding: 1rem;
    background: #fef2f2;
}
</style>
""", unsafe_allow_html=True)

# === FONCTIONS BASE DE DONNÉES ===
def init_database():
    """Initialise la base de données avec toutes les tables nécessaires"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Table des utilisateurs avec couleur préférée
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'user',
                    equipe VARCHAR(50),
                    fonction VARCHAR(50),
                    couleur_preferee VARCHAR(30),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des commandes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commandes (
                    id SERIAL PRIMARY KEY,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    contremaître VARCHAR(100),
                    equipe VARCHAR(50),
                    articles_json TEXT,
                    total_prix DECIMAL(10,2),
                    nb_articles INTEGER
                )
            """)
            
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Table des utilisateurs avec couleur préférée
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    equipe TEXT,
                    fonction TEXT,
                    couleur_preferee TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des commandes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commandes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    contremaître TEXT,
                    equipe TEXT,
                    articles_json TEXT,
                    total_prix REAL,
                    nb_articles INTEGER
                )
            """)
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur initialisation base de données: {e}")

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
                INSERT INTO commandes (date, contremaître, equipe, articles_json, total_prix, nb_articles)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            ''', (date_now, commande_data['utilisateur'], commande_data['equipe'], 
                  articles_json, commande_data['total'], nb_articles))
            commande_id = cursor.fetchone()[0]
        else:
            cursor.execute('''
                INSERT INTO commandes (date, contremaître, equipe, articles_json, total_prix, nb_articles)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (date_now, commande_data['utilisateur'], commande_data['equipe'], 
                  articles_json, commande_data['total'], nb_articles))
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

# === GESTION UTILISATEURS ===
def init_users_db():
    """Initialise les utilisateurs par défaut"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            
            # Vérifier si l'admin existe
            cursor.execute("SELECT id FROM users WHERE username = %s", ('admin',))
            if not cursor.fetchone():
                admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
                cursor.execute("""
                    INSERT INTO users (username, password, role, equipe, fonction, couleur_preferee) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, ('admin', admin_password, 'admin', 'DIRECTION', 'Administrateur', 'DT770'))
            else:
                # Mettre à jour l'admin existant avec la couleur DT770
                cursor.execute("UPDATE users SET couleur_preferee = %s WHERE username = %s", ('DT770', 'admin'))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Vérifier si l'admin existe
            cursor.execute("SELECT id FROM users WHERE username = ?", ('admin',))
            if not cursor.fetchone():
                admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
                cursor.execute("""
                    INSERT INTO users (username, password, role, equipe, fonction, couleur_preferee) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ('admin', admin_password, 'admin', 'DIRECTION', 'Administrateur', 'DT770'))
            else:
                # Mettre à jour l'admin existant avec la couleur DT770
                cursor.execute("UPDATE users SET couleur_preferee = ? WHERE username = ?", ('DT770', 'admin'))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        st.error(f"Erreur initialisation utilisateurs: {e}")

def authenticate_user(username, password):
    """Authentifie un utilisateur et retourne ses informations"""
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, role, equipe, fonction 
                FROM users 
                WHERE username = %s AND password = %s
            """, (username, password_hash))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, role, equipe, fonction 
                FROM users 
                WHERE username = ? AND password = ?
            """, (username, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            user_id, username, role, equipe, fonction = user
            return {
                'id': user_id,
                'username': username,
                'role': role,
                'equipe': equipe,
                'fonction': fonction
            }
        else:
            return None
            
    except Exception as e:
        st.error(f"Erreur authentification: {e}")
        return None

def add_user(username, password, role='user', equipe='', fonction='', email=''):
    """Ajoute un nouvel utilisateur"""
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password, role, equipe, fonction, email)
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
    """Ajoute un article au panier avec vérification budget"""
    prix_ajout = float(article['Prix']) * quantity
    nouveau_total = calculate_cart_total() + prix_ajout
    
    if nouveau_total > MAX_CART_AMOUNT:
        budget_depasse = nouveau_total - MAX_CART_AMOUNT
        
        messages_budget = [
            "Holà ! Tu veux ruiner le secteur FLUX/PARA ? 😅",
            "Attention, comptable en panique ! 🤯",
            "Le budget fait une crise cardiaque ! 💔",
            "Budget FLUX/PARA K.O. ! 🥊",
            "Erreur 404 : Budget not found ! 🔍"
        ]
        
        message_rigolo = random.choice(messages_budget)
        
        st.session_state.budget_error = {
            'message': message_rigolo,
            'nouveau_total': nouveau_total,
            'budget_max': MAX_CART_AMOUNT,
            'depassement': budget_depasse,
            'details': f"Vous tentez d'ajouter {prix_ajout:.2f}€, mais cela dépasserait le budget de {budget_depasse:.2f}€",
            'timestamp': time.time()
        }
        
        return False
    
    for _ in range(quantity):
        st.session_state.cart.append(convert_pandas_to_dict(article))
    
    if quantity == 1:
        st.toast(f"✅ {article['Nom']} ajouté au panier !", icon="🛒")
    else:
        st.toast(f"✅ {quantity}x {article['Nom']} ajoutés au panier !", icon="🛒")
    
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
    
    for group in grouped_articles:
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
                if st.button("➖", key=f"sidebar_minus_{article['Nom']}", help="Réduire quantité"):
                    remove_from_cart(article)
                    st.rerun()
            
            with col_qty:
                st.markdown(f"<div style='text-align: center; font-size: 14px; font-weight: bold; padding: 4px;'>{quantite}</div>", unsafe_allow_html=True)
            
            with col_plus:
                if st.button("➕", key=f"sidebar_plus_{article['Nom']}", help="Augmenter quantité"):
                    add_to_cart(article, 1)
                    st.rerun()
            
            with col_del:
                if st.button("🗑️", key=f"sidebar_delete_{article['Nom']}", help="Supprimer"):
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
    """Page de connexion"""
    st.markdown("### 🔐 Connexion FLUX/PARA")
    
    with st.form("login_form"):
        username = st.text_input("👤 Nom d'utilisateur")
        password = st.text_input("🔒 Mot de passe", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            login_button = st.form_submit_button("🚀 Se connecter", use_container_width=True)
        with col2:
            register_button = st.form_submit_button("📝 S'inscrire", use_container_width=True)
        
        if login_button:
            if not username or not password:
                st.error("❌ Veuillez remplir tous les champs")
            else:
                user_info = authenticate_user(username, password)
                if user_info:
                    st.session_state.authenticated = True
                    st.session_state.current_user = user_info
                    st.session_state.page = "catalogue"
                    st.success(f"✅ Connexion réussie ! Bienvenue {user_info['username']}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects")
        
        if register_button:
            st.session_state.page = 'register'
            st.rerun()
    
    # Lien mot de passe oublié
    st.markdown("---")
    if st.button("🔑 Mot de passe oublié ?"):
        st.session_state.page = 'reset_password'
        st.rerun()

def show_register():
    """Page d'inscription"""
    st.markdown("### 📝 Créer un compte")
    
    with st.form("register_form"):
        username = st.text_input("👤 Nom d'utilisateur")
        password = st.text_input("🔒 Mot de passe", type="password")
        password_confirm = st.text_input("🔒 Confirmer le mot de passe", type="password")
        
        # Sélection d'équipe
        equipes = ["DIRECTION", "FLUX", "PARA", "MAINTENANCE", "QUALITE", "LOGISTIQUE"]
        equipe = st.selectbox("👷‍♂️ Équipe", equipes)
        
        # Fonction
        fonctions = ["Contremaître", "RTZ", "Technicien", "Responsable", "Autre"]
        fonction = st.selectbox("🔧 Fonction", fonctions)
        
        # Question de sécurité
        couleur_preferee = st.text_input("🎨 Votre couleur préférée", placeholder="Pour la récupération de mot de passe")
        
        submitted = st.form_submit_button("✅ Créer le compte", use_container_width=True)
        
        if submitted:
            if not all([username, password, password_confirm, couleur_preferee]):
                st.error("❌ Veuillez remplir tous les champs")
            elif password != password_confirm:
                st.error("❌ Les mots de passe ne correspondent pas")
            elif len(password) < 6:
                st.error("❌ Le mot de passe doit contenir au moins 6 caractères")
            else:
                success, message = create_user(username, password, equipe, fonction, couleur_preferee)
                if success:
                    st.success(f"✅ {message}")
                    time.sleep(2)
                    st.session_state.page = 'login'
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    st.markdown("---")
    if st.button("← Retour à la connexion"):
        st.session_state.page = 'login'
        st.rerun()

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
    
    categories = articles_df['Description'].unique()
    
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
                'total': total
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
    """Page des commandes personnelles pour les contremaîtres"""
    st.markdown("### 📊 Mes commandes")
    
    user_info = st.session_state.get('current_user', {})
    username = user_info.get('username', '')
    
    if not username:
        st.error("❌ Erreur: utilisateur non connecté")
        return
    
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
        
        cursor = conn.cursor()
        
        # Récupérer SEULEMENT les commandes de ce contremaître
        cursor.execute("""
            SELECT id, date, contremaître, equipe, articles_json, total_prix, nb_articles
            FROM commandes 
            WHERE contremaître = ?
            ORDER BY date DESC
        """, (username,))
        
        commandes = cursor.fetchall()
        conn.close()
        
        if not commandes:
            st.info("📭 Vous n'avez encore passé aucune commande")
            if st.button("🛡️ Aller au catalogue"):
                st.session_state.page = "catalogue"
                st.rerun()
            return
        
        # Statistiques personnelles
        df_commandes = pd.DataFrame(commandes, columns=[
            'id', 'date', 'contremaître', 'equipe', 'articles_json', 'total_prix', 'nb_articles'
        ])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_commandes = len(df_commandes)
            st.metric("🛡️ Mes commandes", total_commandes)
        
        with col2:
            total_montant = df_commandes['total_prix'].sum()
            st.metric("💰 Total dépensé", f"{total_montant:.2f}€")
        
        with col3:
            moyenne_commande = df_commandes['total_prix'].mean()
            st.metric("📊 Moyenne/commande", f"{moyenne_commande:.2f}€")
        
        st.markdown("---")
        
        # Afficher les commandes
        for commande in commandes:
            commande_id, date, contremaitre, equipe, articles_json, total_prix, nb_articles = commande
            
            with st.expander(f"🛡️ Commande #{commande_id} - {date} - {total_prix:.2f}€"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**📅 Date:** {date}")
                    st.markdown(f"**👷‍♂️ Équipe:** {equipe}")
                
                with col2:
                    st.markdown(f"**💰 Total:** {total_prix:.2f}€")
                    st.markdown(f"**📦 Nb articles:** {nb_articles}")
                
                # Afficher les articles
                try:
                    articles = json.loads(articles_json)
                    grouped_articles = grouper_articles_panier(articles)
                    
                    st.markdown("**Articles commandés:**")
                    for group in grouped_articles:
                        article = group['article']
                        quantite = group['quantite']
                        prix_total = float(article['Prix']) * quantite
                        st.markdown(f"• {article['Nom']} - Quantité: {quantite} - {prix_total:.2f}€")
                        
                except Exception as e:
                    st.error(f"Erreur affichage articles: {e}")
        
    except Exception as e:
        st.error(f"Erreur chargement commandes: {e}")

def show_stats():
    """Page de statistiques des commandes - Selon permissions"""
    user_info = st.session_state.get('current_user', {})
    
    # Vérifier les droits
    if not user_can_view_stats():
        st.error("🚫 Accès refusé - Vous n'avez pas l'autorisation de voir les statistiques")
        st.info("Contactez un administrateur pour obtenir cette permission.")
        return
    
    # Titre selon le rôle
    if user_info.get('role') == 'admin':
        st.markdown("### 📊 Statistiques globales - Administration")
    else:
        st.markdown("### 📊 Statistiques des commandes")
    
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
        
        cursor = conn.cursor()
        
        # Récupérer toutes les commandes
        cursor.execute("""
            SELECT id, date, contremaître, equipe, articles_json, total_prix, nb_articles
            FROM commandes 
            ORDER BY date DESC
        """)
        
        commandes = cursor.fetchall()
        conn.close()
        
        if not commandes:
            st.info("📭 Aucune commande trouvée pour générer des statistiques")
            return
        
        # Convertir en DataFrame pour faciliter l'analyse
        df_commandes = pd.DataFrame(commandes, columns=[
            'id', 'date', 'contremaître', 'equipe', 'articles_json', 'total_prix', 'nb_articles'
        ])
        
        # Convertir les dates
        df_commandes['date'] = pd.to_datetime(df_commandes['date'])
        df_commandes['mois'] = df_commandes['date'].dt.to_period('M')
        
        # === MÉTRIQUES GÉNÉRALES ===
        st.markdown("### 📈 Vue d'ensemble")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_commandes = len(df_commandes)
            st.metric("🛡️ Total commandes", total_commandes)
        
        with col2:
            total_montant = df_commandes['total_prix'].sum()
            st.metric("💰 Montant total", f"{total_montant:.2f}€")
        
        with col3:
            moyenne_commande = df_commandes['total_prix'].mean()
            st.metric("📊 Moyenne/commande", f"{moyenne_commande:.2f}€")
        
        with col4:
            total_articles = df_commandes['nb_articles'].sum()
            st.metric("📦 Total articles", total_articles)
        
        st.markdown("---")
        
        # === GRAPHIQUES ===
        col1, col2 = st.columns(2)
        
        with col1:
            # Évolution des commandes par mois
            st.markdown("#### 📅 Évolution mensuelle")
            commandes_par_mois = df_commandes.groupby('mois').agg({
                'id': 'count',
                'total_prix': 'sum'
            }).reset_index()
            commandes_par_mois['mois_str'] = commandes_par_mois['mois'].astype(str)
            
            fig_evolution = px.line(
                commandes_par_mois, 
                x='mois_str', 
                y='id',
                title="Nombre de commandes par mois",
                labels={'id': 'Nb commandes', 'mois_str': 'Mois'}
            )
            fig_evolution.update_layout(height=400)
            st.plotly_chart(fig_evolution, use_container_width=True)
        
        with col2:
            # Répartition par équipe
            st.markdown("#### 👷‍♂️ Répartition par équipe")
            commandes_par_equipe = df_commandes.groupby('equipe').agg({
                'id': 'count',
                'total_prix': 'sum'
            }).reset_index()
            
            fig_equipes = px.pie(
                commandes_par_equipe,
                values='id',
                names='equipe',
                title="Commandes par équipe"
            )
            fig_equipes.update_layout(height=400)
            st.plotly_chart(fig_equipes, use_container_width=True)
        
        # === MONTANTS PAR MOIS ===
        st.markdown("#### 💰 Évolution des montants")
        fig_montants = px.bar(
            commandes_par_mois,
            x='mois_str',
            y='total_prix',
            title="Montant total des commandes par mois",
            labels={'total_prix': 'Montant (€)', 'mois_str': 'Mois'}
        )
        fig_montants.update_layout(height=400)
        st.plotly_chart(fig_montants, use_container_width=True)
        
        # === TOP CONTREMAÎTRES ===
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏆 Top contremaîtres (nb commandes)")
            top_contremaitres = df_commandes.groupby('contremaître').agg({
                'id': 'count',
                'total_prix': 'sum'
            }).sort_values('id', ascending=False).head(10)
            
            for idx, (contremaitre, data) in enumerate(top_contremaitres.iterrows(), 1):
                st.markdown(f"{idx}. **{contremaitre}** - {data['id']} commandes ({data['total_prix']:.2f}€)")
        
        with col2:
            st.markdown("#### 💎 Top contremaîtres (montant)")
            top_montants = df_commandes.groupby('contremaître').agg({
                'id': 'count',
                'total_prix': 'sum'
            }).sort_values('total_prix', ascending=False).head(10)
            
            for idx, (contremaitre, data) in enumerate(top_montants.iterrows(), 1):
                st.markdown(f"{idx}. **{contremaitre}** - {data['total_prix']:.2f}€ ({data['id']} commandes)")
        
        # === ANALYSE DES ARTICLES ===
        st.markdown("---")
        st.markdown("#### 📦 Analyse des articles les plus commandés")
        
        # Analyser tous les articles commandés
        tous_articles = []
        for articles_json in df_commandes['articles_json']:
            try:
                articles = json.loads(articles_json)
                for article in articles:
                    tous_articles.append({
                        'nom': article['Nom'],
                        'prix': float(article['Prix']),
                        'categorie': article.get('Catégorie', 'Non définie')
                    })
            except:
                continue
        
        if tous_articles:
            df_articles = pd.DataFrame(tous_articles)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Articles les plus commandés
                top_articles = df_articles['nom'].value_counts().head(10)
                st.markdown("**🔥 Articles les plus commandés:**")
                for idx, (article, count) in enumerate(top_articles.items(), 1):
                    st.markdown(f"{idx}. {article} - {count}x")
            
            with col2:
                # Répartition par catégorie
                if 'categorie' in df_articles.columns:
                    categories = df_articles['categorie'].value_counts()
                    fig_categories = px.pie(
                        values=categories.values,
                        names=categories.index,
                        title="Répartition par catégorie"
                    )
                    fig_categories.update_layout(height=300)
                    st.plotly_chart(fig_categories, use_container_width=True)
        
        # === TABLEAU DÉTAILLÉ ===
        st.markdown("---")
        st.markdown("#### 📋 Tableau détaillé des commandes")
        
        # Préparer les données pour affichage
        df_display = df_commandes[['id', 'date', 'contremaître', 'equipe', 'total_prix', 'nb_articles']].copy()
        df_display['date'] = df_display['date'].dt.strftime('%d/%m/%Y %H:%M')
        df_display.columns = ['ID', 'Date', 'Contremaître', 'Équipe', 'Montant (€)', 'Nb articles']
        
        st.dataframe(df_display, use_container_width=True)
        
        # === EXPORT ===
        st.markdown("---")
        st.markdown("#### 📥 Export des données")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export CSV
            csv_data = df_display.to_csv(index=False)
            st.download_button(
                label="📊 Télécharger CSV",
                data=csv_data,
                file_name=f"statistiques_commandes_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Résumé statistique
            if st.button("📈 Générer rapport PDF", use_container_width=True):
                st.info("🚧 Fonctionnalité en développement")
        
    except Exception as e:
        st.error(f"Erreur chargement statistiques: {e}")

def show_historique():
    """Page d'historique des commandes - Selon permissions"""
    user_info = st.session_state.get('current_user', {})
    
    # Vérifier les droits
    if not user_can_view_all_orders():
        st.error("🚫 Accès refusé - Vous n'avez pas l'autorisation de voir toutes les commandes")
        st.info("Contactez un administrateur pour obtenir cette permission.")
        return
    
    # Titre selon le rôle
    if user_info.get('role') == 'admin':
        st.markdown("### 📊 Historique global - Administration")
    else:
        st.markdown("### 📊 Historique des commandes")
    
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
        
        cursor = conn.cursor()
    
        # Récupérer toutes les commandes
        cursor.execute("""
            SELECT id, date, contremaître, equipe, articles_json, total_prix, nb_articles
            FROM commandes 
            ORDER BY date DESC
        """)
        
        commandes = cursor.fetchall()
        conn.close()
    
        if not commandes:
            st.info("📭 Aucune commande trouvée")
            return
    
        # Afficher les commandes
        for commande in commandes:
            commande_id, date, contremaitre, equipe, articles_json, total_prix, nb_articles = commande
            
            # Colonnes pour l'affichage et la suppression (admin seulement)
            if user_info.get('role') == 'admin':
                col1, col2 = st.columns([4, 1])
            else:
                col1 = st.container()
                col2 = None
            
            with col1:
                with st.expander(f"🛡️ Commande #{commande_id} - {contremaitre} ({equipe}) - {total_prix:.2f}€"):
                    col_info1, col_info2 = st.columns(2)
            
                    with col_info1:
                        st.markdown(f"**📅 Date:** {date}")
                        st.markdown(f"**👨‍💼 Contremaître:** {contremaitre}")
                        st.markdown(f"**👷‍♂️ Équipe:** {equipe}")
                    
                    with col_info2:
                        st.markdown(f"**💰 Total:** {total_prix:.2f}€")
                        st.markdown(f"**📦 Nb articles:** {nb_articles}")
                    
                    # Afficher les articles
                    try:
                        articles = json.loads(articles_json)
                        grouped_articles = grouper_articles_panier(articles)
                        
                        st.markdown("**Articles commandés:**")
                        for group in grouped_articles:
                            article = group['article']
                            quantite = group['quantite']
                            prix_total = float(article['Prix']) * quantite
                            st.markdown(f"• {article['Nom']} - Quantité: {quantite} - {prix_total:.2f}€")
                            
                    except Exception as e:
                        st.error(f"Erreur affichage articles: {e}")
            
            # Bouton de suppression pour admin seulement
            if user_info.get('role') == 'admin' and col2:
                with col2:
                    st.write("")  # Espacement
                    if st.button(f"🗑️ Supprimer", key=f"delete_{commande_id}", type="secondary"):
                        st.session_state[f"confirm_delete_{commande_id}"] = True
                        st.rerun()
                    
                    # Confirmation de suppression
                    if st.session_state.get(f"confirm_delete_{commande_id}", False):
                        st.warning("⚠️ Confirmer ?")
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("✅ Oui", key=f"confirm_yes_{commande_id}"):
                                if delete_commande(commande_id):
                                    st.success("✅ Supprimée")
                                    st.session_state[f"confirm_delete_{commande_id}"] = False
                                    st.rerun()
                                else:
                                    st.error("❌ Erreur")
                        with col_no:
                            if st.button("❌ Non", key=f"confirm_no_{commande_id}"):
                                st.session_state[f"confirm_delete_{commande_id}"] = False
                                st.rerun()
        
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
    """Navigation principale avec différenciation selon le rôle et permissions"""
    user_info = st.session_state.get('current_user', {})
    user_role = user_info.get('role', 'user')
    
    if user_role == 'admin':
        # Navigation complète pour admin
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        
        with col1:
            if st.button("🛡️ Catalogue", use_container_width=True):
                st.session_state.page = "catalogue"
                st.rerun()
        
        with col2:
            if st.button("🛒 Panier", use_container_width=True):
                st.session_state.page = "cart"
                st.rerun()
        
        with col3:
            if st.button("📊 Historique", use_container_width=True):
                st.session_state.page = "historique"
                st.rerun()
        
        with col4:
            if st.button("📈 Statistiques", use_container_width=True):
                st.session_state.page = "stats"
                st.rerun()
        
        with col5:
            if st.button("🛠️ Articles", use_container_width=True):
                st.session_state.page = "admin_articles"
                st.rerun()
        
        with col6:
            if st.button("👥 Utilisateurs", use_container_width=True):
                st.session_state.page = "admin_users"
                st.rerun()
        
        with col7:
            if st.button("🚪 Déconnexion", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.current_user = {}
                st.session_state.page = "login"
                st.rerun()
    
    else:
        # Navigation pour contremaîtres selon leurs permissions
        buttons = []
        
        # Boutons de base
        buttons.extend([
            ("🛡️ Catalogue", "catalogue"),
            ("🛒 Panier", "cart"),
            ("📊 Mes commandes", "mes_commandes")
        ])
        
        # Boutons selon permissions
        if user_can_view_all_orders():
            buttons.append(("📋 Historique", "historique"))
        
        if user_can_view_stats():
            buttons.append(("📈 Statistiques", "stats"))
        
        if user_can_add_articles():
            buttons.append(("➕ Articles", "admin_articles"))
        
        # Bouton déconnexion
        buttons.append(("🚪 Déconnexion", "logout"))
        
        # Créer les colonnes dynamiquement
        cols = st.columns(len(buttons))
        
        for i, (label, page) in enumerate(buttons):
            with cols[i]:
                if page == "logout":
                    if st.button(label, use_container_width=True):
                        st.session_state.authenticated = False
                        st.session_state.current_user = {}
                        st.session_state.page = "login"
                        st.rerun()
                else:
                    if st.button(label, use_container_width=True):
                        st.session_state.page = page
                        st.rerun()

def main():
    """Fonction principale de l'application"""
    # Initialiser la base de données
    init_database()
    
    # Migration pour ajouter la couleur préférée
    migrate_add_couleur_column()
    
    # Initialiser l'utilisateur admin
    init_users_db()
    
    # Initialiser les variables de session
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'cart' not in st.session_state:
        st.session_state.cart = []
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    
    # Navigation selon l'état d'authentification
    if not st.session_state.get('authenticated', False):
        if st.session_state.get('page') == 'register':
            show_register()
        elif st.session_state.get('page') == 'reset_password':
            show_reset_password()
        else:
            show_login()
    else:
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
            show_historique()
        elif page == "stats":
            show_stats()
        elif page == "mes_commandes":
            show_mes_commandes()
        elif page == "admin_articles":
            show_admin_articles()
        elif page == "admin_users":
            show_admin_users()
        else:
            show_catalogue()

def show_admin_articles():
    """Page de gestion des articles - ADMIN et contremaîtres autorisés"""
    user_info = st.session_state.get('current_user', {})
    
    # Vérifier les droits
    if not user_can_add_articles():
        st.error("🚫 Accès refusé - Vous n'avez pas l'autorisation d'ajouter des articles")
        st.info("Contactez un administrateur pour obtenir cette permission.")
        return
    
    # Titre différent selon le rôle
    if user_info.get('role') == 'admin':
        st.markdown("### 🛠️ Gestion des articles - Administration")
    else:
        st.markdown("### ➕ Ajouter des articles")
    
    # Onglets selon les permissions
    if user_info.get('role') == 'admin':
        # Admin : tous les onglets
        tab1, tab2, tab3 = st.tabs(["📋 Catalogue actuel", "➕ Ajouter article", "📁 Import CSV"])
    else:
        # Contremaître : seulement ajout individuel
        tab1, tab2 = st.tabs(["📋 Catalogue actuel", "➕ Ajouter article"])
        tab3 = None
    
    with tab1:
        # Afficher le catalogue actuel (lecture seule pour contremaîtres)
        st.markdown("#### 📋 Articles actuels")
        
        if not articles_df.empty:
            # Statistiques rapides
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📦 Total articles", len(articles_df))
            with col2:
                if 'Prix' in articles_df.columns:
                    prix_moyen = articles_df['Prix'].astype(float).mean()
                    st.metric("💰 Prix moyen", f"{prix_moyen:.2f}€")
            with col3:
                if 'Catégorie' in articles_df.columns:
                    nb_categories = articles_df['Catégorie'].nunique()
                    st.metric("🏷️ Catégories", nb_categories)
            
            # Tableau
            st.markdown("**Catalogue complet:**")
            st.dataframe(articles_df, use_container_width=True)
            
            # Bouton téléchargement seulement pour admin
            if user_info.get('role') == 'admin':
                csv_data = articles_df.to_csv(index=False)
                st.download_button(
                    label="📥 Télécharger CSV actuel",
                    data=csv_data,
                    file_name=f"articles_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
        else:
            st.warning("⚠️ Aucun article trouvé dans le catalogue")
    
    with tab2:
        # Formulaire d'ajout d'article (accessible aux deux)
        st.markdown("#### ➕ Ajouter un nouvel article")
        
        # Message pour contremaîtres
        if user_info.get('role') != 'admin':
            st.info("🛠️ Vous avez l'autorisation d'ajouter des articles au catalogue.")
        
        # ... reste du code du formulaire identique ...
        with st.form("add_article_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Récupérer la prochaine référence disponible
                if not articles_df.empty and 'Référence' in articles_df.columns:
                    try:
                        max_ref = articles_df['Référence'].astype(int).max()
                        next_ref = max_ref + 1
                    except:
                        next_ref = 50000
                else:
                    next_ref = 40000
                
                reference = st.number_input("🔢 Référence", value=next_ref, min_value=1)
                nom = st.text_input("📝 Nom de l'article", placeholder="Ex: Chaussure de sécurité JALAS Taille 42")
                prix = st.number_input("💰 Prix (€)", min_value=0.0, step=0.01, format="%.2f")
            
            with col2:
                # Récupérer les catégories existantes
                if not articles_df.empty and 'Catégorie' in articles_df.columns:
                    categories_existantes = articles_df['Catégorie'].dropna().unique().tolist()
                else:
                    categories_existantes = []
                
                # Option pour nouvelle catégorie ou existante
                nouvelle_categorie = st.checkbox("Créer une nouvelle catégorie")
                
                if nouvelle_categorie:
                    categorie = st.text_input("🏷️ Nouvelle catégorie", placeholder="Ex: Chaussures de sécurité")
                else:
                    if categories_existantes:
                        categorie = st.selectbox("🏷️ Catégorie", categories_existantes)
                    else:
                        categorie = st.text_input("🏷️ Catégorie", placeholder="Ex: Chaussures de sécurité")
                
                description = st.text_area("📄 Description (optionnel)", placeholder="Description détaillée de l'article")
            
            submitted = st.form_submit_button("✅ Ajouter l'article", use_container_width=True)
            
            if submitted:
                if nom and prix > 0:
                    # Ajouter l'article au CSV
                    nouvel_article = {
                        'Référence': reference,
                        'Nom': nom,
                        'Prix': prix,
                        'Catégorie': categorie,
                        'Description': description
                    }
                    
                    if add_article_to_csv(nouvel_article):
                        st.success(f"✅ Article '{nom}' ajouté avec succès !")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de l'ajout de l'article")
                else:
                    st.error("❌ Veuillez remplir tous les champs obligatoires")
    
    # Onglet import seulement pour admin
    if tab3 and user_info.get('role') == 'admin':
        with tab3:
            # ... code import CSV identique ...
            pass

def add_article_to_csv(nouvel_article):
    """Ajoute un article au fichier CSV"""
    try:
        global articles_df
        
        # Charger le CSV actuel
        try:
            df_actuel = pd.read_csv('articles.csv')
        except FileNotFoundError:
            # Créer un nouveau DataFrame si le fichier n'existe pas
            df_actuel = pd.DataFrame(columns=['Référence', 'Nom', 'Prix', 'Catégorie', 'Description'])
        
        # Ajouter le nouvel article
        nouveau_df = pd.concat([df_actuel, pd.DataFrame([nouvel_article])], ignore_index=True)
        
        # Sauvegarder
        nouveau_df.to_csv('articles.csv', index=False)
        
        # Recharger le cache
        st.cache_data.clear()
        articles_df = load_articles()
        
        return True
        
    except Exception as e:
        st.error(f"Erreur ajout article: {e}")
        return False


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
    """Interface d'administration des utilisateurs"""
    st.markdown("### 👥 Gestion des utilisateurs - Administration")
    
    # Afficher la liste des utilisateurs
    st.markdown("#### 📋 Liste des utilisateurs et permissions")
    
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, role, equipe, fonction, couleur_preferee, created_at 
                FROM users 
                ORDER BY created_at DESC
            """)
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, role, equipe, fonction, couleur_preferee, created_at 
                FROM users 
                ORDER BY created_at DESC
            """)
        
        users = cursor.fetchall()
        conn.close()
        
        if users:
            for user in users:
                user_id, username, role, equipe, fonction, couleur, created_at = user
                
                with st.expander(f"👤 {username} ({role}) - {equipe or 'N/A'}", expanded=False):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**ID:** {user_id}")
                        st.write(f"**Rôle:** {role}")
                        st.write(f"**Équipe:** {equipe or 'Non définie'}")
                        st.write(f"**Fonction:** {fonction or 'Non définie'}")
                    
                    with col2:
                        st.write(f"**Couleur préférée:** {couleur or 'Non définie'}")
                        st.write(f"**Créé le:** {created_at}")
                        
                        # Modifier le rôle
                        new_role = st.selectbox(
                            "Modifier le rôle:", 
                            ["user", "admin"], 
                            index=0 if role == "user" else 1,
                            key=f"role_{user_id}"
                        )
                        
                        if st.button(f"💾 Sauvegarder rôle", key=f"save_{user_id}"):
                            if update_user_role(user_id, new_role):
                                st.success("✅ Rôle mis à jour")
                                st.rerun()
                            else:
                                st.error("❌ Erreur mise à jour")
                    
                    with col3:
                        # Bouton de suppression (sauf pour admin)
                        if username != "admin":
                            if st.button(f"🗑️ Supprimer", key=f"delete_{user_id}", type="secondary"):
                                if st.session_state.get(f"confirm_delete_{user_id}", False):
                                    if delete_user(user_id):
                                        st.success(f"✅ Utilisateur {username} supprimé")
                                        st.rerun()
                                    else:
                                        st.error("❌ Erreur suppression")
                                else:
                                    st.session_state[f"confirm_delete_{user_id}"] = True
                                    st.warning("⚠️ Cliquez à nouveau pour confirmer la suppression")
                        else:
                            st.info("🔒 Admin protégé")
        else:
            st.info("Aucun utilisateur trouvé")
            
    except Exception as e:
        st.error(f"Erreur chargement utilisateurs: {e}")

def update_user_role(user_id, new_role):
    """Met à jour le rôle d'un utilisateur"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Erreur mise à jour rôle: {e}")
        return False

def delete_user(user_id):
    """Supprime un utilisateur"""
    try:
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Erreur suppression utilisateur: {e}")
        return False

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
            SELECT can_view_all_orders 
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

def create_user(username, password, equipe=None, fonction=None, couleur_preferee=None):
    """Crée un nouvel utilisateur"""
    try:
        # Hacher le mot de passe
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if USE_POSTGRESQL:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password, role, equipe, fonction, couleur_preferee) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username.strip(), password_hash, 'user', equipe, fonction, couleur_preferee))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password, role, equipe, fonction, couleur_preferee) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username.strip(), password_hash, 'user', equipe, fonction, couleur_preferee))
        
        conn.commit()
        conn.close()
        return True, "Compte créé avec succès"
        
    except Exception as e:
        if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e):
            return False, "Ce nom d'utilisateur existe déjà"
        return False, f"Erreur création utilisateur: {e}"

def get_category_emoji(category):
    """Retourne l'emoji correspondant à chaque catégorie"""
    emoji_map = {
        'Chaussures': '👟',
        'Veste Blouson': '🧥', 
        'Sous Veste': '👕',
        'Veste Oxycoupeur': '🔥',
        'Sécurité': '🦺',
        'Gants': '🧤',
        'Pantalon': '👖',
        'Casque': '⛑️',
        'Protection': '🛡️',
        'Lunette': '🥽',
        'Oxycoupage': '🔧',
        'Outil': '🔨',
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
                SELECT id, date, total, status, articles 
                FROM orders 
                WHERE user_id = %s 
                ORDER BY date DESC
            """, (user_id,))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, date, total, status, articles 
                FROM orders 
                WHERE user_id = ? 
                ORDER BY date DESC
            """, (user_id,))
        
        orders = cursor.fetchall()
        conn.close()
        return orders
        
    except Exception as e:
        st.error(f"Erreur chargement commandes: {e}")
        return []

def show_my_orders():
    """Affiche les commandes de l'utilisateur connecté"""
    st.markdown("### 📊 Mes commandes")
    
    if not st.session_state.get('current_user'):
        st.error("❌ Utilisateur non connecté")
        return
    
    user_id = st.session_state.current_user['id']
    orders = get_user_orders(user_id)
    
    if not orders:
        st.info("📦 Aucune commande trouvée")
        return
    
    for order in orders:
        order_id, date, total, status, articles_json = order
        
        with st.expander(f"🛍️ Commande #{order_id} - {date} - {total:.2f}€"):
            st.write(f"**Statut:** {status}")
            
            try:
                articles = json.loads(articles_json) if articles_json else []
                if articles:
                    st.write("**Articles commandés:**")
                    for article in articles:
                        st.write(f"- {article.get('Nom', 'N/A')} - {article.get('Prix', 0):.2f}€")
                else:
                    st.write("Aucun article dans cette commande")
            except json.JSONDecodeError:
                st.write("Erreur de lecture des articles")

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
            cursor.execute("UPDATE users SET password = %s WHERE username = %s", (password_hash, username))
        else:
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (password_hash, username))
        
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

if __name__ == "__main__":
    main()