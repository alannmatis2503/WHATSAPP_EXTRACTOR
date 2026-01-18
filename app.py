import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
from datetime import datetime
from collections import Counter
import zipfile
import io

def is_phone_number(name):
    """Vérifie si le nom est un numéro de téléphone (contact non enregistré)"""
    # Pattern pour détecter les numéros de téléphone
    # Exemples: +237 6 90 99 37 08, +237690993708, +33 6 12 34 56 78
    phone_pattern = r'^\+?\d[\d\s\-\.]{6,}$'
    return bool(re.match(phone_pattern, name.strip()))

# Configuration de la page
st.set_page_config(
    page_title="WhatsApp Analytics",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé - Design convivial et apaisant
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');
    
    /* Fond général - tons clairs et apaisants */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 50%, #d9e2ec 100%);
    }
    
    /* Titres */
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif !important;
        color: #2d3748 !important;
    }
    
    .main-title {
        font-family: 'Poppins', sans-serif !important;
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        text-align: center;
        padding: 1.5rem 0;
        color: #4a5568 !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .subtitle {
        text-align: center;
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        color: #718096;
        margin-bottom: 2rem;
    }
    
    /* Cartes de statistiques */
    .stat-card {
        background: white;
        border: none;
        border-radius: 16px;
        padding: 24px;
        margin: 10px 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }
    
    .stat-value {
        font-family: 'Poppins', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .stat-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 8px;
    }
    
    /* Boutons */
    .stButton>button {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 28px;
        font-size: 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Zone de téléchargement */
    .uploadedFile {
        border: 2px dashed #667eea !important;
        border-radius: 12px !important;
        background: rgba(102, 126, 234, 0.05) !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e2e8f0;
    }
    
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #4a5568 !important;
    }
    
    /* Sélecteurs */
    div[data-baseweb="select"] > div {
        background-color: white !important;
        border-color: #e2e8f0 !important;
        border-radius: 10px !important;
    }
    
    /* Texte général */
    .stMarkdown {
        font-family: 'Inter', sans-serif;
        color: #4a5568;
    }
    
    /* Feature cards */
    .feature-card {
        background: white;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        transition: all 0.3s ease;
        margin: 10px;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 16px;
    }
    
    .feature-title {
        font-family: 'Poppins', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 8px;
    }
    
    .feature-desc {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #718096;
    }
    
    /* Section instructions */
    .instructions-box {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    /* DataFrames */
    .dataframe {
        font-family: 'Inter', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)

def parse_whatsapp_file(file_content):
    """Parse le contenu d'un fichier WhatsApp et extrait les messages"""
    lines = file_content.split('\n')
    messages = []
    
    # Pattern pour détecter une nouvelle ligne de message
    pattern = r'(\d{1,2}/\d{1,2}/\d{4}),\s*(\d{1,2}:\d{2})\s*-\s*([^:]+):\s*(.*)'
    
    current_message = None
    
    for line in lines:
        match = re.match(pattern, line)
        if match:
            if current_message:
                messages.append(current_message)
            
            date_str, time_str, sender, content = match.groups()
            
            # Ignorer les messages système
            if sender.startswith('‎'):
                current_message = None
                continue
            
            try:
                datetime_str = f"{date_str} {time_str}"
                dt = datetime.strptime(datetime_str, "%d/%m/%Y %H:%M")
                
                current_message = {
                    'datetime': dt,
                    'date': dt.date(),
                    'time': dt.time(),
                    'sender': sender.strip(),
                    'message': content.strip()
                }
            except:
                current_message = None
        elif current_message and line.strip():
            current_message['message'] += ' ' + line.strip()
    
    if current_message:
        messages.append(current_message)
    
    return pd.DataFrame(messages)

def load_file(uploaded_file):
    """Charge un fichier txt ou zip"""
    if uploaded_file.name.endswith('.zip'):
        with zipfile.ZipFile(io.BytesIO(uploaded_file.read())) as z:
            txt_files = [f for f in z.namelist() if f.endswith('.txt')]
            if txt_files:
                with z.open(txt_files[0]) as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    return content
    else:
        return uploaded_file.read().decode('utf-8', errors='ignore')
    
    return None

# Header
st.markdown('<h1 class="main-title">💬 WhatsApp Analytics</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Analysez facilement vos conversations de groupe</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📂 Charger un fichier")
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "Importez votre export WhatsApp",
        type=['txt', 'zip'],
        help="Formats acceptés: .txt ou .zip"
    )
    
    if uploaded_file:
        st.success(f"✅ Fichier chargé: **{uploaded_file.name}**")

# Corps principal
if uploaded_file:
    with st.spinner('🔄 Analyse en cours...'):
        file_content = load_file(uploaded_file)
        
        if file_content:
            df = parse_whatsapp_file(file_content)
            
            if not df.empty:
                st.success(f"✅ {len(df)} messages analysés avec succès!")
                
                # Statistiques globales
                st.markdown("### 📈 Vue d'ensemble")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-value">{len(df)}</div>
                        <div class="stat-label">Messages</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-value">{df['sender'].nunique()}</div>
                        <div class="stat-label">Participants</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    date_range = (df['date'].max() - df['date'].min()).days
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-value">{date_range}</div>
                        <div class="stat-label">Jours</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    avg_per_day = len(df) / max(date_range, 1)
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-value">{avg_per_day:.1f}</div>
                        <div class="stat-label">Msg/Jour</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Filtres
                with st.sidebar:
                    st.markdown("### 🎯 Filtres")
                    st.markdown("---")
                    
                    # Option pour exclure les numéros inconnus
                    exclude_unknown = st.checkbox(
                        "📱 Contacts uniquement",
                        value=False,
                        help="Exclure les numéros non enregistrés (+237...)"
                    )
                    
                    all_senders = sorted(df['sender'].unique())
                    
                    # Filtrer les numéros si demandé
                    if exclude_unknown:
                        all_senders = [s for s in all_senders if not is_phone_number(s)]
                    
                    selected_senders = st.multiselect(
                        "👥 Participants",
                        options=all_senders,
                        default=all_senders,
                        help="Sélectionnez les participants à analyser"
                    )
                    
                    st.markdown("#### 📅 Période")
                    min_date = df['date'].min()
                    max_date = df['date'].max()
                    
                    col_date1, col_date2 = st.columns(2)
                    with col_date1:
                        start_date = st.date_input(
                            "Du",
                            value=min_date,
                            min_value=min_date,
                            max_value=max_date
                        )
                    with col_date2:
                        end_date = st.date_input(
                            "Au",
                            value=max_date,
                            min_value=min_date,
                            max_value=max_date
                        )
                
                # Filtrer les données
                mask = (
                    (df['sender'].isin(selected_senders)) &
                    (df['date'] >= start_date) &
                    (df['date'] <= end_date)
                )
                filtered_df = df[mask]
                
                if not filtered_df.empty:
                    # Compter les messages par participant
                    message_counts = filtered_df['sender'].value_counts().reset_index()
                    message_counts.columns = ['Participant', 'Messages']
                    message_counts = message_counts.sort_values('Messages', ascending=True)
                    
                    # Graphique principal
                    st.markdown("### 🏆 Classement des interventions")
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=message_counts['Messages'],
                        y=message_counts['Participant'],
                        orientation='h',
                        marker=dict(
                            color=message_counts['Messages'],
                            colorscale='Purples',
                            line=dict(color='rgba(102, 126, 234, 0.3)', width=1),
                            colorbar=dict(
                                title=dict(
                                    text="Messages",
                                    font=dict(family='Inter', size=12, color='#4a5568')
                                ),
                                tickfont=dict(family='Inter', color='#718096')
                            )
                        ),
                        text=message_counts['Messages'],
                        textposition='outside',
                        textfont=dict(
                            family='Inter',
                            size=12,
                            color='#4a5568'
                        ),
                        hovertemplate='<b>%{y}</b><br>Messages: %{x}<extra></extra>'
                    ))
                    
                    fig.update_layout(
                        title=dict(
                            text=f'Top {len(message_counts)} Participants',
                            font=dict(family='Poppins', size=20, color='#2d3748'),
                            x=0.5,
                            xanchor='center'
                        ),
                        xaxis=dict(
                            title=dict(
                                text='Nombre de messages',
                                font=dict(family='Inter', size=14, color='#718096')
                            ),
                            tickfont=dict(family='Inter', color='#718096'),
                            gridcolor='rgba(0, 0, 0, 0.05)',
                            showgrid=True
                        ),
                        yaxis=dict(
                            title='',
                            tickfont=dict(family='Inter', size=12, color='#4a5568')
                        ),
                        plot_bgcolor='white',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=max(450, len(message_counts) * 35),
                        hoverlabel=dict(
                            bgcolor='white',
                            font=dict(family='Inter', size=13, color='#2d3748'),
                            bordercolor='#e2e8f0'
                        ),
                        margin=dict(l=20, r=80, t=60, b=50),
                        bargap=0.3
                    )
                    
                    st.plotly_chart(fig, use_container_width=True, key="main_chart")
                    
                    # Tableau détaillé
                    st.markdown("### 📋 Détails par participant")
                    
                    detailed_stats = []
                    for sender in message_counts['Participant']:
                        sender_df = filtered_df[filtered_df['sender'] == sender]
                        total_chars = sender_df['message'].str.len().sum()
                        avg_length = sender_df['message'].str.len().mean()
                        
                        detailed_stats.append({
                            'Participant': sender,
                            'Messages': len(sender_df),
                            'Caractères totaux': int(total_chars),
                            'Longueur moyenne': round(avg_length, 1),
                            'Pourcentage': round(len(sender_df)/len(filtered_df)*100, 1)
                        })
                    
                    stats_df = pd.DataFrame(detailed_stats)
                    stats_df = stats_df.sort_values('Messages', ascending=False)
                    stats_df.insert(0, 'Rang', range(1, len(stats_df) + 1))
                    
                    st.dataframe(
                        stats_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Rang": st.column_config.NumberColumn("🏅 Rang", width="small"),
                            "Participant": st.column_config.TextColumn("👤 Participant"),
                            "Messages": st.column_config.NumberColumn("💬 Messages", format="%d"),
                            "Caractères totaux": st.column_config.NumberColumn("📝 Caractères", format="%d"),
                            "Longueur moyenne": st.column_config.NumberColumn("📏 Moy. caractères", format="%.1f"),
                            "Pourcentage": st.column_config.NumberColumn("📊 Part (%)", format="%.1f%%")
                        }
                    )
                    
                    # Graphique temporel
                    st.markdown("### 📅 Activité dans le temps")
                    
                    daily_counts = filtered_df.groupby('date').size().reset_index(name='Messages')
                    
                    fig_timeline = go.Figure()
                    
                    fig_timeline.add_trace(go.Scatter(
                        x=daily_counts['date'],
                        y=daily_counts['Messages'],
                        mode='lines+markers',
                        line=dict(color='#667eea', width=3, shape='spline'),
                        marker=dict(
                            size=8,
                            color='#764ba2',
                            line=dict(color='white', width=2)
                        ),
                        fill='tozeroy',
                        fillcolor='rgba(102, 126, 234, 0.1)',
                        hovertemplate='<b>%{x}</b><br>Messages: %{y}<extra></extra>'
                    ))
                    
                    fig_timeline.update_layout(
                        title=dict(
                            text='Évolution quotidienne de l\'activité',
                            font=dict(family='Poppins', size=18, color='#2d3748'),
                            x=0.5,
                            xanchor='center'
                        ),
                        xaxis=dict(
                            title=dict(
                                text='Date',
                                font=dict(family='Inter', size=14, color='#718096')
                            ),
                            tickfont=dict(family='Inter', color='#718096'),
                            gridcolor='rgba(0, 0, 0, 0.05)'
                        ),
                        yaxis=dict(
                            title=dict(
                                text='Messages',
                                font=dict(family='Inter', size=14, color='#718096')
                            ),
                            tickfont=dict(family='Inter', color='#718096'),
                            gridcolor='rgba(0, 0, 0, 0.05)'
                        ),
                        plot_bgcolor='white',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=400,
                        hoverlabel=dict(
                            bgcolor='white',
                            font=dict(family='Inter', size=13, color='#2d3748'),
                            bordercolor='#e2e8f0'
                        ),
                        margin=dict(l=20, r=20, t=60, b=50)
                    )
                    
                    st.plotly_chart(fig_timeline, use_container_width=True, key="timeline_chart")
                    
                    # Export des données
                    st.markdown("### 💾 Exporter les résultats")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Export Excel
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                            stats_df.to_excel(writer, sheet_name='Classement', index=False)
                            daily_counts.to_excel(writer, sheet_name='Activité journalière', index=False)
                        excel_data = excel_buffer.getvalue()
                        
                        st.download_button(
                            label="📥 Excel (.xlsx)",
                            data=excel_data,
                            file_name=f"whatsapp_analytics_{start_date}_{end_date}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    with col2:
                        csv = stats_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 CSV",
                            data=csv,
                            file_name=f"whatsapp_analytics_{start_date}_{end_date}.csv",
                            mime="text/csv"
                        )
                    
                    with col3:
                        json_data = stats_df.to_json(orient='records', indent=2)
                        st.download_button(
                            label="📥 JSON",
                            data=json_data,
                            file_name=f"whatsapp_analytics_{start_date}_{end_date}.json",
                            mime="application/json"
                        )
                    
                else:
                    st.warning("⚠️ Aucun message ne correspond aux filtres sélectionnés.")
            else:
                st.error("❌ Impossible de parser le fichier. Vérifiez le format.")
        else:
            st.error("❌ Impossible de lire le contenu du fichier.")
