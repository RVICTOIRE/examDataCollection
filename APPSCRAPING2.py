import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import matplotlib.pyplot as plt
import webbrowser
import numpy as np
# Fonction pour scraper une seule page
def scrape_page(url):
    try:
        # Récupérer le contenu HTML de la page
        response = requests.get(url)
        response.raise_for_status()  # Vérifier si la requête a réussi
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trouver tous les conteneurs correspondants
        containers = soup.select("div.card.ad__card")
        data = []
        
        for container in containers:
            try:
                # Extraire les informations souhaitées
                type_ = container.select_one('.ad__card-description').text.strip()
                prix = container.select_one('.ad__card-price').text.replace('CFA', '').strip()
                adresse = container.select_one('.ad__card-location').text.strip().replace('location_on','')
                image_link = container.find('img')['src']
                
                # Ajouter les données au tableau
                data.append({
                    'Type': type_,
                    'Prix': prix,
                    'Adresse': adresse,
                    'Image': image_link
                })
            except AttributeError:
                continue  # Ignorer les erreurs liées aux éléments manquants
        
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Une erreur s'est produite lors du scraping : {e}")
        return pd.DataFrame()

# Fonction pour scraper plusieurs pages
def scrape_multiple_pages(base_url, num_pages):
    all_data = pd.DataFrame()
    progress_bar = st.progress(0)
    for page in range(1, num_pages + 1):
        url = f"{base_url}?page={page}"
        st.write(f"Scraping de la page {page}...")
        page_data = scrape_page(url)
        all_data = pd.concat([all_data, page_data], ignore_index=True)
        progress_bar.progress(page / num_pages)  # Mettre à jour la barre de progression
    return all_data

# Fonction principale pour le scraping
def main():
    st.title("🛍️ Scraper avec BeautifulSoup")
    
    # Ajout d'une clé unique pour l'URL de base
    base_url = st.text_input("🔗 URL de base", "https://sn.coinafrique.com/categorie/vetements-homme", key="scraper_base_url")
    
    # Ajout d'une clé unique pour le nombre de pages
    num_pages = st.number_input("📄 Nombre de pages à scraper", min_value=1, max_value=120, value=10, key="scraper_num_pages")
    
    if st.button("🚀 Lancer le scraping", key="scraper_button"):
        with st.spinner("⏳ Scraping en cours..."):
            scraped_data = scrape_multiple_pages(base_url, num_pages)
            
            if scraped_data.empty:
                st.warning("Aucune donnée n'a été trouvée.")
            else:
                st.success("✅ Scraping terminé avec succès !")
                
                # Affichage des données sous forme de tableau
                st.dataframe(scraped_data)

                # Option de téléchargement des données
                csv_data = scraped_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Télécharger les données en CSV",
                    data=csv_data,
                    file_name="data_scrapees.csv",
                    mime="text/csv",
                    key="scraper_download_button"
                )
                # Affichage des images des produits
                st.subheader("🖼️ Aperçu des produits")
                for index, row in scraped_data.iterrows():
                    st.image(row["Image"], caption=f"{row['Type']} - {row['Prix']} CFA", width=150)
                
          



