import fitz # PyMuPDF
import os

def extract_text_from_pdf(pdf_path):
    """
    Extracts all text from a given PDF file.

    Args:
        pdf_path (str): The file path to the PDF.

    Returns:
        str: The concatenated text from all pages of the PDF.
             Returns None if an error occurs (e.g., file not found, corrupted PDF).
    """
    if not os.path.exists(pdf_path):
        # Log error: File not found
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    full_text = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            full_text.append(page.get_text("text"))
        doc.close()
        return "".join(full_text)
    except fitz.errors.FitzError as e: # Specific exception for fitz
        # Log error: FitzError (e.g. corrupted PDF, not a PDF)
        print(f"FitzError while processing {pdf_path}: {e}")
        return None
    except Exception as e:
        # Log error: General error during PDF processing
        print(f"An unexpected error occurred while processing {pdf_path}: {e}")
        return None

import re

def identify_prices_in_text(text_content):
    """
    Identifies potential prices in a given text string.

    Args:
        text_content (str): The text to search for prices.

    Returns:
        list[str]: A list of identified price strings.
    """
    if not text_content:
        return []

    # Regex to find numbers that could be prices:
    # - Optional currency symbols (common ones) at the beginning or end.
    # - Numbers can have thousands separators (commas or spaces) - handled by allowing them but not requiring.
    # - Decimal part is optional, can use dot or comma, followed by 1 or 2 digits.
    # - Ensure that it doesn't just match any number by looking for some price-like structure.
    
    # This regex is a starting point and can be refined.
    # It tries to match common currency symbols, then digits with optional decimal part, or vice-versa.
    # It handles symbols like $, €, £, грн, UAH. And decimal separators . or ,
    # (?:\s*) is for optional space.
    # \d{1,3}(?:[,\s]\d{3})* matches numbers with optional thousands separators (e.g., 1,000,000 or 1 000 000)
    # (?:[.,]\d{1,2})? matches optional decimal part.
    
    # Pattern for "Symbol Amount" (e.g., $123.45)
    pattern1 = r'([\$€£грнUAH₴]\s*\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d{1,2})?)'
    # Pattern for "Amount Symbol" (e.g., 123.45 €)
    pattern2 = r'(\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d{1,2})?\s*[\$€£грнUAH₴])'
    # Pattern for amounts without explicit currency symbols but with typical price format (e.g., 123.45)
    # This one needs to be more careful to avoid matching any random number.
    # We make the decimal part with 2 digits more indicative of a price.
    pattern3 = r'(\b\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d{2})\b)' # Requires 2 decimal places
    # Pattern for amounts that are just numbers, could be prices if context is right (e.g. 123, 1500)
    # This is more general and might pick up non-prices.
    pattern4 = r'(\b\d+\b)'


    found_prices = []
    # Apply patterns in order of specificity
    # We use finditer to get match objects, allowing access to captured groups if needed later for structured data
    
    # More complex combined pattern:
    # Looks for optional symbol, then number, then optional different symbol (less common but possible)
    # Or number followed by symbol.
    # The core is \d{1,3}(?:[,\s]\d{3})*(?:[.,]\d{1,2})? which matches numbers like 1,234,567.89 or 1234.56 or 1 234
    # Currency symbols: $, €, £, грн, UAH, ₴
    # The regex tries to capture the value and optionally the currency symbol.
    
    # Regex Explanation:
    # (?:[\$€£грнUAH₴]\s*)? - Optional currency symbol at the beginning, followed by optional space. Non-capturing group.
    # (\d{1,3}(?:[,\s]\d{3})*(?:[.,]\d{1,2})?) - The number part. Capturing group 1.
    #   \d{1,3} - Start with 1-3 digits.
    #   (?:[,\s]\d{3})* - Optionally, groups of (comma or space followed by 3 digits) - for thousands separators.
    #   (?:[.,]\d{1,2})? - Optional decimal part (dot or comma followed by 1 or 2 digits).
    # (?:s*[\$€£грнUAH₴])? - Optional currency symbol at the end, preceded by optional space. Non-capturing group.
    
    # This combined regex attempts to capture the numeric part and identify surrounding currency symbols.
    # For simplicity, we'll just extract the full match string for now.
    # A more robust solution would involve capturing value and currency separately.

    # Regex focusing on capturing the price-like number, with optional symbols on either side.
    # It prioritizes symbol-number or number-symbol combinations.
    # \b is for word boundaries to avoid matching parts of larger numbers/strings.
    
    # Main pattern:
    # It looks for (optional symbol then number) OR (number then optional symbol) OR (number with decimal places)
    # This is still a simplified approach. True price extraction often needs NLP context.
    
    # Let's try a list of patterns and combine their findings.
    # Order matters: more specific patterns first.
    
    # Pattern: CurrencySymbol<optional_space>Digits<optional_decimals>
    # Example: $123.45, € 500, грн1000,20
    regex1 = r'[\$€£грнUAH₴]\s*\d+(?:[.,]\d{1,2})?'
    
    # Pattern: Digits<optional_decimals><optional_space>CurrencySymbol
    # Example: 123.45$, 500 €, 1000,20грн
    regex2 = r'\d+(?:[.,]\d{1,2})?\s*[\$€£грнUAH₴]'
    
    # Pattern: Digits<mandatory_decimals_2_places> (often indicates price even without symbol)
    # Example: 123.45, 1000,00
    regex3 = r'\b\d+[.,]\d{2}\b'

    # Pattern: Digits (more generic, might be a price, e.g., in a column of prices)
    # Example: 123, 5000. This is broad.
    # To make it slightly more price-like, let's assume it could be an integer price.
    # We'll avoid matching single digits or very small numbers unless they have decimals or symbols.
    regex4 = r'\b\d{2,}\b' # Matches numbers with 2 or more digits

    potential_matches = []
    for match in re.finditer(regex1, text_content):
        potential_matches.append(match.group(0))
    
    for match in re.finditer(regex2, text_content):
        potential_matches.append(match.group(0))
        
    # For regex3 and regex4, we need to be careful not to add substrings of already found matches from regex1 & regex2
    current_text_for_regex3_4 = text_content
    for found_price_str in potential_matches:
        current_text_for_regex3_4 = current_text_for_regex3_4.replace(found_price_str, "MATCHED", 1) # Replace first occurence

    for match in re.finditer(regex3, current_text_for_regex3_4):
        potential_matches.append(match.group(0))
        current_text_for_regex3_4 = current_text_for_regex3_4.replace(match.group(0), "MATCHED", 1)

    for match in re.finditer(regex4, current_text_for_regex3_4):
        # Avoid adding numbers that are part of years or other non-price contexts if possible.
        # This is very hard with regex alone. For now, accept if it's 2+ digits.
        num_str = match.group(0)
        if len(num_str) >=2 : # Basic filter: at least 2 digits for standalone numbers
             potential_matches.append(num_str)

    # Remove duplicates while preserving order (if important, though not strictly for this list)
    # and filter out any "MATCHED" strings if they somehow got in.
    final_prices = []
    seen = set()
    for item in potential_matches:
        if item != "MATCHED" and item not in seen:
            final_prices.append(item)
            seen.add(item)
            
    return final_prices

