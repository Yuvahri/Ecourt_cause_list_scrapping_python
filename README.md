Automated eCourts Cause List Scraper

This Python project automates fetching cause list data from the eCourts India
 website and exports it as a well-formatted PDF. It handles dropdown selections, captcha input, and result extraction seamlessly.

🚀 Features

🧩 Navigate the eCourts Cause List section automatically

⚙️ Select State, District, Court Complex, Court Establishment, and Court dynamically

🔐 Capture and display captcha for manual entry

🧠 Optional captcha text extraction using Tesseract OCR

🧾 Export the cause list table to a landscape PDF using ReportLab

🧹 Handles alerts, popups, and invalid captcha gracefully

🛠️ Tech Stack

Python 3.x

Selenium – Browser automation

OpenCV – Captcha image processing

pytesseract – OCR for captcha text extraction

Pandas – Data structuring

ReportLab – PDF generation

Pillow (PIL) – Captcha image display

⚡ Setup Instructions

Clone the repository

git clone <your-repo-url>
cd <repo-directory>


Install dependencies

pip install selenium opencv-python pytesseract pandas reportlab pillow


Install ChromeDriver and ensure it matches your Chrome version.

Install Tesseract OCR

Windows: https://github.com/tesseract-ocr/tesseract

Set the path in the script if required:

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


Run the script

python fetch_cause_list.py


Follow prompts to select State, District, Court, and enter captcha.

Check the output in the output/ folder. PDF and raw HTML will be saved there.

📂 Output

cause_list_output.pdf – Formatted cause list report

raw_result.html – Raw HTML from eCourts for reference

Captcha screenshots displayed for manual input

⚠️ Notes

Captcha must be entered manually unless OCR is enabled and accurate.

Ensure Chrome and ChromeDriver versions match to avoid errors.

Dates are currently hardcoded in the script; modify as needed.

💡 Future Improvements

Fully automate captcha solving with improved OCR.

Allow dynamic date input.

Add logging and error handling for failed submissions.
  
> The default date is **27-10-2025** because courts resume work on this day after Diwali. Output files will always reflect the latest available cause list.

