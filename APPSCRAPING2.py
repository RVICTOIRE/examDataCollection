import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import matplotlib.pyplot as plt
import webbrowser
# Fonction pour scraper une seule page avec BeautifulSoup
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
                
          




def page_telechargement_donnees():
    st.title("📥 Télécharger des données non nettoyées")
    
    try:
        # Chemin vers le répertoire contenant les données brutes
        data_directory = "raw_data/"
        if not os.path.exists(data_directory):
            os.makedirs(data_directory) # Modifiez ici avec le chemin réel
        
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

# Page dashboard
def page_dashboard():
    st.title("📊 Dashboard des données")
    
    # Chemin vers le répertoire contenant les fichiers nettoyés
    cleaned_data_path = "cleaned_data/"

    if not os.path.exists(cleaned_data_path):
        os.makedirs(cleaned_data_path)
    
    try:
        # Vérifier si le répertoire existe et lister les fichiers
        files = [f for f in os.listdir(cleaned_data_path) if f.endswith(('.csv', '.xlsx'))]
        if not files:
            st.warning("Aucun fichier nettoyé trouvé dans le répertoire 'cleaned_data'.")
            return
        
        # Afficher une liste déroulante pour choisir un fichier
        selected_file = st.selectbox("🔍 Sélectionnez un fichier nettoyé :", files)
        
        # Construire le chemin complet du fichier sélectionné
        file_path = os.path.join(cleaned_data_path, selected_file)
        
        # Charger le fichier sélectionné
        if file_path.endswith('.csv'):
            data = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            data = pd.read_excel(file_path)
        
        # Nettoyer les noms de colonnes
        data.columns = data.columns.str.strip().str.lower()
        
        # Afficher un aperçu des données
        st.write(f"🔍 Aperçu des données du fichier : {selected_file}", data.head())
        
        # Graphique des prix sous forme d'histogramme
        st.subheader("💰 Distribution des prix par intervalles de 5000")
        if "prix" in data.columns:
            # Nettoyage et conversion de la colonne 'Prix'
            data["prix"] = pd.to_numeric(data["prix"], errors="coerce")
            prices = data["prix"].dropna()
            
            if not prices.empty:
                # Définir les tranches de prix
                min_price = int(prices.min() // 5000) * 5000
                max_price = int(prices.max() // 5000) * 5000 + 5000
                bins = range(min_price, max_price + 5000, 5000)
                
                # Catégorisation des prix
                data["tranche_prix"] = pd.cut(data["prix"], bins=bins, right=False)
                
                # Comptage des articles par tranche de prix
                price_counts = data["tranche_prix"].value_counts().sort_index()
                
                # Création du graphique
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(price_counts.index.astype(str), price_counts.values, color='skyblue', edgecolor="black")
                
                # Ajout de labels et titre
                ax.set_xlabel("Tranche de prix (CFA)", fontsize=12)
                ax.set_ylabel("Nombre d'articles", fontsize=12)
                ax.set_title("Distribution des prix par intervalles de 5000", fontsize=14)
                
                # Rotation des étiquettes pour une meilleure lisibilité
                ax.tick_params(axis='x', rotation=45, labelsize=10)
                ax.tick_params(axis='y', labelsize=10)
                
                # Affichage du graphique dans Streamlit
                st.pyplot(fig)
            else:
                st.warning("Aucune donnée valide trouvée dans la colonne 'Prix'.")
        else:
            st.warning("La colonne 'Prix' n'a pas été trouvée dans les données.")
    
    except Exception as e:
        st.error(f"❌ Une erreur s'est produite : {e}")




def page_evaluation():
    st.title("⭐ Évaluation de l'application")
    
    # Lien vers le formulaire Kobotoolbox
    kobo_form_url = "https://ee.kobotoolbox.org/x/3ZAgNPD9"  # Remplacez par votre lien Kobotoolbox
    
    with st.form("form_eval"):
        name = st.text_input("👤 Nom")
        
        submitted = st.form_submit_button("✅ Soumettre")
        
        if submitted:
            if name.strip() == "":
                st.warning("Veuillez entrer votre nom avant de soumettre.")
            else:
                # Option 1 : Afficher un lien hypertexte
                st.success("🎉 Merci d'avoir utilisé notre application ! Veuillez cliquer sur le lien ci-dessous pour remplir le formulaire détaillé.")
                st.markdown(f"[Cliquez ici pour accéder au formulaire]({https://ee.kobotoolbox.org/x/3ZAgNPD9})")
                
                # Option 2 : Redirection automatique avec JavaScript
                st.components.v1.html(
                    f"""
                    <script>
                        window.open("{https://ee.kobotoolbox.org/x/3ZAgNPD9}", "_blank").focus();
                    </script>
                    """,
                    height=0
                )
# Menu principal Streamlit
menu = st.sidebar.radio("📌 Menu", ["Scraper", "Téléchargement Données Brutes", "Dashboard", "Évaluation"])
if menu == "Scraper":
    main()
elif menu == "Téléchargement Données Brutes":
    page_telechargement_donnees()

elif menu == "Dashboard":
    page_dashboard()
elif menu == "Évaluation":
    page_evaluation()