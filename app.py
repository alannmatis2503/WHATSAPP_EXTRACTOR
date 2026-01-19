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
    phone_pattern = r'^\+?\d[\d\s\-\.]{6,}$'
    return bool(re.match(phone_pattern, name.strip()))

def extract_group_name(filename):
    """Extrait le nom du groupe à partir du nom de fichier"""
    # Enlever l'extension
    name = filename.replace('.zip', '').replace('.txt', '')
    # Enlever le préfixe "Discussion WhatsApp avec "
    name = re.sub(r'^Discussion WhatsApp avec\s*', '', name)
    # Enlever les suffixes comme " (1)", " (2)"
    name = re.sub(r'\s*\(\d+\)\s*$', '', name)
    return name.strip()

def parse_whatsapp_file(file_content, group_name):
    """Parse le contenu d'un fichier WhatsApp et extrait les messages"""
    lines = file_content.split('\n')
    messages = []
    
    pattern = r'(\d{1,2}/\d{1,2}/\d{4}),\s*(\d{1,2}:\d{2})\s*-\s*([^:]+):\s*(.*)'
    
    current_message = None
    
    for line in lines:
        match = re.match(pattern, line)
        if match:
            if current_message:
                messages.append(current_message)
            
            date_str, time_str, sender, content = match.groups()
            
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
                    'message': content.strip(),
                    'groupe': group_name
                }
            except:
                current_message = None
        elif current_message and line.strip():
            current_message['message'] += ' ' + line.strip()
    
    if current_message:
        messages.append(current_message)
    
    return pd.DataFrame(messages)

def load_file(uploaded_file):
    """Charge un fichier txt ou zip et retourne le contenu et le nom du groupe"""
    group_name = extract_group_name(uploaded_file.name)
    
    if uploaded_file.name.endswith('.zip'):
        with zipfile.ZipFile(io.BytesIO(uploaded_file.read())) as z:
            txt_files = [f for f in z.namelist() if f.endswith('.txt')]
            if txt_files:
                with z.open(txt_files[0]) as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    return content, group_name
    else:
        return uploaded_file.read().decode('utf-8', errors='ignore'), group_name
    
    return None, group_name

