import zipfile
import json
import os
import sys
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(SCRIPT_DIR, 'data')
RAW_DIR    = os.path.join(DATA_DIR, 'raw')
os.makedirs(DATA_DIR, exist_ok=True)

# Year to process — override with --year YYYY argument
YEAR = 2025
for i, arg in enumerate(sys.argv[1:]):
    if arg == '--year' and i + 1 < len(sys.argv[1:]):
        YEAR = int(sys.argv[i + 2])
    elif arg.isdigit() and len(arg) == 4:
        YEAR = int(arg)

print(f"Processing year: {YEAR}")

# Structure 1: commodity drill-down (no country breakdown)
# drill_commodity[flow][month][commodity_10] = value
drill_commodity = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

# Structure 2: country totals (no commodity breakdown)
# drill_country[flow][month][country] = value
drill_country = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

# Structure 3: per-country chapter breakdown (2-digit commodity)
# country_chapter[flow][month][country][commodity_2] = value
country_chapter = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))

# Structure 4: per-country 4-digit breakdown
# country_chapter_4[flow][month][country][commodity_4] = value
country_chapter_4 = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))

# Structure 5: per-country 6-digit breakdown
# country_chapter_6[flow][month][country][commodity_6] = value
country_chapter_6 = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(int))))

def parse_line(line):
    if len(line) < 40:
        return None
    flow      = line[3]
    country   = line[10:13].strip()
    commodity = line[16:26].strip()
    value_str = line[26:40].strip()

    if flow not in ('1', '2'):
        return None
    if not commodity or not value_str:
        return None
    try:
        value = int(value_str)
    except ValueError:
        return None

    return {
        'flow': flow,
        'country': country,
        'commodity': commodity.zfill(10),
        'value': value
    }

processed = 0

for month_num in range(1, 13):
    for flow_prefix in ('imp', 'exp'):
        filename = f"{flow_prefix}_{month_num}_{YEAR}.zip"
        filepath = os.path.join(RAW_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Missing: {filename}")
            continue

        month_key = str(month_num).zfill(2)

        with zipfile.ZipFile(filepath, 'r') as zf:
            txt_files = [f for f in zf.namelist() if f.endswith('.txt')]
            for txt_file in txt_files:
                with zf.open(txt_file) as f:
                    for raw_line in f:
                        line = raw_line.decode('utf-8', errors='ignore').rstrip()
                        parsed = parse_line(line)
                        if parsed:
                            fl = parsed['flow']
                            drill_commodity[fl][month_key][parsed['commodity']] += parsed['value']
                            drill_country[fl][month_key][parsed['country']] += parsed['value']
                            country_chapter[fl][month_key][parsed['country']][parsed['commodity'][:2]] += parsed['value']
                            country_chapter_4[fl][month_key][parsed['country']][parsed['commodity'][:4]] += parsed['value']
                            country_chapter_6[fl][month_key][parsed['country']][parsed['commodity'][:6]] += parsed['value']
                            processed += 1

print(f"Processed: {processed:,} lines")

# Build all-months totals (month "00" = full year)
for fl in list(drill_commodity.keys()):
    for mo in list(drill_commodity[fl].keys()):
        for commodity, value in drill_commodity[fl][mo].items():
            drill_commodity[fl]['00'][commodity] += value

for fl in list(drill_country.keys()):
    for mo in list(drill_country[fl].keys()):
        for country, value in drill_country[fl][mo].items():
            drill_country[fl]['00'][country] += value

for fl in list(country_chapter.keys()):
    for mo in list(country_chapter[fl].keys()):
        for country in country_chapter[fl][mo]:
            for ch, value in country_chapter[fl][mo][country].items():
                country_chapter[fl]['00'][country][ch] += value

for fl in list(country_chapter_4.keys()):
    for mo in list(country_chapter_4[fl].keys()):
        for country in country_chapter_4[fl][mo]:
            for ch4, value in country_chapter_4[fl][mo][country].items():
                country_chapter_4[fl]['00'][country][ch4] += value

for fl in list(country_chapter_6.keys()):
    for mo in list(country_chapter_6[fl].keys()):
        for country in country_chapter_6[fl][mo]:
            for ch6, value in country_chapter_6[fl][mo][country].items():
                country_chapter_6[fl]['00'][country][ch6] += value

# Convert to regular dicts
output = {
    "year": YEAR,
    "commodity": {f: {m: dict(c) for m, c in months.items()} for f, months in drill_commodity.items()},
    "country":   {f: {m: dict(c) for m, c in months.items()} for f, months in drill_country.items()},
    "country_chapter": {
        f: {m: {c: dict(chs) for c, chs in countries.items()} for m, countries in months.items()}
        for f, months in country_chapter.items()
    },
    "country_chapter_4": {
        f: {m: {c: dict(chs) for c, chs in countries.items()} for m, countries in months.items()}
        for f, months in country_chapter_4.items()
    },
    "country_chapter_6": {
        f: {m: {c: dict(chs) for c, chs in countries.items()} for m, countries in months.items()}
        for f, months in country_chapter_6.items()
    }
}

out_path = os.path.join(DATA_DIR, f"trade_data_{YEAR}.json")
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, separators=(',', ':'))

size_mb = os.path.getsize(out_path) / 1024 / 1024
print(f"Saved trade_data_{YEAR}.json ({size_mb:.1f} MB)")

js_path = os.path.join(DATA_DIR, f"trade_data_{YEAR}.js")
with open(js_path, 'w', encoding='utf-8') as f:
    f.write(f'var TRADE_DATA_{YEAR} = ')
    json.dump(output, f, ensure_ascii=False, separators=(',', ':'))
    f.write(';')

js_mb = os.path.getsize(js_path) / 1024 / 1024
print(f"Saved trade_data_{YEAR}.js ({js_mb:.1f} MB)")

# Stats
for fl, label in [('1', 'יבוא'), ('2', 'יצוא')]:
    n_commodities = len(output['commodity'].get(fl, {}).get('00', {}))
    n_countries   = len(output['country'].get(fl, {}).get('00', {}))
    total_value   = sum(output['country'].get(fl, {}).get('00', {}).values())
    print(f"{label}: {n_commodities:,} commodity codes, {n_countries} countries, total ${total_value:,}K")
