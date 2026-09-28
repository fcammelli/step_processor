 
import os
import re
import glob
from pathlib import Path

def clean_filename(text):
    """Pulisce una stringa per usarla come nome di file"""
    # Sostituisce caratteri non validi con trattini
    invalid_chars = r'[<>:"/\\|?*]'
    cleaned = re.sub(invalid_chars, '-', text)
    # Rimuove spazi multipli e trim
    cleaned = re.sub(r'\s+', ' ', cleaned.strip())
    # Sostituisce spazi con underscore
    cleaned = cleaned.replace(' ', '_')
    # Rimuove trattini multipli consecutivi
    cleaned = re.sub(r'-+', '-', cleaned)
    # Rimuove trattini all'inizio e alla fine
    cleaned = cleaned.strip('-').strip('_')
    return cleaned

def extract_step_description(step_content):
    """Estrae la descrizione dello step dal contenuto"""
    step_description = ""
    
    # Cerca la riga che contiene "Step description"
    lines = step_content.strip().split('\n')
    for line in lines:
        if 'Step description' in line:
            # Prova a estrarre il valore dopo "Step description"
            parts = re.split(r'Step description\s*[:|\t]\s*', line, flags=re.IGNORECASE)
            if len(parts) > 1:
                step_description = parts[1].strip()
                break
    
    return step_description

def extract_step_content(lines, step_idx, next_step_idx):
    """Estrae il contenuto di uno Step"""
    start_idx = step_idx
    
    # Se c'è un prossimo Step, termina prima di quello
    if next_step_idx is not None:
        end_idx = next_step_idx
    else:
        end_idx = len(lines)
    
    # Estrai il contenuto dell'intervallo
    step_content_lines = lines[start_idx:end_idx]
    step_content = ''.join(step_content_lines)
    
    return step_content

