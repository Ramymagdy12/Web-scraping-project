# Egyptian Industry Web Scraper - User Guide

This guide walks you through setting up and running the web scraper for [Egyptian Industry](https://www.egyptianindustry.com).

## Project Structure

The following files have been set up in your workspace:
1. [egyptian_industry_scraper.py](file:///c:/Users/ramy.salama/GB%20Corp/Analytics%20and%20Insights%20Department%20-%20General/Romany%20Adel/GB%20Lease/Web%20Scraping/egyptian_industry_scraper.py) — The main scraper script.
2. [config.json](file:///c:/Users/ramy.salama/GB%20Corp/Analytics%20and%20Insights%20Department%20-%20General/Romany%20Adel/GB%20Lease/Web%20Scraping/config.json) — Configuration file for your login credentials and target industries.

## Target Industries Mapped
Based on your request, the scraper targets the following categories:
- **Cars Industries**: ID `9` (`السيارات وقطع غيارها`)
- **Food Industries**: ID `10` (`الصناعات الغذائية`)
- **Chemicals Industries**: ID `11` (`المواد الكيميائية`)
- **Medicines & Cosmetics**: ID `19` (`أدوية وتجميل ومستلزمات`)
- **Industrial Detergents**: ID `12` (`المنظفات الصناعية`)

---

## Getting Started

### Step 1: Update Your Credentials
Open [config.json](file:///c:/Users/ramy.salama/GB%20Corp/Analytics%20and%20Insights%20Department%20-%20General/Romany%20Adel/GB%20Lease/Web%20Scraping/config.json) and replace the placeholder values with your login information:
```json
{
  "email": "YOUR_ACTUAL_EMAIL@example.com",
  "password": "YOUR_ACTUAL_PASSWORD",
  "industries": [9, 10, 11, 12, 19],
  "output_file": "scraped_companies.xlsx"
}
```

### Step 2: Run the Scraper
Open a terminal in your workspace directory:
`c:\Users\ramy.salama\GB Corp\Analytics and Insights Department - General\Romany Adel\GB Lease\Web Scraping`

And run the script using Python:
```bash
python egyptian_industry_scraper.py
```

---

## Features

- **Automated Authentication**: Dynamically fetches the Laravel CSRF token on runtime and logs into your account.
- **Data Safeguard (Auto-save)**: Automatically saves progress to `scraped_companies.xlsx` after each page is scraped. If the scrape is interrupted, you will not lose data.
- **Smart Parsing**: Dynamically parses contact blocks (Management Phone, Factory Phone, Mobile, General Manager, Email, Website, Activity, Address) from the layout.
- **Polite Scraping (Rate Limiting)**: Implements request spacing (default: 1.5 seconds) to avoid trigger firewalls or IP blocks.

## Output Columns In Excel

The generated Excel file `scraped_companies.xlsx` will contain the following columns:
1. **Company Name (الاسم)**
2. **Industry (القطاع)**
3. **City/Classification (المدينة/التصنيف)**
4. **النشاط** (Activity)
5. **المدير العام** (General Manager)
6. **الموبايل** (Mobile Phone)
7. **البريد الإلكترونى** (Email Address)
8. **هاتف الإدارة** (Management Phone)
9. **هاتف المصنع** (Factory Phone)
10. **الموقع الإلكترونى** (Website URL)
11. **عنوان المصنع** (Factory Address)
12. **العنوان** (General Address)
13. **الفاكس** (Fax Number)
14. **Detail Page URL**