import pytesseract
from PIL import Image
import io

def extract_text_from_region_ocr(pdf_path, page_number, x1, y1, x2, y2, language='eng'):
    """
    Extracts text from a specific region of a PDF page using OCR.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int): 0-indexed page number.
        x1, y1, x2, y2 (float): Coordinates of the bounding box.
        language (str): Language code for Tesseract (e.g., 'eng', 'ukr', 'ita').

    Returns:
        str: Extracted text from the region, or None if an error occurs.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF {pdf_path}: {e}")
        return None

    if page_number < 0 or page_number >= len(doc):
        print(f"Error: Page number {page_number} is out of range for PDF {pdf_path} (pages: {len(doc)}).")
        if doc: doc.close()
        return None
    
    page = doc.load_page(page_number)
    
    # Define the clipping rectangle
    # PyMuPDF uses (x0, y0, x1, y1) where (x0,y0) is top-left and (x1,y1) is bottom-right
    clip_rect = fitz.Rect(float(x1), float(y1), float(x2), float(y2))

    if clip_rect.is_empty or clip_rect.width <= 0 or clip_rect.height <= 0:
        print(f"Error: Invalid or zero-area rectangle defined by ({x1},{y1},{x2},{y2}).")
        doc.close()
        return None

    try:
        # Get pixmap of the clipped region
        # zoom factor can be increased to get higher resolution image for OCR
        zoom = 2.0 # Increase zoom for better OCR; adjust as needed
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=clip_rect)
        
        if pix.width == 0 or pix.height == 0:
            print(f"Error: Pixmap for region ({x1},{y1},{x2},{y2}) on page {page_number} is empty.")
            doc.close()
            return None

        # Convert pixmap to PIL Image
        img_data = pix.tobytes("png") # Get bytes in PNG format
        image = Image.open(io.BytesIO(img_data))
        
        # Perform OCR
        ocr_text = pytesseract.image_to_string(image, lang=language)
        
        doc.close()
        return ocr_text.strip()
        
    except pytesseract.TesseractNotFoundError:
        print("Error: Tesseract is not installed or not found in your PATH.")
        if doc: doc.close()
        return None
    except RuntimeError as e: # Catch Tesseract runtime errors (e.g. lang data not found)
        print(f"Error during Tesseract OCR processing: {e}")
        if doc: doc.close()
        return None
    except Exception as e:
        print(f"An unexpected error occurred during OCR for region: {e}")
        if doc: doc.close()
        return None

def get_text_style_in_region(pdf_path, page_number, x1, y1, x2, y2):
    """
    Analyzes the text style (font, size, color, flags) in a specific region of a PDF page.

    Args:
        pdf_path (str): Path to the PDF file.
        page_number (int): 0-indexed page number.
        x1, y1, x2, y2 (float): Coordinates of the bounding box.

    Returns:
        dict: A dictionary containing style information for the first text span
              found primarily within the region, or None if no text is found or an error occurs.
              Example: {"font": "Arial", "size": 12.0, "color": "#000000", 
                        "bold": False, "italic": False, "text": "sample text"}
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    doc = None  # Initialize doc to None for broader scope in finally block
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF {pdf_path}: {e}")
        return None

    try:
        if page_number < 0 or page_number >= len(doc):
            print(f"Error: Page number {page_number} is out of range for PDF {pdf_path} (pages: {len(doc)}).")
            return None
        
        page = doc.load_page(page_number)
        
        clip_rect = fitz.Rect(float(x1), float(y1), float(x2), float(y2))

        if clip_rect.is_empty or clip_rect.width <= 0 or clip_rect.height <= 0:
            print(f"Error: Invalid or zero-area rectangle defined by ({x1},{y1},{x2},{y2}).")
            return None

        # get_text("dict") or "rawdict" provides detailed information including spans
        text_dict = page.get_text("dict", clip=clip_rect)
        
        extracted_text_in_region = ""
        
        for block in text_dict.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    # Heuristic: Check if a significant portion of the span is within the clip_rect
                    # For simplicity, if get_text with clip is used, we assume spans returned are relevant.
                    # A more precise check would involve comparing span bbox with clip_rect.
                    
                    # Extract style from the first relevant span
                    font_name = span.get("font", "Unknown")
                    font_size = round(span.get("size", 0.0), 2)
                    
                    # Color is an integer, convert to hex
                    color_int = span.get("color", 0) # Default to black
                    color_hex = f"#{color_int:06x}" if isinstance(color_int, int) else "#000000"

                    flags = span.get("flags", 0)
                    is_bold = bool(flags & (1 << 4)) # Bit 4 for bold (font-specific, but common)
                                                 # PyMuPDF docs: 2 for italic, 16 for bold (supersedes 2^4)
                                                 # Let's check common flags: is_bold = font_name.lower().contains("bold") or (flags & 16)
                                                 # A common flag for bold is (flags & 2**4) or if the font name implies bold.
                                                 # PyMuPDF's documentation should be consulted for the exact meaning of flags.
                                                 # From common observations with PDF text:
                                                 # flags & 1: superscript
                                                 # flags & 2: italic
                                                 # flags & 4: serifed (vs sans-serif)
                                                 # flags & 16: bold (more reliable than (1<<4) for some fonts)
                    
                    is_italic = bool(flags & 2) 
                    # More robust bold check:
                    # Some fonts have "Bold" in their name. Or use flags & 16.
                    # A simple check for boldness in font name:
                    if not is_bold and "bold" in font_name.lower():
                        is_bold = True
                    elif flags & 16: # Flag 16 is often used for bold
                        is_bold = True

                    extracted_text_in_region += span.get("text", "") + " "

                    # Return style of the first span found
                    return {
                        "font": font_name,
                        "size": font_size,
                        "color": color_hex,
                        "bold": is_bold,
                        "italic": is_italic,
                        "text": span.get("text", "").strip() # Return only the text of this specific span
                    }
        
        # If no spans were found in the iteration
        if not extracted_text_in_region: # Check if any text was aggregated
             return {"font": "Unknown", "size": 0.0, "color": "#000000", 
                     "bold": False, "italic": False, "text": "", "message": "No text found in the specified region."}
        
        # This part might not be reached if we return from the first span
        return {"font": "Unknown", "size": 0.0, "color": "#000000", 
                "bold": False, "italic": False, "text": extracted_text_in_region.strip(), 
                "message": "Could not determine specific style for aggregated text, returning default."}

    except Exception as e:
        print(f"An unexpected error occurred during style analysis for region: {e}")
        return None
    finally:
        if doc:
            doc.close()

