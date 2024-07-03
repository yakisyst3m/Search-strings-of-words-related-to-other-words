import os
import re
from email import policy
from email.parser import BytesParser
from unidecode import unidecode
from tqdm import tqdm

def read_word_list(file_path):
    print(f"Reading word list from {file_path}")
    word_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    a_part, b_part = line.split('|')
                    a_words = [unidecode(word.strip()).lower() for word in a_part.replace('A=', '').split(',')]
                    b_words = [unidecode(word.strip()).lower() for word in b_part.replace('B=', '').split(',')]
                    word_list.append({'A': a_words, 'B': b_words})
    except Exception as e:
        print(f"Error reading word list: {e}")
    return word_list

def extract_text_from_email(file_path):
    print(f"Extracting text from email: {file_path}")
    with open(file_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
        content = []
        for part in msg.walk():
            if part.get_content_type() in ['text/plain', 'text/html']:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset('utf-8')
                    content.append(payload.decode(charset, errors='replace'))
        return ' '.join(content)

def search_in_eml(file_path, word_dict):
    results = []
    content = extract_text_from_email(file_path).lower()
    content_normalized = unidecode(content)

    for word_group in word_dict:
        found_a = []
        found_b = []

        # Collectez tous les mots de la liste A trouvés dans le contenu
        for word_a in word_group['A']:
            if word_a in content_normalized:
                found_a.append(word_a)
        
        # Collectez tous les mots de la liste B trouvés dans le contenu
        for word_b in word_group['B']:
            if word_b in content_normalized:
                found_b.append(word_b)
        
        # Ajoutez aux résultats uniquement si nous avons trouvé au moins un mot de A et un de B
        if found_a and found_b:
            results.append((found_a, found_b, file_path))
    
    return results

def generate_report(results, report_file_path):
    print(f"Generating report: {report_file_path}")
    with open(report_file_path, 'w', encoding='utf-8') as report_file:
        if results:
            for result in results:
                words_a, words_b, file_path = result
                report_file.write(f"Recherche : A={words_a} | B={words_b} | Chemin du fichier : {file_path}\n")
        else:
            report_file.write("Aucune correspondance trouvée !!\n")

def search_strings_in_eml(file_path, word_dict):
    results = set()  # Utilisation d'un ensemble pour éviter les doublons
    print(f"Searching strings in email: {file_path}")
    with open(file_path, 'rb') as f:
        content = f.read().decode('utf-8', errors='ignore')  # Lire le contenu brut du fichier .eml
        for word_group in word_dict:
            for word_a in word_group['A']:
                if word_a.lower() in content.lower():  # Recherche sans tenir compte de la casse
                    results.add((word_a, file_path))  # Ajout au set
            for word_b in word_group['B']:
                if word_b.lower() in content.lower():  # Recherche sans tenir compte de la casse
                    results.add((word_b, file_path))  # Ajout au set
    return results

def generate_strings_report(results, report_file_path):
    print(f"Generating strings report: {report_file_path}")
    # Filtrer les résultats pour ne garder que les lignes où un mot a été trouvé
    filtered_results = [result for result in results if result[0]]
    # Ajouter le nom de fichier à chaque résultat
    enriched_results = [(word_found, file_path, os.path.basename(file_path)) for word_found, file_path in filtered_results]
    # Trier les résultats par "word_found" et "file_name"
    sorted_results = sorted(enriched_results, key=lambda x: (x[0], x[2]))
    
    with open(report_file_path, 'w', encoding='utf-8') as report_file:
        for result in sorted_results:
            word_found, file_path, file_name = result
            report_file.write(f"word found: {word_found} | Chemin du fichier: {file_path} | fileName: {file_name}\n")

def main():
    start_path = '.'  # Définissez votre emplacement de départ ici
    word_list_path = 'word_list.txt'  # Chemin vers votre fichier .txt
    report_file_path = 'rapport_matching_combinaisons.txt'  # Chemin vers le fichier de rapport
    strings_report_file_path = 'rapport_strings_worlds.txt'  # Chemin vers le deuxième fichier de rapport

    word_list = read_word_list(word_list_path)
    all_results = []

    # Obtenez la liste de tous les fichiers .eml
    eml_files = []
    for dirpath, dirnames, filenames in os.walk(start_path):
        for file in filenames:
            if file.endswith('.eml'):
                eml_files.append(os.path.join(dirpath, file))

    # Traitez chaque fichier .eml avec une barre de progression
    for file_path in tqdm(eml_files, desc="Processing .eml files"):
        search_results = search_in_eml(file_path, word_list)
        if search_results:
            all_results.extend(search_results)

    # Générez le rapport
    generate_report(all_results, report_file_path)
    print(f"Le rapport a été généré : {report_file_path}")

    # Generate strings report
    strings_results = []
    for file_path in tqdm(eml_files, desc="Processing .eml files for strings report"):
        strings_results.extend(search_strings_in_eml(file_path, word_list))
    
    generate_strings_report(strings_results, strings_report_file_path)
    print(f"Le rapport des mots trouvés a été généré : {strings_report_file_path}")

if __name__ == '__main__':
    main()

