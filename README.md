# Framesdirect_Data_Extractions
FramesDirect Web Scraper

This project is a Python script that scrapes product details from FramesDirect across all 99 paginated pages.
It uses Selenium (with Chrome WebDriver) and BeautifulSoup to extract product information such as brand, product name, original price, current price, and discounts.

Features

Scrapes all 99 pages of eyeglasses listings automatically.

Extracts brand, product name, original price, current price, and discount (if available).

Saves results into both CSV and JSON formats.

Handles missing values gracefully (null in CSV, null in JSON).

Headless browser mode supported (runs without opening a visible Chrome window).

Requirements

Python 3.8+

Google Chrome installed

Dependencies (install via pip):

pip install selenium webdriver-manager beautifulsoup4 lxml tqdm


Clone this repository:
git clone https://github.com/your-username/framesdirect-scraper.git
cd framesdirect-scraper

Run the scraper:
python scraper.py

Output files will be generated in the project folder:
framesdirect_output.csv
framesdirect_output.json

Configuration

Change HEADLESS = False in the script if you want to see the browser while scraping.
Adjust time.sleep(2) between page loads if you want faster or slower scraping.
By default, it scrapes up to 99 pages but will stop early if no products are found.


Example Output
CSV (framesdirect_output.csv)
Brand,Product_Name,Original_Price,Current_Price,Discount
Ray-Ban,RX5184 New Wayfarer Eyeglasses,200.0,150.0,25%
Oakley,OX3217 Socket 5.5 Eyeglasses,null,180.0,null
Gucci,GG0276O Eyeglasses,320.0,280.0,12%

JSON (framesdirect_output.json)
[
  {
    "Brand": "Ray-Ban",
    "Product_Name": "RX5184 New Wayfarer Eyeglasses",
    "Original_Price": 200.0,
    "Current_Price": 150.0,
    "Discount": "25%"
  },
  {
    "Brand": "Oakley",
    "Product_Name": "OX3217 Socket 5.5 Eyeglasses",
    "Original_Price": null,
    "Current_Price": 180.0,
    "Discount": null
  },
  {
    "Brand": "Gucci",
    "Product_Name": "GG0276O Eyeglasses",
    "Original_Price": 320.0,
    "Current_Price": 280.0,
    "Discount": "12%"
  }
]



# Sunglasses_Data_Extractions
Creating a data extraction for smarter Eyewear Choices
Glasses.com Web Scraper

This project is a Python script that scrapes eyeglasses product data from Glasses.com
It collects product information such as brand, product name, original price, current price, and discounts, then saves the results to both CSV and JSON formats.

Features

Scrapes multiple pages of eyeglass listings automatically.

Extracts:

Brand

Product name

Former/original price

Current/discounted price

Discount (if available)

Saves results in CSV and JSON files.

Removes duplicates before saving.

Runs in headless mode (no visible browser).

Requirements

Python 3.8+

Google Chrome installed

Dependencies (install via pip):

pip install selenium webdriver-manager beautifulsoup4 lxml

Usage

Clone the repository:

git clone https://github.com/your-username/glasses-scraper.git
cd glasses-scraper


Run the scraper:
python scraper.py


Output files will be saved in the ./extracted_data/ folder:

glasses_data.json
glasses_data.csv

Example Output
CSV (glasses_data.csv)
brand,name,former_price,current_price,discount
Oakley,OX3218 Pitchman R, $210.00, $147.00, 30% Off
Ray-Ban,RX5154 Clubmaster Eyeglasses, $200.00, $150.00, 25% Off
Coach,HC6132 Eyeglasses, null, $190.00, null

JSON (glasses_data.json)
[
  {
    "brand": "Oakley",
    "name": "OX3218 Pitchman R",
    "former_price": "$210.00",
    "current_price": "$147.00",
    "discount": "30% Off"
  },
  {
    "brand": "Ray-Ban",
    "name": "RX5154 Clubmaster Eyeglasses",
    "former_price": "$200.00",
    "current_price": "$150.00",
    "discount": "25% Off"
  },
  {
    "brand": "Coach",
    "name": "HC6132 Eyeglasses",
    "former_price": null,
    "current_price": "$190.00",
    "discount": null
  }
]