# Configuration de la page
st.set_page_config(
    page_title="WhatsApp Analytics",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 50%, #d9e2ec 100%);
    }
    
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
    
    section[data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e2e8f0;
    }
    
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
    
    .feature-icon { font-size: 2.5rem; margin-bottom: 16px; }
    .feature-title { font-family: 'Poppins', sans-serif; font-size: 1.1rem; font-weight: 600; color: #2d3748; margin-bottom: 8px; }
    .feature-desc { font-family: 'Inter', sans-serif; font-size: 0.9rem; color: #718096; }
    
    .instructions-box {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-title">💬 WhatsApp Analytics</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Analysez facilement vos conversations de groupe</p>', unsafe_allow_html=True)

# Sidebar - Upload multiple files
with st.sidebar:
    st.markdown("### 📂 Charger des fichiers")
    st.markdown("---")
    
    uploaded_files = st.file_uploader(
        "Importez vos exports WhatsApp",
        type=['txt', 'zip'],
        accept_multiple_files=True,
        help="Formats acceptés: .txt ou .zip (plusieurs fichiers possibles)"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} fichier(s) chargé(s)")
        for f in uploaded_files:
            st.info(f"📄 {f.name}")

# Corps principal
if uploaded_files:
    with st.spinner('🔄 Analyse en cours...'):
        # Charger et combiner tous les fichiers
        all_dfs = []
        group_names = []
        
        for uploaded_file in uploaded_files:
            file_content, group_name = load_file(uploaded_file)
            if file_content:
                df_single = parse_whatsapp_file(file_content, group_name)
                if not df_single.empty:
                    all_dfs.append(df_single)
                    if group_name not in group_names:
                        group_names.append(group_name)
        
        if all_dfs:
            # Combiner tous les DataFrames
            df = pd.concat(all_dfs, ignore_index=True)
            
            st.success(f"✅ {len(df)} messages analysés depuis {len(group_names)} groupe(s)!")
            
            # Statistiques globales
            st.markdown("### 📈 Vue d'ensemble")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
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
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{len(group_names)}</div>
                    <div class="stat-label">Groupes</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                date_range = (df['date'].max() - df['date'].min()).days
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{date_range}</div>
                    <div class="stat-label">Jours</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col5:
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
                
                # Filtre par groupe (si plusieurs groupes)
                if len(group_names) > 1:
                    selected_groups = st.multiselect(
                        "📁 Groupes WhatsApp",
                        options=sorted(group_names),
                        default=sorted(group_names),
                        help="Sélectionnez les groupes à analyser"
                    )
                else:
                    selected_groups = group_names
                
                # Option pour exclure les numéros inconnus
                exclude_unknown = st.checkbox(
                    "📱 Contacts uniquement",
                    value=False,
                    help="Exclure les numéros non enregistrés (+237...)"
                )
                
                # Filtrer d'abord par groupe pour obtenir la liste des participants
                df_by_group = df[df['groupe'].isin(selected_groups)]
                all_senders = sorted(df_by_group['sender'].unique())
                
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
                (df['groupe'].isin(selected_groups)) &
                (df['sender'].isin(selected_senders)) &
                (df['date'] >= start_date) &
                (df['date'] <= end_date)
            )
            filtered_df = df[mask]
            
            if not filtered_df.empty:
                multiple_groups = len(selected_groups) > 1
                
                # Compter les messages par participant (total)
                message_counts = filtered_df['sender'].value_counts().reset_index()
                message_counts.columns = ['Participant', 'Messages']
                message_counts = message_counts.sort_values('Messages', ascending=True)
                
                # === GRAPHIQUE PRINCIPAL ===
                st.markdown("### 🏆 Classement des interventions")
                
                if multiple_groups:
                    # Graphique empilé par groupe
                    group_participant_counts = filtered_df.groupby(['sender', 'groupe']).size().reset_index(name='Messages')
                    
                    fig = px.bar(
                        group_participant_counts,
                        x='Messages',
                        y='sender',
                        color='groupe',
                        orientation='h',
                        title=f'Top {len(message_counts)} Participants (ventilé par groupe)',
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    
                    # Trier par total de messages
                    order = message_counts['Participant'].tolist()
                    fig.update_yaxes(categoryorder='array', categoryarray=order)
                    
                    fig.update_layout(
                        title=dict(font=dict(family='Poppins', size=20, color='#2d3748'), x=0.5),
                        xaxis=dict(title=dict(text='Nombre de messages', font=dict(family='Inter', size=14, color='#718096'))),
                        yaxis=dict(title=dict(text=''), tickfont=dict(family='Inter', size=11, color='#4a5568')),
                        legend=dict(title='Groupe', font=dict(family='Inter')),
                        plot_bgcolor='white',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=max(500, len(message_counts) * 35),
                        bargap=0.3
                    )
                else:
                    # Graphique simple
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=message_counts['Messages'],
                        y=message_counts['Participant'],
                        orientation='h',
                        marker=dict(
                            color=message_counts['Messages'],
                            colorscale='Purples',
                            line=dict(color='rgba(102, 126, 234, 0.3)', width=1)
                        ),
                        text=message_counts['Messages'],
                        textposition='outside',
                        textfont=dict(family='Inter', size=12, color='#4a5568'),
                        hovertemplate='<b>%{y}</b><br>Messages: %{x}<extra></extra>'
                    ))
                    
                    fig.update_layout(
                        title=dict(text=f'Top {len(message_counts)} Participants', font=dict(family='Poppins', size=20, color='#2d3748'), x=0.5),
                        xaxis=dict(title=dict(text='Nombre de messages', font=dict(family='Inter', size=14, color='#718096'))),
                        yaxis=dict(title='', tickfont=dict(family='Inter', size=12, color='#4a5568')),
                        plot_bgcolor='white',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=max(450, len(message_counts) * 35),
                        margin=dict(l=20, r=80, t=60, b=50),
                        bargap=0.3
                    )
                
                st.plotly_chart(fig, use_container_width=True, key="main_chart")
                
                # === TABLEAU DÉTAILLÉ ===
                st.markdown("### 📋 Détails par participant")
                
                if multiple_groups:
                    # Tableau avec ventilation par groupe
                    detailed_stats = []
                    for sender in message_counts.sort_values('Messages', ascending=False)['Participant']:
                        sender_df = filtered_df[filtered_df['sender'] == sender]
                        total_chars = sender_df['message'].str.len().sum()
                        avg_length = sender_df['message'].str.len().mean()
                        
                        # Ventilation par groupe
                        group_breakdown = sender_df.groupby('groupe').size().to_dict()
                        
                        row = {
                            'Participant': sender,
                            'Total': len(sender_df),
                            'Caractères': int(total_chars),
                            'Moy. car.': round(avg_length, 1),
                            '%': round(len(sender_df)/len(filtered_df)*100, 1)
                        }
                        
                        # Ajouter une colonne par groupe
                        for grp in sorted(selected_groups):
                            row[grp] = group_breakdown.get(grp, 0)
                        
                        detailed_stats.append(row)
                    
                    stats_df = pd.DataFrame(detailed_stats)
                    stats_df.insert(0, 'Rang', range(1, len(stats_df) + 1))
                    
                    # Configuration des colonnes
                    col_config = {
                        "Rang": st.column_config.NumberColumn("🏅", width="small"),
                        "Participant": st.column_config.TextColumn("👤 Participant"),
                        "Total": st.column_config.NumberColumn("💬 Total", format="%d"),
                        "Caractères": st.column_config.NumberColumn("📝 Car.", format="%d"),
                        "Moy. car.": st.column_config.NumberColumn("📏 Moy.", format="%.1f"),
                        "%": st.column_config.NumberColumn("📊 %", format="%.1f%%")
                    }
                    
                    for grp in sorted(selected_groups):
                        col_config[grp] = st.column_config.NumberColumn(f"📁 {grp[:15]}...", format="%d") if len(grp) > 15 else st.column_config.NumberColumn(f"📁 {grp}", format="%d")
                    
                    st.dataframe(stats_df, use_container_width=True, hide_index=True, column_config=col_config)
                else:
                    # Tableau simple
                    detailed_stats = []
                    for sender in message_counts.sort_values('Messages', ascending=False)['Participant']:
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
                
                # === GRAPHIQUE TEMPOREL ===
                st.markdown("### 📅 Activité dans le temps")
                
                if multiple_groups:
                    # Graphique temporel par groupe
                    daily_by_group = filtered_df.groupby(['date', 'groupe']).size().reset_index(name='Messages')
                    
                    fig_timeline = px.line(
                        daily_by_group,
                        x='date',
                        y='Messages',
                        color='groupe',
                        title='Évolution quotidienne par groupe',
                        markers=True,
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    
                    fig_timeline.update_layout(
                        title=dict(font=dict(family='Poppins', size=18, color='#2d3748'), x=0.5),
                        xaxis=dict(title=dict(text='Date', font=dict(family='Inter', size=14, color='#718096'))),
                        yaxis=dict(title=dict(text='Messages', font=dict(family='Inter', size=14, color='#718096'))),
                        legend=dict(title='Groupe', font=dict(family='Inter')),
                        plot_bgcolor='white',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=400
                    )
                else:
                    daily_counts = filtered_df.groupby('date').size().reset_index(name='Messages')
                    
                    fig_timeline = go.Figure()
                    
                    fig_timeline.add_trace(go.Scatter(
                        x=daily_counts['date'],
                        y=daily_counts['Messages'],
                        mode='lines+markers',
                        line=dict(color='#667eea', width=3, shape='spline'),
                        marker=dict(size=8, color='#764ba2', line=dict(color='white', width=2)),
                        fill='tozeroy',
                        fillcolor='rgba(102, 126, 234, 0.1)',
                        hovertemplate='<b>%{x}</b><br>Messages: %{y}<extra></extra>'
                    ))
                    
                    fig_timeline.update_layout(
                        title=dict(text='Évolution quotidienne de l\'activité', font=dict(family='Poppins', size=18, color='#2d3748'), x=0.5),
                        xaxis=dict(title=dict(text='Date', font=dict(family='Inter', size=14, color='#718096'))),
                        yaxis=dict(title=dict(text='Messages', font=dict(family='Inter', size=14, color='#718096'))),
                        plot_bgcolor='white',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=400
                    )
                
                st.plotly_chart(fig_timeline, use_container_width=True, key="timeline_chart")
                
                # === GRAPHIQUE PAR GROUPE (si plusieurs groupes) ===
                if multiple_groups:
                    st.markdown("### 📊 Répartition par groupe")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        group_totals = filtered_df.groupby('groupe').size().reset_index(name='Messages')
                        
                        fig_pie = px.pie(
                            group_totals,
                            values='Messages',
                            names='groupe',
                            title='Distribution des messages par groupe',
                            color_discrete_sequence=px.colors.qualitative.Set2
                        )
                        fig_pie.update_layout(
                            title=dict(font=dict(family='Poppins', size=16, color='#2d3748'), x=0.5),
                            legend=dict(font=dict(family='Inter'))
                        )
                        st.plotly_chart(fig_pie, use_container_width=True, key="pie_chart")
                    
                    with col2:
                        fig_bar_groups = px.bar(
                            group_totals.sort_values('Messages', ascending=True),
                            x='Messages',
                            y='groupe',
                            orientation='h',
                            title='Messages par groupe',
                            color='Messages',
                            color_continuous_scale='Purples'
                        )
                        fig_bar_groups.update_layout(
                            title=dict(font=dict(family='Poppins', size=16, color='#2d3748'), x=0.5),
                            showlegend=False,
                            plot_bgcolor='white',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig_bar_groups, use_container_width=True, key="bar_groups")
                
                # === EXPORT ===
                st.markdown("### 💾 Exporter les résultats")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    excel_buffer = io.BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        stats_df.to_excel(writer, sheet_name='Classement', index=False)
                        
                        daily_counts_export = filtered_df.groupby('date').size().reset_index(name='Messages')
                        daily_counts_export.to_excel(writer, sheet_name='Activité journalière', index=False)
                        
                        if multiple_groups:
                            # Ventilation par groupe
                            group_summary = filtered_df.groupby('groupe').agg({
                                'sender': 'nunique',
                                'message': 'count'
                            }).reset_index()
                            group_summary.columns = ['Groupe', 'Participants', 'Messages']
                            group_summary.to_excel(writer, sheet_name='Par groupe', index=False)
                            
                            # Détail par groupe et participant
                            detail_by_group = filtered_df.groupby(['groupe', 'sender']).size().reset_index(name='Messages')
                            detail_by_group = detail_by_group.sort_values(['groupe', 'Messages'], ascending=[True, False])
                            detail_by_group.to_excel(writer, sheet_name='Détail par groupe', index=False)
                    
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
            st.error("❌ Impossible de parser les fichiers. Vérifiez le format.")
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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📤</div>
            <div class="feature-title">Multi-fichiers</div>
            <div class="feature-desc">Chargez plusieurs groupes</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">👥</div>
            <div class="feature-title">Filtres flexibles</div>
            <div class="feature-desc">Par groupe, participant, période</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Visualisations</div>
            <div class="feature-desc">Graphiques par groupe</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💾</div>
            <div class="feature-title">Export Excel</div>
            <div class="feature-desc">Données ventilées</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="instructions-box">
        <h3 style='font-family: Poppins; color: #2d3748; margin-bottom: 16px;'>🚀 Comment commencer ?</h3>
        <ol style='font-family: Inter; color: #4a5568; line-height: 2; padding-left: 20px;'>
            <li>Exportez vos conversations WhatsApp (Menu > Plus > Exporter)</li>
            <li>Chargez un ou plusieurs fichiers .txt ou .zip</li>
            <li>Filtrez par groupe, participants ou période</li>
            <li>Explorez les statistiques croisées</li>
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