else:
    # Page d'accueil
    st.markdown("""
    <div style='text-align: center; padding: 2rem;'>
        <div style='font-size: 4rem; margin-bottom: 1.5rem;'>📊</div>
        <h2 style='font-family: Poppins; color: #2d3748; font-weight: 600;'>Bienvenue!</h2>
        <p style='font-family: Inter; font-size: 1.1rem; color: #718096; margin: 1.5rem 0; max-width: 600px; margin-left: auto; margin-right: auto;'>
            Analysez vos conversations WhatsApp pour suivre les interventions de vos contacts dans vos groupes.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📤</div>
            <div class="feature-title">Import facile</div>
            <div class="feature-desc">Chargez vos fichiers .txt ou .zip</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">👥</div>
            <div class="feature-title">Filtres flexibles</div>
            <div class="feature-desc">Sélectionnez participants et période</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Visualisations</div>
            <div class="feature-desc">Graphiques interactifs</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💾</div>
            <div class="feature-title">Export Excel</div>
            <div class="feature-desc">Téléchargez vos résultats</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Instructions
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="instructions-box">
        <h3 style='font-family: Poppins; color: #2d3748; margin-bottom: 16px;'>🚀 Comment commencer ?</h3>
        <ol style='font-family: Inter; color: #4a5568; line-height: 2; padding-left: 20px;'>
            <li>Exportez votre conversation WhatsApp (Menu > Plus > Exporter)</li>
            <li>Cliquez sur <strong>Parcourir</strong> dans la barre latérale</li>
            <li>Sélectionnez votre fichier .txt ou .zip</li>
            <li>Explorez les statistiques et graphiques</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 1rem; font-family: Inter; color: #a0aec0;'>
    <p style='font-size: 0.9rem;'>WhatsApp Analytics © 2026</p>
</div>
""", unsafe_allow_html=True)
