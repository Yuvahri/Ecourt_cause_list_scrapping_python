import os
import time
import json
import requests
import pandas as pd
import tempfile
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os
import cv2
import pytesseract
from PIL import Image
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
def get_col_widths(df, page_width, min_width=40, max_width=200):
    col_lengths = [max([len(str(cell)) for cell in df[col]] + [len(col)]) for col in df.columns]
    total = sum(col_lengths)

    if total == 0:
        print("⚠️ Column lengths sum to zero. Using default widths.")
        return [min_width] * df.shape[1]

    scale = page_width / total
    return [max(min_width, min(max_width, l * scale)) for l in col_lengths]

def handle_alert(driver, timeout=5):
    try:
        WebDriverWait(driver, timeout).until(EC.alert_is_present())
        alert = driver.switch_to.alert
        print(f"⚠️ Alert appeared: {alert.text}")
        alert.accept()
        time.sleep(1)  # Give browser time to settle
        print("✅ Alert closed successfully.")
    except:
        pass

def wait_for_dropdown(driver, dropdown_id, min_options=2, timeout=15):
    def dropdown_ready(d):
        try:
            el = d.find_element(By.ID, dropdown_id)
            options = el.find_elements(By.TAG_NAME, "option")
            return el if len([opt for opt in options if opt.text.strip()]) >= min_options else False
        except:
            return False

    return WebDriverWait(driver, timeout).until(dropdown_ready)

from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.by import By

def safe_select_dropdown(driver, dropdown_id, visible_text, timeout=10):
    try:
        # Wait until dropdown is visible and enabled
        dropdown = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.ID, dropdown_id))
        )

        # Scroll into view and click via JS to ensure visibility
        driver.execute_script("arguments[0].scrollIntoView(true);", dropdown)
        driver.execute_script("arguments[0].click();", dropdown)

        # Select the option
        Select(dropdown).select_by_visible_text(visible_text)

        # Trigger change event manually
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", dropdown)
        print(f"✅ Selected Court: {visible_text}")

    except ElementNotInteractableException:
        print("❌ Dropdown not interactable. Trying JS fallback...")
        try:
            # JS fallback: set value and trigger change
            driver.execute_script(f"""
                const dropdown = document.getElementById('{dropdown_id}');
                dropdown.value = [...dropdown.options].find(opt => opt.text.trim() === '{visible_text}').value;
                dropdown.dispatchEvent(new Event('change'));
            """)
            print(f"✅ JS fallback succeeded for: {visible_text}")
        except Exception as e:
            print(f"❌ JS fallback failed: {e}")

    except TimeoutException:
        print("❌ Timeout waiting for dropdown to be clickable.")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

# If on Windows, explicitly set the path to tesseract.exe
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
def extract_table_headings(result_div):
    try:
        heading_div = result_div.find_element(By.ID, "table_heading")
        spans = heading_div.find_elements(By.TAG_NAME, "span")
        return [span.text.strip() for span in spans if span.text.strip()]
    except:
        return []
def extract_text_from_captcha(image_path: str) -> str:
    # Load the image
    image = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply thresholding to make text clearer
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    # Optionally remove noise (morphological opening)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    clean = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # Save intermediate step if needed for debugging
    # cv2.imwrite("cleaned_captcha.png", clean)

    # Use pytesseract to extract text
    text = pytesseract.image_to_string(clean, config="--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")

    # Clean up unwanted characters/spaces/newlines
    return text.strip()