# page de téléchargement des données
def page_telechargement_donnees():
    st.title("📥 Télécharger des données non nettoyées")
    
    try:
        
        data_directory = "raw_data/"
        if not os.path.exists(data_directory):
            os.makedirs(data_directory) 
        
        # Vérifier si le répertoire existe
        if not os.path.exists(data_directory):
            st.error(f"Le répertoire '{data_directory}' n'existe pas.")
            return
        
        # Lister tous les fichiers valides dans le répertoire
        files = [f for f in os.listdir(data_directory) if f.endswith(('.csv', '.json', '.xlsx'))]
        if not files:
            st.warning("Aucun fichier trouvé dans le répertoire des données non nettoyées.")
            return
        
        # Afficher une liste déroulante pour choisir un fichier
        selected_file = st.selectbox("🔍 Sélectionnez un fichier :", files)
        
        # Construire le chemin complet du fichier sélectionné
        file_path = os.path.join(data_directory, selected_file)
        
        # Détection du type de fichier et lecture des données
        if file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            data = pd.read_json(file_path)
        elif file_path.endswith('.xlsx'):
            data = pd.read_excel(file_path)  # Lecture du fichier Excel
        else:
            st.error("Le format du fichier n'est pas pris en charge (seuls CSV, JSON et XLSX sont acceptés).")
            return
        
        # Affichage d'un aperçu des données
        st.write(f"🔍 Aperçu des données du fichier : {selected_file}", data.head())
        
        # Option de téléchargement des données en différents formats
        csv_data = data.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Télécharger les données en CSV",
            data=csv_data,
            file_name=f"{selected_file.split('.')[0]}.csv",  # Garder le nom d'origine
            mime="text/csv"
        )
        
        json_data = data.to_json(orient='records').encode('utf-8')
        st.download_button(
            "📥 Télécharger les données en JSON",
            data=json_data,
            file_name=f"{selected_file.split('.')[0]}.json",  # Garder le nom d'origine
            mime="application/json"
        )
        
        # Ajout du téléchargement en format Excel (XLSX) avec openpyxl
        excel_file_path = f"{selected_file.split('.')[0]}_export.xlsx"
        data.to_excel(excel_file_path, index=False, engine="openpyxl", sheet_name="Données")
        with open(excel_file_path, "rb") as f:
            excel_data = f.read()
        st.download_button(
            "📥 Télécharger les données en XLSX",
            data=excel_data,
            file_name=f"{selected_file.split('.')[0]}.xlsx",  # Garder le nom d'origine
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    except Exception as e:
        st.error(f"Une erreur s'est produite lors du chargement des données : {e}")


def page_dashboard():
    st.title("📊 Dashboard des données")
    
    # Chemin vers le répertoire contenant les fichiers nettoyés
    cleaned_data_path = "cleaned_data/"

    if not os.path.exists(cleaned_data_path):
        os.makedirs(cleaned_data_path)
    
    try:
        # Lister les fichiers
        files = [f for f in os.listdir(cleaned_data_path) if f.endswith(('.csv', '.xlsx'))]
        if not files:
            st.warning("Aucun fichier nettoyé trouvé dans 'cleaned_data'.")
            return
        
        # Sélection du fichier
        selected_file = st.selectbox("🔍 Sélectionnez un fichier nettoyé :", files)
        file_path = os.path.join(cleaned_data_path, selected_file)

        # Chargement des données
        data = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_excel(file_path)
        data.columns = data.columns.str.strip().str.lower()
        
        st.write(f"🔍 Aperçu des données du fichier : {selected_file}", data.head())
        
        # Vérifier la présence de la colonne 'prix'
        if "prix" in data.columns:
            data["prix"] = pd.to_numeric(data["prix"], errors="coerce")
            prices = data["prix"].dropna()

            if not prices.empty:
                # Échantillonnage pour accélérer le rendu
                prices = prices.sample(min(5000, len(prices)), random_state=42)

                # Définition de catégories de prix (tranches de 10 000)
                bins = range(int(prices.min()), int(prices.max()) + 10_000, 10_000)
                price_bins = pd.cut(prices, bins=bins)  # Catégorisation des prix
                price_counts = price_bins.value_counts().sort_index()

                # ✅ Convertir les intervalles en chaînes pour éviter l'erreur
                price_counts.index = [f"{int(i.left)}-{int(i.right)}" for i in price_counts.index]

                # Affichage optimisé du graphique
                st.bar_chart(price_counts)


            else:
                st.warning("Aucune donnée valide trouvée dans la colonne 'Prix'.")
        else:
            st.warning("La colonne 'Prix' n'a pas été trouvée dans les données.")

    except Exception as e:
        st.error(f"❌ Erreur : {e}")






#page d'évaluation
def page_evaluation():
    st.title("⭐ Évaluation de l'application")
    
    # Lien vers le formulaire Kobotoolbox
    kobo_form_url = "https://ee.kobotoolbox.org/x/3ZAgNPD9"  
    
    with st.form("form_eval"):
        name = st.text_input("👤 Nom")
        
        submitted = st.form_submit_button("✅ Soumettre")
        
        if submitted:
            if name.strip() == "":
                st.warning("Veuillez entrer votre nom avant de soumettre.")
            else:
                # Option 1 : Afficher un lien hypertexte
                st.success("🎉 Merci d'avoir utilisé notre application ! Veuillez cliquer sur le lien ci-dessous pour remplir le formulaire détaillé.")
                st.markdown("[Cliquez ici pour accéder au formulaire](https://ee.kobotoolbox.org/x/3ZAgNPD9)")
                
                # Option 2 : Redirection automatique avec JavaScript
                st.components.v1.html(
                    """
                    <script>
                        window.open("https://ee.kobotoolbox.org/x/3ZAgNPD9", "_blank").focus();
                    </script>
                    """,
                    height=0
                )

#

# Menu principal Streamlit
menu = st.sidebar.radio("📌 Menu", ["Scraper", "Téléchargement Données Brutes", "Dashboard", "Évaluation"])
try:
    if menu == "Scraper":
        main()
    elif menu == "Téléchargement Données Brutes":
        page_telechargement_donnees()
    elif menu == "Dashboard":
        page_dashboard()
    elif menu == "Évaluation":
        page_evaluation()
except NameError as e:
    st.error(f"Erreur détectée: {e}")
