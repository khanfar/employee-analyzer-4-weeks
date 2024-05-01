import csv
from datetime import datetime, timedelta
import re
import tkinter as tk
from tkinter import filedialog
import os
import json
import matplotlib.pyplot as plt
import requests
import tempfile

date_ranges = []

def fetch_csv_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        # Save the response content to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(response.content)
        temp_file.close()
        return temp_file.name
    except requests.RequestException as e:
        print(f"Error fetching CSV from URL: {e}")
        return None

def read_csv_from_url(root, entry_filename):
    url = "https://huggingface.co/spaces/mhammad/Khanfar/raw/main/docs/your_data.csv"
    temp_csv_file = fetch_csv_from_url(url)
    if temp_csv_file:
        entry_filename.delete(0, tk.END)
        entry_filename.insert(0, temp_csv_file)

def parse_custom_date(date_str):
    date_pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
    match = date_pattern.match(date_str)
    if match:
        year, month, day = match.groups()
        return datetime(int(year), int(month), int(day))
    else:
        raise ValueError("Invalid date format in calendar text file")

def load_calendar(filename):
    dates = []
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line:  
                dates.append(parse_custom_date(line))
    return dates

def read_csv(filename, start_date, end_date):
    mechanics_work = {}
    cash_amount = 0
    with open(filename, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row.get('تقرير نهائي') and 'شيكل' in row.get('تقرير نهائي', ''):
                try:
                    entry_date = datetime.strptime(row['تاريخ الدخول'], '%d.%m.%Y')
                except ValueError:
                    print(f"Error parsing date for row: {row}")
                    continue

                if start_date <= entry_date <= end_date:
                    mechanic = row['اسم الميكانيكي'].strip()
                    if mechanic in mechanics_work:
                        mechanics_work[mechanic]['job_count'] += 1
                        amount_str = row['تقرير نهائي']
                        amount = re.findall(r'(\d+(\.\d+)?) شيكل', amount_str)
                        if amount:
                            mechanics_work[mechanic]['total_money'] += float(amount[0][0])
                        else:
                            print(f"No amount found for row: {row}")
                    else:
                        mechanics_work[mechanic] = {'job_count': 1, 'total_money': 0}
                        amount_str = row['تقرير نهائي']
                        amount = re.findall(r'(\d+(\.\d+)?) شيكل', amount_str)
                        if amount:
                            mechanics_work[mechanic]['total_money'] = float(amount[0][0])
                        else:
                            print(f"No amount found for row: {row}")

                    if row['رقم المركبة'].strip() == 'كاش' and row['نوع المركبه'].strip() == 'كاش':
                        cash_amount += float(re.findall(r'(\d+(\.\d+)?) شيكل', row['تقرير نهائي'])[0][0])
    return mechanics_work, cash_amount

def get_work_by_date_range(filename, date_ranges):
    all_work_by_date_range = []
    for start_date, end_date in date_ranges:
        mechanics_work, cash_amount = read_csv(filename, start_date, end_date)
        total_amount = sum(info['total_money'] for info in mechanics_work.values())
        total_jobs = sum(info['job_count'] for info in mechanics_work.values())
        all_work_by_date_range.append((mechanics_work, total_amount, total_jobs))
        
        print(f"Date Range: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}")
        print("Mechanics Work:", mechanics_work)
        print("Total Amount:", total_amount)
        print("Total Jobs:", total_jobs)
        print("-" * 50)
        
    return all_work_by_date_range

def write_to_text_file(data, filename, date_ranges):
    with open(filename, 'w', encoding='utf-8') as file:
        for i, (mechanics_work, total_amount, total_jobs) in enumerate(data):
            start_date, end_date = date_ranges[i]
            file.write(f'    ARAFAR JOB Calc. from date ({start_date.strftime("%d.%m.%Y")}) to date ({end_date.strftime("%d.%m.%Y")})\n')
            file.write('#' * 70 + '\n')
            file.write('-' * 50 + '\n')
            file.write(f'Total Amount: {total_amount} Shekel (Total Jobs: {total_jobs})\n')
            file.write('-' * 50 + '\n')
            for mechanic, info in mechanics_work.items():
                file.write(f'{mechanic}: {info["total_money"]} Shekel (Total Jobs: {info["job_count"]})\n')
                file.write('-' * 50 + '\n')

def plot_graph(all_work_by_date_range, date_ranges):
    plt.figure(figsize=(10, 6))  # Adjust the figure size as needed
    periods = [f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}" for start_date, end_date in date_ranges]
    total_jobs = [total_jobs for _, _, total_jobs in all_work_by_date_range]
    total_amounts = [total_amount for _, total_amount, _ in all_work_by_date_range]
    plt.barh(periods, total_amounts, color='skyblue')  # Use barh for horizontal bars
    for i, (period, amount) in enumerate(zip(periods, total_amounts)):
        plt.text(amount + 200, i, f"Total Amount: {amount} Shekel", va='center')
        plt.text(amount + 200, i-0.2, f"Total Jobs: {total_jobs[i]}", va='center')  # Adjust the vertical position
    plt.ylabel('Date Range')
    plt.xlabel('Total Amount (Shekel)')
    plt.title('(ARAFAT GARAGE) Total Amount by Date Range')
    plt.tight_layout()
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    plt.savefig(os.path.join(output_folder, "analyzer_graph.png"))
    plt.show()



def browse_file():
    filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    entry_filename.delete(0, tk.END)
    entry_filename.insert(0, filename)

def find_csv_in_directory():
    directory = os.path.dirname(os.path.abspath(__file__))
    for file in os.listdir(directory):
        if file.endswith(".csv"):
            entry_filename.delete(0, tk.END)
            entry_filename.insert(0, os.path.join(directory, file))
            break

def save_settings(filename, date_ranges):
    settings = {
        "date_ranges": [(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')) for start_date, end_date in date_ranges]
    }
    with open(filename, 'w') as file:
        json.dump(settings, file)

def load_settings(filename):
    with open(filename, 'r') as file:
        settings = json.load(file)
        date_ranges = [(datetime.strptime(start_date, '%Y-%m-%d'), datetime.strptime(end_date, '%Y-%m-%d')) for start_date, end_date in settings["date_ranges"]]
    return date_ranges

def start_processing():
    global date_ranges
    date_ranges = []
    for i in range(4):
        start_date = datetime.strptime(entry_start_dates[i].get(), '%d.%m.%Y')
        end_date = datetime.strptime(entry_end_dates[i].get(), '%d.%m.%Y')
        date_ranges.append((start_date, end_date))
    csv_filename = entry_filename.get()
    output_filename = 'employee_works.txt'
    all_work_by_date_range = get_work_by_date_range(csv_filename, date_ranges)
    write_to_text_file(all_work_by_date_range, output_filename, date_ranges)
    plot_graph(all_work_by_date_range, date_ranges)
    save_settings("settings.json", date_ranges)

def load_previous_settings():
    if os.path.exists("settings.json"):
        date_ranges = load_settings("settings.json")
        for i, (start_date, end_date) in enumerate(date_ranges):
            entry_start_dates[i].delete(0, tk.END)
            entry_start_dates[i].insert(0, start_date.strftime('%d.%m.%Y'))
            entry_end_dates[i].delete(0, tk.END)
            entry_end_dates[i].insert(0, end_date.strftime('%d.%m.%Y'))

def fill_with_last_four_weeks():
    global date_ranges
    date_ranges = []
    today = datetime.now()
    current_day_of_week = today.weekday()
    if current_day_of_week == 4:  
        end_date = today
    else:
        days_since_last_friday = (current_day_of_week - 4 + 7) % 7
        end_date = today - timedelta(days=days_since_last_friday)
    for i in range(4):
        start_date = end_date - timedelta(days=6)
        date_ranges.append((start_date, end_date))
        entry_start_dates[3 - i].delete(0, tk.END)
        entry_start_dates[3 - i].insert(0, start_date.strftime('%d.%m.%Y'))
        entry_end_dates[3 - i].delete(0, tk.END)
        entry_end_dates[3 - i].insert(0, end_date.strftime('%d.%m.%Y'))
        end_date -= timedelta(weeks=1)

root = tk.Tk()
root.title("التحليل الشهري للبيانات")
root.geometry("1000x400")

label_dates = []
entry_start_dates = []
entry_end_dates = []

for i in range(4):
    label_from = tk.Label(root, text=f"من تاريخ (dd.mm.yyyy) {i+1}:")
    label_from.grid(row=i, column=0)
    label_dates.append(label_from)

    entry_start_date = tk.Entry(root)
    entry_start_date.grid(row=i, column=1)
    entry_start_dates.append(entry_start_date)

    label_to = tk.Label(root, text=f"الى تاريخ (dd.mm.yyyy) {i+1}:")
    label_to.grid(row=i, column=2)
    label_dates.append(label_to)

    entry_end_date = tk.Entry(root)
    entry_end_date.grid(row=i, column=3)
    entry_end_dates.append(entry_end_date)

label_filename = tk.Label(root, text="CSV اسم ملف:")
label_filename.grid(row=5, column=0)

entry_filename = tk.Entry(root)
entry_filename.grid(row=5, column=1, columnspan=3)

button_browse = tk.Button(root, text="استكشاف", command=browse_file)
button_browse.grid(row=5, column=4)

button_find_csv = tk.Button(root, text="قاعدة البيانات", command=find_csv_in_directory)
button_find_csv.grid(row=5, column=5)

button_load_previous = tk.Button(root, text="استخدم الاعدادات السابقة", command=load_previous_settings)
button_load_previous.grid(row=6, columnspan=6)

button_fill_current_month_weeks = tk.Button(root, text="ملء بأسابيع الشهر الحالي", command=fill_with_last_four_weeks)
button_fill_current_month_weeks.grid(row=7, columnspan=6)

button_start = tk.Button(root, text="ابدأ الحساب", command=start_processing)
button_start.grid(row=8, columnspan=6)

button_read_from_url = tk.Button(root, text="قراءة من الرابط", command=lambda: read_csv_from_url(root, entry_filename))
button_read_from_url.grid(row=6, column=4)

root.mainloop()