from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def export_to_pdf(df, filename="output.pdf", headings=None):
    """
    Export a pandas DataFrame to a well-formatted PDF file.
    Handles empty DataFrames and variable-length text gracefully.
    """
    try:
        if df is None or df.empty:
            print("⚠️ No data to export. DataFrame is empty.")
            return

        # Setup document
        doc = SimpleDocTemplate(
            filename,
            pagesize=landscape(A4),
            leftMargin=20,
            rightMargin=20,
            topMargin=30,
            bottomMargin=30
        )

        styles = getSampleStyleSheet()
        elements = []

        # Title
        title = Paragraph("<b>Cause List Data</b>", styles["Title"])
        elements.append(title)
        elements.append(Spacer(1, 0.2 * inch))

        # Prepare table data
        data = [list(df.columns)] + df.values.tolist()

        # Estimate column widths (prevent layout overflow)
        num_cols = len(df.columns)
        page_width = A4[1] - 60  # Landscape width minus margins
        base_width = page_width / max(1, num_cols)

        col_widths = []
        for col in df.columns:
            max_len = max(df[col].astype(str).map(len).max(), len(str(col)))
            width = min(max(60, base_width * (max_len / 15)), 200)
            col_widths.append(width)

        # Create ReportLab Table
        table = Table(data, colWidths=col_widths, repeatRows=1)

        # Styling
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ])
        table.setStyle(style)

        # Add to doc and build
        elements.append(table)
        doc.build(elements)

        print(f"✅ PDF exported successfully: {filename}")

    except Exception as e:
        print(f"❌ PDF export failed: {e}")


SAVE_DIR = "output"
os.makedirs(SAVE_DIR, exist_ok=True)

def setup_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
    return webdriver.Chrome(options=options)

def close_modal_if_present(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'modal') and contains(@style, 'display: block')]"))
        )
        print("⚠️ Modal detected. Closing...")
        driver.execute_script("""
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                modal.style.display = 'none';
                modal.classList.remove('show');
            });
        """)
        time.sleep(1)
        print("✅ Modal closed.")
    except:
        print("👌 No modal blocking the page.")

def save_and_show_captcha(driver, captcha_div_id, filename):
    try:
        captcha_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, captcha_div_id))
        )
        captcha_img = captcha_container.find_element(By.TAG_NAME, "img")

        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView(true);", captcha_img)
        time.sleep(0.5)

        # Screenshot only the captcha element (not full page)
        captcha_path = os.path.join(SAVE_DIR, filename)
        captcha_img.screenshot(captcha_path)

        print(f"📸 Captcha saved at: {captcha_path}")
        Image.open(captcha_path).show()

        return captcha_path

    except Exception as e:
        print("❌ Failed to capture captcha from browser:", e)
        return None


