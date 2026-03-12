# Eldsneytisvaktin — Iceland Fuel Price Tracker

Automated tracker of fuel prices from Icelandic petrol stations. Data sourced from [gasvaktin.is](https://gasvaktin.is/).

Shows the **cheapest station price per brand** for both Bensín 95 and Diesel, updated every 15 minutes.

## How it works

1. A **GitHub Actions** workflow runs every 15 minutes
2. It fetches live price data from the [gasvaktin](https://github.com/gasvaktin/gasvaktin) project
3. It computes the cheapest price per brand (Atlantsolía, Costco, N1, ÓB, Olís, Orkan)
4. It appends a row to `data/history.csv` (historical record) and updates `data/current.json`
5. It builds a static site and deploys to **GitHub Pages**

## Setup

### 1. Create the repository

Create a new GitHub repository (e.g., `eldsneytisvaktin`) and push this code:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/eldsneytisvaktin.git
git push -u origin main
```

### 2. Enable GitHub Pages

1. Go to your repo → **Settings** → **Pages**
2. Under **Source**, select **GitHub Actions**

### 3. Seed the initial data

Either wait for the first scheduled run (up to 15 minutes), or trigger it manually:

1. Go to **Actions** → **Scrape fuel prices**
2. Click **Run workflow** → **Run workflow**

The site will be live at `https://YOUR_USERNAME.github.io/eldsneytisvaktin/`

## Files

```
├── .github/workflows/
│   └── scrape.yml          # Scheduled workflow (every 15 min)
├── scripts/
│   ├── scrape.py           # Fetches + processes gasvaktin data
│   └── build_site.py       # Generates static site in docs/
├── data/
│   ├── current.json        # Latest prices (auto-generated)
│   └── history.csv         # Full price history (auto-generated)
├── docs/
│   ├── index.html          # The website (auto-generated)
│   ├── current.json        # Copy for Pages (auto-generated)
│   └── history.csv         # Copy for Pages (auto-generated)
└── README.md
```

## Data format

### current.json
```json
{
  "timestamp": "2026-03-12T14:30:00Z",
  "brands": {
    "orkan": {
      "name": "Orkan",
      "stations": 73,
      "bensin95": 193.1,
      "diesel": 217.3,
      "bensin95_discount": null,
      "diesel_discount": 216.4
    }
  }
}
```

### history.csv
One row every 15 minutes with columns:
`timestamp, atlantsolia_bensin95, atlantsolia_diesel, ..., orkan_diesel_discount`

## Credits

Data from [gasvaktin.is](https://gasvaktin.is/) / [gasvaktin/gasvaktin](https://github.com/gasvaktin/gasvaktin) (MIT License).
