import subprocess
from prettytable import PrettyTable
import openai  
from colorama import init, Fore
import sys
import time
import threading

global spinner_running


init(autoreset=True)

# Banner Style T3L3machus 
def banner():
        padding = '  '
        END = '\033[0m'

       
        X = [[' ', "\\", ' ', '/'],[' ', ' ', '─', ' '],[' ', '/', ' ', "\\"]]
        T = [[' ', '┌','─','┐'], [' ', ' ','│',' '], [' ', ' ','┴',' ']]
        S = [[' ', '┌','─','┐'], [' ', '└','─','┐'], [' ', '└','─','┘']]
        C = [[' ', '┌','─','┐'], [' ', '│',' ',' '], [' ', '└','─','┘']]
        A = [[' ', '┌','─','┐'], [' ', '├','─','┤'], [' ', '┴',' ','┴']]
       	N = [[' ', '┌','┐','┌'], [' ', '│','│','│'], [' ', '┘','└','┘']]

        banner = [T, X, T, S, C, A, N]
        final = []
        print('\r')        

        gradient_colors = [21, 27, 33, 39, 54, 89, 126, 162, 163, 164, 165, 200, 201]

        current_color_idx = 0

        for charset in range(0, 3):
                for pos in range(0, len(banner)):
                        for i in range(0, len(banner[pos][charset])):
                                clr = f'\033[38;5;{gradient_colors[current_color_idx % len(gradient_colors)]}m'
                                char = f'{clr}{banner[pos][charset][i]}'
                                final.append(char)
                                current_color_idx += 1

                if charset < 2: final.append('\n   ')

        print(f"   {''.join(final)}")
        print(f'{END}{padding}                       Dig in TXT records\n')

banner()


OPENAI_API_KEY = 'XXXXXX YOUR API KEY XXXXXXXX'
openai.api_key = OPENAI_API_KEY

def spinner():
    chars = "|/-\\"
    while spinner_running:
        for char in chars:
            sys.stdout.write('\r' + char + ' Cleaning & Analysing ...')
            time.sleep(0.1)
            sys.stdout.flush()

def get_txt_records(domain):
    try:
        result = subprocess.check_output(["dig", "-t", "txt", domain], universal_newlines=True)
        lines = result.split("\n")
        txt_records = [line.split('"')[1] for line in lines if "IN	TXT" in line and '"' in line]
        return txt_records
    except subprocess.CalledProcessError:
        print(Fore.RED + "error while launching Dig command.")
        return []

def is_valid_word(word):
    segments = word.split('-') if '-' in word else word.split(' ')
    return all(segment.isalpha() for segment in segments)

def process_spf_record(record):
    parts = record.split("include:")
    includes = [part.split()[0] for part in parts[1:]]
    return includes


def clean_text(records):
    cleaned_records = []
    for record in records:
        if record.startswith("v=spf1"):
            cleaned_records.extend(process_spf_record(record))
            continue

        record = record.replace('-site-verification', '').replace('-domain-verification', '')
        
        if "=" in record:
            record = record.split("=")[0].strip()

        if is_valid_word(record):
            cleaned_records.append(record)
    
    return list(set(cleaned_records))


def analyze_services_with_gpt(records):

    global spinner_running 
    spinner_running = True
    thread = threading.Thread(target=spinner)
    thread.start()


    prompt = f"Analyze the following list and return a list on every line with a small comment after \":\" explaining the best probability that the web service goal is in less than 12 words, and give the official product name. Here is the list: {', '.join(records)}"
    
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{
        "role": "system",
        "content": "You are a helpful assistant."
    }, {
        "role": "user",
        "content": prompt
    }]
    )

    analysis = response.choices[0].message['content']

    spinner_running = False
    thread.join() 
    print("\rDone!          ")  

    table = PrettyTable()
    table.field_names = ["Service", "Most Probable Technology"]
    
    for line in analysis.split("\n"):
        parts = line.split(":")
        if len(parts) == 2:
            service, description = parts
            table.add_row([service.strip(), description.strip()])

    print (table)
    

def main():
    domain = input("Enter the domain to look for TXT records (enter q to Quit): ")

    if domain.lower() == 'q':
        return "quit"

    records = get_txt_records(domain)
    
    print("\nAll TXT Records:")
    for record in records:
        print(record)
    
    cleaned = clean_text(records)
    analyze_services_with_gpt(cleaned)

if __name__ == "__main__":
    main()