# Helper function to convert hex color to RGB tuple for PyMuPDF
def hex_to_rgb(hex_color):
    """Converts a hex color string (e.g., "#RRGGBB") to an RGB tuple (r, g, b) scaled 0-1."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return (0, 0, 0) # Default to black if format is wrong
    try:
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b)
    except ValueError:
        return (0, 0, 0) # Default to black on error

# Helper function to select a PyMuPDF base14 font based on name and style
def get_pymupdf_font_name(font_name, is_bold, is_italic):
    """Attempts to map a font name and style to a PyMuPDF base14 font name."""
    name_lower = font_name.lower()
    
    # Base font selection (heuristic)
    if "times" in name_lower:
        base = "ti"
    elif "helvetica" in name_lower or "arial" in name_lower or "sans-serif" in name_lower:
        base = "he"
    elif "courier" in name_lower or "monospace" in name_lower:
        base = "co"
    else:
        base = "he" # Default to Helvetica

    # Style suffix
    if is_bold and is_italic:
        style_suffix = "bi" # Bold Italic
    elif is_bold:
        style_suffix = "bo" # Bold
    elif is_italic:
        style_suffix = "it" # Italic
    else:
        style_suffix = "no" # Normal (Roman)
        
    # PyMuPDF font names: ti,tii,tibo,tibi / he,hei,hebo,hebi / co,coi,cobo,cobi
    # For Symbol (sy) and ZapfDingbats (za) direct mapping is simpler if needed.
    # This mapping is very basic.
    if base == "ti": # Times
        return {"no": "Times-Roman", "it": "Times-Italic", "bo": "Times-Bold", "bi": "Times-BoldItalic"}.get(style_suffix)
    elif base == "he": # Helvetica
        return {"no": "Helvetica", "it": "Helvetica-Oblique", "bo": "Helvetica-Bold", "bi": "Helvetica-BoldOblique"}.get(style_suffix)
    elif base == "co": # Courier
        return {"no": "Courier", "it": "Courier-Oblique", "bo": "Courier-Bold", "bi": "Courier-BoldOblique"}.get(style_suffix)
    
    return "Helvetica" # Fallback

def replace_text_in_pdf_region(pdf_path, page_number, x1, y1, x2, y2, new_text, 
                               font_name, font_size, text_color_hex, is_bold, is_italic, 
                               output_pdf_path):
    """
    Replaces text in a specific region of a PDF page by redacting the old content
    and inserting new text with specified style.

    Args:
        pdf_path (str): Path to the original PDF file.
        page_number (int): 0-indexed page number.
        x1, y1, x2, y2 (float): Coordinates of the bounding box for redaction and text insertion.
        new_text (str): The new text to insert.
        font_name (str): Name of the font (e.g., "Arial", "Helvetica").
        font_size (float): Font size.
        text_color_hex (str): Text color in hex format (e.g., "#RRGGBB").
        is_bold (bool): Whether the text should be bold.
        is_italic (bool): Whether the text should be italic.
        output_pdf_path (str): Path to save the modified PDF.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return False

    doc = None
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening PDF {pdf_path}: {e}")
        return False

    try:
        if page_number < 0 or page_number >= len(doc):
            print(f"Error: Page number {page_number} is out of range for PDF (pages: {len(doc)}).")
            return False
        
        page = doc.load_page(page_number)
        
        # 1. Redact/Remove Old Text
        # Define the redaction rectangle
        redact_rect = fitz.Rect(float(x1), float(y1), float(x2), float(y2))
        if redact_rect.is_empty or redact_rect.width <= 0 or redact_rect.height <= 0:
            print(f"Error: Invalid or zero-area redaction rectangle defined by ({x1},{y1},{x2},{y2}).")
            return False
        
        # Add redaction annotation with white fill (assuming white background)
        # Note: Redaction fill color might need to match actual page background if not white.
        page.add_redact_annot(redact_rect, fill=(1, 1, 1), text="") 
        page.apply_redactions()

        # 2. Add New Text
        # Convert hex color to RGB tuple (scaled 0-1)
        text_color_rgb = hex_to_rgb(text_color_hex)
        
        # Attempt to map font name and style to a PyMuPDF base14 font
        pymupdf_fontname = get_pymupdf_font_name(font_name, is_bold, is_italic)
        if not pymupdf_fontname: # Fallback if mapping fails (shouldn't with current get_pymupdf_font_name)
            pymupdf_fontname = "Helvetica" 
            print(f"Warning: Could not map font '{font_name}'. Defaulting to '{pymupdf_fontname}'.")

        # Positioning for insert_text:
        # PyMuPDF's insert_text uses the bottom-left of the *first character*.
        # We need to estimate a suitable baseline. A common heuristic is y1 + fontsize.
        # This will likely require significant fine-tuning.
        # For textbox, y1 is the top of the box.
        # Let's try to place it slightly below y1.
        insertion_point = fitz.Point(float(x1), float(y1) + float(font_size) * 0.9) # Adjust y for baseline

        # Using insert_textbox for potentially better alignment within the defined box
        # Define the rectangle for the new text. This should ideally be the same as redact_rect or derived.
        text_insert_rect = fitz.Rect(float(x1), float(y1), float(x2), float(y2))

        # insert_textbox arguments:
        # rect, buffer, fontname, fontsize, color, align, ...
        # For alignment: 0 (left), 1 (center), 2 (right), 3 (justify)
        # We'll default to left alignment for now.
        # Note: insert_textbox will wrap text. If new_text is too long for the box, it might not look good.
        
        # Simpler approach first: insert_text (might be harder to align perfectly in box)
        # page.insert_text(insertion_point,
        #                  new_text,
        #                  fontname=pymupdf_fontname,
        #                  fontsize=float(font_size),
        #                  color=text_color_rgb,
        #                  # rotate=0, morph=None, render_mode=0 (fill text)
        #                 )

        # Using insert_textbox - often better for fitting text into a region
        res = page.insert_textbox(text_insert_rect,
                                  new_text,
                                  fontname=pymupdf_fontname,
                                  fontsize=float(font_size),
                                  color=text_color_rgb,
                                  align=0) # 0 for left, 1 center, 2 right, 3 justify
        
        if res < 0:
            print(f"Warning: Textbox overflow for document {pdf_path}, page {page_number}. Text may not be fully visible. Overflow amount: {res}")


        # 3. Save the modified document
        # Ensure the output directory exists
        output_dir = os.path.dirname(output_pdf_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        doc.save(output_pdf_path, garbage=3, deflate=True, clean=True) # Use clean for smaller files
        return True

    except Exception as e:
        print(f"An unexpected error occurred during PDF text replacement: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if doc:
            doc.close()

# Helper function to parse price string
def parse_price_string(price_text):
    """Converts a price string (e.g., "$1,234.56", "€123,45") to a float."""
    if not price_text:
        return 0.0
    
    # Remove common currency symbols and whitespace
    cleaned_text = re.sub(r'[\$€£грнUAH₴\s]', '', price_text)
    
    # Standardize decimal separator to '.'
    if ',' in cleaned_text and '.' in cleaned_text: # e.g. 1.234,56
        cleaned_text = cleaned_text.replace('.', '') # Remove thousands separator
        cleaned_text = cleaned_text.replace(',', '.')
    elif ',' in cleaned_text: # e.g. 123,45
        cleaned_text = cleaned_text.replace(',', '.')
        
    try:
        return float(cleaned_text)
    except ValueError:
        print(f"Warning: Could not parse price string '{price_text}' to float. Got '{cleaned_text}'.")
        return 0.0 # Or raise an error

# Helper function to format new price (basic implementation)
def format_new_price(original_price_text, new_value_float):
    """
    Formats a new float price value based on the characteristics of the original price string.
    (e.g., currency symbol, decimal places). This is a basic heuristic.
    """
    # Identify currency symbol from original
    currency_symbol_match = re.match(r'([\$€£грнUAH₴])', original_price_text)
    currency_symbol = currency_symbol_match.group(1) if currency_symbol_match else ""
    
    # Identify decimal places from original (if any)
    if ',' in original_price_text and '.' not in original_price_text: # european format e.g. 123,45
        num_decimals = len(original_price_text.split(',')[-1]) if ',' in original_price_text else 0
        decimal_separator = ','
    elif '.' in original_price_text: # US/UK format e.g. 123.45
        num_decimals = len(original_price_text.split('.')[-1]) if '.' in original_price_text else 0
        decimal_separator = '.'
    else: # Integer price
        num_decimals = 0
        decimal_separator = '.' # Default if no decimal found

    # Ensure num_decimals is typically 0 or 2 for prices, but respect original if different
    if num_decimals > 2 and original_price_text.replace(',','').replace('.','').isdigit(): # if it's just a number 1.234
        if decimal_separator == '.': # 1.234 could be 1234
             if len(original_price_text.split('.')[-1]) == 3 : num_decimals =0 # e.g. 1.234 is 1234 not 1.23
        elif decimal_separator == ',': # 1,234 could be 1234
             if len(original_price_text.split(',')[-1]) == 3 : num_decimals =0


    formatted_new_value = f"{new_value_float:.{num_decimals}f}"
    
    if decimal_separator == ',':
        formatted_new_value = formatted_new_value.replace('.', ',')
        
    return f"{currency_symbol}{formatted_new_value}"