def fetch_cause_list():
    driver = setup_driver()
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(), options=chrome_options)
    driver.get("https://services.ecourts.gov.in/ecourtindia_v6/")
    close_modal_if_present(driver)

    try:
        # Click Cause List tab
        cause_list_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "leftPaneMenuCL"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", cause_list_link)
        driver.execute_script("arguments[0].click();", cause_list_link)
        time.sleep(2)
        close_modal_if_present(driver)

        print("\n⚙️ Select Court Details")

        # 🧩 STATE
        # 🧩 STATE
        state = wait_for_dropdown(driver, "sess_state_code")
        state_options = [opt.text.strip() for opt in state.find_elements(By.TAG_NAME, "option") if opt.text.strip()]

        print("\nAvailable States:")
        for i, opt in enumerate(state_options, 1):
            print(f"{i}. {opt}")

        while True:
            try:
                st_index = int(input("\nEnter the number of the State: ").strip()) - 1
                if 0 <= st_index < len(state_options):
                    st_choice = state_options[st_index]
                    Select(state).select_by_visible_text(st_choice)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", state)
                    print(f"✅ Selected State: {st_choice}")
                    break
                else:
                    print("❌ Invalid number. Try again.")
            except ValueError:
                print("❌ Please enter a valid number.")
        time.sleep(2)

        # 🧩 DISTRICT
        dist = wait_for_dropdown(driver, "sess_dist_code")
        dist_options = [opt.text.strip() for opt in dist.find_elements(By.TAG_NAME, "option") if opt.text.strip()]

        print("\nAvailable Districts:")
        for i, opt in enumerate(dist_options, 1):
            print(f"{i}. {opt}")

        while True:
            try:
                dist_index = int(input("\nEnter the number of the District: ").strip()) - 1
                if 0 <= dist_index < len(dist_options):
                    dist_choice = dist_options[dist_index]
                    Select(dist).select_by_visible_text(dist_choice)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", dist)
                    print(f"✅ Selected District: {dist_choice}")
                    break
                else:
                    print("❌ Invalid number. Try again.")
            except ValueError:
                print("❌ Please enter a valid number.")
        time.sleep(2)

        # 🧩 COURT COMPLEX
        complex_ = wait_for_dropdown(driver, "court_complex_code")
        complex_options = [opt.text.strip() for opt in complex_.find_elements(By.TAG_NAME, "option") if opt.text.strip()]

        print("\nAvailable Court Complexes:")
        for i, opt in enumerate(complex_options, 1):
            print(f"{i}. {opt}")

        while True:
            try:
                complex_index = int(input("\nEnter the number of the Court Complex: ").strip()) - 1
                if 0 <= complex_index < len(complex_options):
                    complex_choice = complex_options[complex_index]
                    Select(complex_).select_by_visible_text(complex_choice)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", complex_)
                    print(f"✅ Selected Court Complex: {complex_choice}")
                    break
                else:
                    print("❌ Invalid number. Try again.")
            except ValueError:
                print("❌ Please enter a valid number.")
        time.sleep(2)
        close_modal_if_present(driver)

        # 🧩 COURT ESTABLISHMENT (Optional but may trigger alert)
        try:
            handle_alert(driver)
            time.sleep(2)

            # Fetch all options
            est = wait_for_dropdown(driver, "court_est_code")
            est_options = [opt.text.strip() for opt in est.find_elements(By.TAG_NAME, "option") if opt.text.strip()]

            print("\nAvailable Court Establishments:")
            for i, opt in enumerate(est_options, 1):
                print(f"{i}. {opt}")

            # Ask user to select by number instead of typing
            choice_index = int(input("\nEnter the number of Court Establishment: ").strip()) - 1
            if choice_index < 0 or choice_index >= len(est_options):
                print("❌ Invalid selection.")
            else:
                est_choice = est_options[choice_index]
                Select(est).select_by_visible_text(est_choice)
                driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", est)
                print(f"✅ Selected Court Establishment: {est_choice}")

            time.sleep(2)
        except:
            print("ℹ️ No Court Establishment dropdown found.")
        close_modal_if_present(driver)
       # 🧩 COURT
        time.sleep(5)
        court = wait_for_dropdown(driver, "CL_court_no")
        court_options = [opt.text.strip() for opt in court.find_elements(By.TAG_NAME, "option") if opt.text.strip()]

        if not court_options:
            print("❌ No court options found. Check previous selections.")
            return

        print("\nAvailable Courts:")
        for i, opt in enumerate(court_options, 1):
            print(f"{i}. {opt}")

        while True:
            try:
                choice_index = int(input("\nEnter the number of the Court: ").strip()) - 1
                if 0 <= choice_index < len(court_options):
                    court_choice = court_options[choice_index]
                    Select(court).select_by_visible_text(court_choice)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change'))", court)
                    print(f"✅ Selected Court: {court_choice}")
                    break
                else:
                    print("❌ Invalid number. Try again.")
            except ValueError:
                print("❌ Please enter a valid number.")


        # 🧩 DATE
        date_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "causelist_date")))
        date_field.clear()
        date_field.send_keys("27-10-2025")

        # 🧩 TYPE (civil / criminal)
        choice = input("\n⚖️ Enter 'civil' or 'criminal': ").strip().lower()
        if choice == "civil":
            btn_xpath = "//button[@onclick=\"submit_causelist('civ')\"]"
        elif choice == "criminal":
            btn_xpath = "//button[@onclick=\"submit_causelist('cri')\"]"
        else:
            print("⚠️ Invalid choice.")
            driver.quit()
            return

        #Step 1: Locate captcha input
        save_and_show_captcha(driver, "div_captcha_cause_list", "cause_captcha.png")
        captcha_text = input("🔐 Enter captcha shown in image: ").strip()
        try:
            captcha_input = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "cause_list_captcha_code"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", captcha_input)
            time.sleep(0.5)

            # Inject captcha via JS and trigger events
            driver.execute_script("""
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input'));
                arguments[0].dispatchEvent(new Event('change'));
            """, captcha_input, captcha_text)

            # Try sending keys normally
            try:
                captcha_input.clear()
                captcha_input.send_keys(captcha_text)
                print("✅ Captcha entered successfully.")
            except Exception as inner_e:
                print("⚠️ Typing failed, injecting via JS:", inner_e)
                driver.execute_script("arguments[0].value = arguments[1];", captcha_input, captcha_text)
                print("✅ Captcha value set via JS.")

        except Exception as e:
            print("❌ Failed to set captcha:", e)

    # Confirm captcha value
        value = driver.execute_script("return document.getElementById('cause_list_captcha_code').value;")
        print("🔎 Captcha currently in box:", value)
        print("Sent still captcha")

        # 🧩 Step 2: Locate and click submit button
        try:
            button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, btn_xpath))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(1)

            # Force visibility and enablement
            driver.execute_script("""
                arguments[0].style.display = 'block';
                arguments[0].style.visibility = 'visible';
                arguments[0].style.opacity = 1;
                arguments[0].disabled = false;
            """, button)

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, btn_xpath)))

            # Trigger full JS event chain
            driver.execute_script("""
                arguments[0].click();
                arguments[0].dispatchEvent(new Event('click'));
            """, button)
            print("✅ After button click")

        except Exception as e:
            print("❌ Failed to click submit button:", e)
        # 🧩 Step 4: Detect modal after submission
        time.sleep(3)
        try:
            modal = driver.find_element(By.CLASS_NAME, "modal")
            if modal.is_displayed():
                print("⚠️ Modal detected after submission. Likely invalid captcha.")
                print("🧪 Modal text:", modal.text.strip())

                # Close modal
                close_btns = driver.find_elements(By.XPATH, "//button[contains(@class, 'btn-close') or @data-bs-dismiss='modal']")
                for btn in close_btns:
                    try:
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(1)
                        print("✅ Modal closed.")
                        break
                    except:
                        continue

                # 🧩 Step 5: Refresh captcha and retry
                save_and_show_captcha(driver, "div_captcha_cause_list", "cause_captcha_retry.png")
                captcha_text = input("🔁 Enter refreshed captcha: ").strip()

                # Inject new captcha
                captcha_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "cause_list_captcha_code"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", captcha_input)
                driver.execute_script("""
                    arguments[0].value = arguments[1];
                    arguments[0].dispatchEvent(new Event('input'));
                    arguments[0].dispatchEvent(new Event('change'));
                """, captcha_input, captcha_text)

                # Resubmit
                driver.execute_script("arguments[0].click();", button)
                print("🔁 Retried submission with new captcha.")

        except Exception as e:
            print("✅ No modal after submission.")   
        # 🧩 Step 4: Wait for results
        try:
            WebDriverWait(driver, 25).until(
                lambda d: d.find_element(By.ID, "res_cause_list").text.strip() != ""
            )
            result_div = driver.find_element(By.ID, "res_cause_list")

            raw_html = result_div.get_attribute("innerHTML")
            with open(os.path.join(SAVE_DIR, "raw_result.html"), "w", encoding="utf-8") as f:
                f.write(raw_html)
            print("📄 Raw HTML saved to output/raw_result.html")

            try:
                table = result_div.find_element(By.TAG_NAME, "table")
                rows = table.find_elements(By.TAG_NAME, "tr")

                # ✅ Split header and data correctly
                header_cells = rows[0].find_elements(By.TAG_NAME, "th")
                if not header_cells:
                    # fallback if <th> not found — use first row <td> as header
                    header_cells = rows[0].find_elements(By.TAG_NAME, "td")

                headers = [h.text.strip() for h in header_cells]
                data = [
                    [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
                    for row in rows[1:]
                    if row.text.strip()
                ]

                df = pd.DataFrame(data, columns=headers if headers else None)

                # Extract heading spans for title
                try:
                    heading_div = result_div.find_element(By.ID, "table_heading")
                    spans = heading_div.find_elements(By.TAG_NAME, "span")
                    heading_texts = [span.text.strip() for span in spans if span.text.strip()]
                except Exception:
                    heading_texts = []

                # ✅ Dynamic filename (optional)
                pdf_name = os.path.join(SAVE_DIR, "cause_list_output.pdf")

                # ✅ Call fixed export_to_pdf()
                export_to_pdf(df, filename=pdf_name, headings=heading_texts)

            except Exception as e:
                print(f"❌ Error processing result table: {e}")

        except Exception:
            print("❌ Timed out waiting for results.")

    except Exception as e:
        print("❌ Error:", e)
    finally:
        driver.quit()



if __name__ == "__main__":
    fetch_cause_list()