# CLAUDE.md — מחשבון יבוא ויצוא ישראל

## סקירה כללית

מחשבון אינטראקטיבי לנתוני סחר חוץ של ישראל, המבוסס על נתוני הלשכה המרכזית לסטטיסטיקה (למ"ס). הממשק בנוי כדף HTML סטטי, ללא שרת ובלי build system — נפתח ישירות בדפדפן.

## מבנה הפרויקט

```
import_export_calculator/
├── index.html              # האפליקציה הראשית — כל ה-UI וה-JS
├── process_data.py         # סקריפט Python לעיבוד קבצי ZIP מה-למ"ס
├── chart.umd.min.js        # Chart.js 4.4.0 (מקומי, לא CDN)
├── data/
│   ├── trade_data_2025.js  # נתוני 2025 מעובדים (const TRADE_DATA / TRADE_DATA_2025)
│   ├── trade_data_2024.js  # נתוני 2024 (אם קיים) — const TRADE_DATA_2024
│   ├── trade_data_2026.js  # נתוני 2026 (אם קיים) — const TRADE_DATA_2026
│   └── raw/                # קבצי ZIP גולמיים מה-למ"ס
│       ├── imp_1_2025.zip
│       ├── exp_1_2025.zip
│       └── ...
└── CLAUDE.md               # קובץ זה
```

## זרימת הנתונים

1. **קבצי ZIP גולמיים** מה-למ"ס (`imp_M_YYYY.zip`, `exp_M_YYYY.zip`) → `data/raw/`
2. **`process_data.py`** קורא את ה-ZIP, מנתח שורות בפורמט רוחב-קבוע, מייצר `data/trade_data_YYYY.js`
3. **`index.html`** טוען את ה-JS ומציג גרפים ואינטראקציות

## הפעלת process_data.py

```bash
python process_data.py --year 2024
python process_data.py --year 2025
python process_data.py --year 2026
```

## פורמט קובץ CBS (רוחב קבוע)

```
עמדה 3:      זרם (1=יבוא, 2=יצוא)
עמדות 10-13: קוד מדינה (ISO 2 אותיות)
עמדות 16-26: קוד סחורה (10 ספרות HS)
עמדות 26-40: ערך (אלפי דולר)
```

## מבנה JSON שנוצר (`trade_data_YYYY.js`)

```javascript
const TRADE_DATA_YYYY = {
  year: YYYY,
  commodity:       { flow: { month: { code10: value } } },
  country:         { flow: { month: { countryCode: value } } },
  country_chapter: { flow: { month: { country: { code2: value } } } },
  country_chapter_4: { flow: { month: { country: { code4: value } } } },
  country_chapter_6: { flow: { month: { country: { code6: value } } } }
};
// month "00" = סה"כ שנתי
// 2025 גם מייצא TRADE_DATA לתאימות לאחור
```

## לוגיקת הגרפים

- **גרף 1**: טופ 8 לפי 2 ספרות (פרקים) — לחיצה פותחת גרף 2
- **גרף 2**: טופ 8 לפי 4 ספרות עבור הפרק שנבחר — לחיצה פותחת גרף 3
- **גרף 3**: טופ 8 לפי 6 ספרות עבור הפרט שנבחר
- כל גרף כולל לחצן "השוואה שנתית" — פאנל רבעוני לאורך שנים

## מצב סינון

| משתנה | תיאור |
|--------|--------|
| `year` | שנה פעילה |
| `flow` | '1'=יבוא, '2'=יצוא |
| `month` | '00'=כל השנה, '01'-'12'=חודש |
| `tab` | 'commodity'/'country' |
| `selectedCountry` | קוד ISO 2 אותיות או '' |
| `selectedChapter` | קוד 2 ספרות (פרק סחורה) |
| `selectedChapter4` | קוד 4 ספרות (פרט, בלשונית מדינה בלבד) |
| `drillPath` | מערך [{code, digits}] — מסלול ירידה |
| `ALL_DATA` | {year: TRADE_DATA_OBJ} — כל השנים הזמינות |

## כלי עיון לשמות קטגוריות

- `COMMODITY_NAMES` — 2 ספרות (97 פרקי HS)
- `COMMODITY_NAMES_4` — 4 ספרות (~400 כותרות)
- `COMMODITY_NAMES_6` — 6 ספרות (~500 תת-כותרות נבחרות)
- **שמות עברו עיבוד באמצעות AI** — אינם מהספר הרשמי; לנוחות בלבד

## הוספת שנה חדשה

1. הורד קבצי ZIP מה-למ"ס ושמור ב-`data/raw/` עם שמות `imp_M_YYYY.zip`/`exp_M_YYYY.zip`
2. הפעל: `python process_data.py --year YYYY`
3. הסקריפט יוצר `data/trade_data_YYYY.js` עם `const TRADE_DATA_YYYY = {...}`
4. index.html כבר טוען `data/trade_data_2024.js` ו-`data/trade_data_2026.js` אוטומטית

## ייצוא CSV

לחצן "ייצוא CSV" בראש הטבלה מייצא את הנתונים הנוכחיים עם BOM לעברית.

## השוואה שנתית

לחצן "↔ השוואה שנתית" ליד כל גרף מציג גרף בר מקובץ של Q1-Q4 לפי כל השנים הזמינות. אם שנת 2026 חלקית, מסומן בכוכבית.

## עקרונות פיתוח

- **אין build system** — vanilla JS, אין npm, אין React
- **CORS**: בגלל `file://` פרוטוקול, אין fetch — כל הנתונים נטענים כ-`<script>`
- **ביצועים**: כל האגרגציות נעשות ב-Python; ב-JS רק הצגה
- **RTL**: הדף מלא בעברית `dir="rtl"`, Chart.js עם `ticks.color: '#000'`