def main():
    # Intestazione del programma
    print("=" * 60)
    print("STEP PROCESSOR 1.2 - per tribometro PCS MTM-2")
    print("=" * 60)
    print("STEP PROCESSOR 1.2 © 2026 by Francesco Cammelli is licensed under")
    print("GNU 3 Public Licence")
    print("=" * 60)
    
    while True:
        # 1. Selezione file
        print("\n1. SELEZIONE FILE")
        print("-" * 40)
        
        # Trova tutti i file TXT nella cartella corrente
        data_files = sorted(glob.glob('*.txt')) + sorted(glob.glob('*.TXT'))
        
        if not data_files:
            print("Nessun file TXT trovato nella cartella corrente.")
            print("Assicurati che i file siano nella stessa cartella del programma.")
            return
        
        print("File disponibili nella cartella corrente:")
        for i, f in enumerate(data_files, 1):
            file_size = os.path.getsize(f)
            print(f"{i}. {f} ({file_size} bytes)")
        
        while True:
            choice = input("\nInserisci il numero del file da processare (o 'exit' per uscire): ").strip().lower()
            
            if choice == 'exit':
                print("Programma terminato.")
                return
            
            try:
                file_idx = int(choice) - 1
                if 0 <= file_idx < len(data_files):
                    file_path = data_files[file_idx]
                    print(f"\nFile selezionato: {file_path}")
                    break
                else:
                    print("Numero non valido! Riprova.")
            except ValueError:
                print("Input non valido! Inserisci un numero.")
        
        # 2. Lettura del file e individuazione degli Step (Stribeck o BodTimed)
        print("\n2. INDIVIDUAZIONE STEP (Stribeck o BodTimed)")
        print("-" * 40)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
            except:
                print("Errore nella lettura del file. Verifica l'encoding.")
                continue
        
        # Cerca Step che hanno "Stribeck" o "BodTimed" nella riga successiva
        valid_step_indices = []
        step_names = []          # es. "step007"
        step_types = []          # es. "Stribeck", "BodTimed"
        step_descriptions = []
        
        i = 0
        while i < len(lines) - 1:  # -1 perché dobbiamo controllare la riga successiva
            current_line = lines[i].strip()
            
            # Cerca "Step" nella riga corrente (case insensitive)
            step_match = re.search(r'Step\s*\d+', current_line, re.IGNORECASE)
            
            if step_match:
                # Controlla la riga successiva per "Stribeck" o "BodTimed" (case insensitive)
                next_line = lines[i + 1].strip()
                lower_next = next_line.lower()
                if 'stribeck' in lower_next or 'bodtimed' in lower_next:
                    valid_step_indices.append(i)
                    
                    # Estrai il numero dello step e formattalo a tre cifre
                    step_number_match = re.search(r'\d+', step_match.group())
                    if step_number_match:
                        step_num = step_number_match.group()
                        step_num_padded = step_num.zfill(3)  # trasforma '7' in '007'
                        step_name = f"step{step_num_padded}"
                    else:
                        # Fallback (non dovrebbe mai accadere)
                        step_name = step_match.group().replace(" ", "").lower()
                    
                    step_names.append(step_name)
                    
                    # Determina il tipo di step (usa la stringa esatta dalla riga per preservare maiuscole)
                    if 'stribeck' in lower_next:
                        # Cerca la parola 'Stribeck' nella riga (potrebbe essere "Stribeck" o "STRIBECK")
                        type_match = re.search(r'Stribeck', next_line, re.IGNORECASE)
                        step_type = type_match.group() if type_match else 'Stribeck'
                    elif 'bodtimed' in lower_next:
                        type_match = re.search(r'BodTimed', next_line, re.IGNORECASE)
                        step_type = type_match.group() if type_match else 'BodTimed'
                    else:
                        step_type = 'Unknown'
                    
                    step_types.append(step_type)
                    
                    print(f"  Trovato: {step_name} (tipo: {step_type})")
                    
                    # Estrai la descrizione dello step
                    # Cerca nelle prossime righe per "Step description"
                    step_desc = ""
                    for j in range(i, min(i + 10, len(lines))):
                        if 'Step description' in lines[j]:
                            # Estrai il valore dopo "Step description"
                            parts = re.split(r'Step description\s*[:|\t]\s*', lines[j], flags=re.IGNORECASE)
                            if len(parts) > 1:
                                step_desc = parts[1].strip()
                                break
                    
                    step_descriptions.append(step_desc)
                    if step_desc:
                        print(f"    Descrizione: {step_desc}")
                    
                    # Salta alla prossima riga per evitare di processare la stessa riga due volte
                    i += 1
                else:
                    print(f"  Ignorato: {step_match.group()} (tipo non riconosciuto o non presente)")
            i += 1
        
        if not valid_step_indices:
            print("\nNessuno Step valido trovato (con Stribeck o BodTimed nella riga successiva).")
            continue
        
        print(f"\nStep validi rilevati: {len(valid_step_indices)}")
        
        # 3. Estrazione del contenuto di ogni Step
        print("\n3. ESTRAZIONE CONTENUTI STEP")
        print("-" * 40)
        
        step_contents = []
        
        for idx, step_idx in enumerate(valid_step_indices):
            step_name = step_names[idx]
            step_type = step_types[idx]
            step_desc = step_descriptions[idx]
            
            # Determina l'indice del prossimo Step
            next_step_idx = None
            if idx < len(valid_step_indices) - 1:
                next_step_idx = valid_step_indices[idx + 1]
            
            # Estrai il contenuto dello Step
            step_content = extract_step_content(lines, step_idx, next_step_idx)
            step_contents.append(step_content)
            
            # Mostra info
            start_line = step_idx + 1
            end_line = next_step_idx if next_step_idx else len(lines)
            print(f"  Estratto: {step_name} ({step_type}) (righe {start_line}-{end_line})")
            if step_desc:
                print(f"    Descrizione: {step_desc}")
        
        print(f"\nStep estratti: {len(step_contents)}")
        
        # 4. Salvataggio dei file
        print("\n4. SALVATAGGIO FILE")
        print("-" * 40)
        
        while True:
            save_choice = input("\nVuoi salvare i file per ogni Step? (s/n): ").strip().lower()
            
            if save_choice in ['s', 'si', 'y', 'yes']:
                # Nome base del file originale
                base_name = Path(file_path).stem
                
                saved_files = []
                
                for i, (step_content, step_name, step_type, step_desc) in enumerate(zip(step_contents, step_names, step_types, step_descriptions), 1):
                    # Costruisci il nome del file: base_stepNNN_tipo[_descrizione].txt
                    if step_desc:
                        cleaned_desc = clean_filename(step_desc)
                        output_filename = f"{base_name}_{step_name}_{step_type}_{cleaned_desc}.txt"
                    else:
                        output_filename = f"{base_name}_{step_name}_{step_type}.txt"
                    
                    try:
                        # Salva il contenuto originale dello Step senza modifiche
                        with open(output_filename, 'w', encoding='utf-8') as f:
                            f.write(step_content)
                        
                        saved_files.append(output_filename)
                        
                        # Calcola statistiche
                        line_count = step_content.count('\n') + 1
                        char_count = len(step_content)
                        
                        print(f"  Salvato: {output_filename}")
                        print(f"    Righe: {line_count}, Caratteri: {char_count}")
                        if step_desc:
                            print(f"    Descrizione: {step_desc}")
                        
                    except Exception as e:
                        print(f"  ERRORE nel salvataggio di {step_name}: {e}")
                
                print(f"\nFile salvati nella cartella corrente:")
                print(f"Totale file salvati: {len(saved_files)}")
                
                # Mostra percorso completo
                current_dir = os.getcwd()
                print(f"Percorso: {current_dir}")
                break
                
            elif save_choice in ['n', 'no']:
                print("Salvataggio annullato.")
                break
            else:
                print("Risposta non valida! Usa 's' o 'n'.")
        
        # 5. Nuova analisi o uscita
        print("\n" + "=" * 60)
        choice = input("\nVuoi processare un altro file? (s/n): ").strip().lower()
        if choice not in ['s', 'si', 'sì', 'y', 'yes']:
            print("\nGrazie per aver usato STEP EXTRACTOR! Arrivederci.")
            break

if __name__ == "__main__":
    main()
