#import stuff
import keyboard # type: ignore
import time
import pyautogui # type: ignore
import glob
import os
import sys
import pytesseract # type: ignore
from PIL import Image, ImageEnhance, ImageOps # type: ignore
import numpy as np # type: ignore
import google.genai as genai

#variables and setup
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
screenshot_folder = "screenshots"
os.makedirs(screenshot_folder, exist_ok=True)
l = 0
timestamp = 0

client  = genai.Client(api_key="get it yourself")


#resolution adaption
regxstart = 721
regystart = 164
regxsize = 239
regysize = 785
res = input("Please enter the vertical resolution of your screen: ")
scaleres = int(res) / 1080
print(scaleres)
reg = (int(regxstart * scaleres),
       int(regystart * scaleres),
       int((regxsize * scaleres) + (regxstart * scaleres)),
       int((regysize * scaleres) + (regystart * scaleres)))

reg2 = (int( 960 * scaleres),
       int( 154 * scaleres),
       int(( 242 * scaleres) + ( 960 * scaleres)),
       int(( 783 * scaleres) + ( 154 * scaleres)))

#function to take screenshot (with timestamp)
def take_screenshot(usereg): 
    global timestamp
    timestamp += 1
    filename = f"screenshot_{timestamp}.png"
    cropped_filename = f"cropped_screenshot_{timestamp}.png"
    processed_filename = f"processed_screenshot_{timestamp}.png"
    filepath = os.path.join(screenshot_folder, filename)
    cropped_filepath = os.path.join(screenshot_folder, cropped_filename)
    processed_filepath = os.path.join(screenshot_folder, processed_filename)

    try:
        # Take full screenshot
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        print(f"Screenshot saved to: {filepath}")
        
        # Crop the screenshot using the specified region
        cropped_screenshot = screenshot.crop(usereg)
        cropped_screenshot.save(cropped_filepath)
        print(f"Cropped screenshot saved to: {cropped_filepath}")

        # Process the cropped screenshot
        img_array = np.array(cropped_screenshot)
        processed_img = Image.fromarray(img_array).convert('L')
        processed_img = ImageEnhance.Contrast(processed_img).enhance(3.0)
        processed_img = processed_img.point(lambda x: 0 if x < 150 else 255, '1')
        processed_img = ImageOps.invert(processed_img.convert('L'))
        processed_img.save(processed_filepath)
        print(f"Processed screenshot saved to: {processed_filepath}")
        
        # Extract text using custom OCR configuration
        custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
        extracted_text = pytesseract.image_to_string(
            processed_img, 
            lang='eng+ger+fra',
            config=custom_config
        )
        
        #extracted_text = extracted_text.replace(' ', '\n')

        text_filename = f"text_{timestamp}.txt"
        text_filepath = os.path.join(screenshot_folder, text_filename)
        
        # Save extracted text to a file
        with open(text_filepath, 'w', encoding='utf-8') as text_file:
            text_file.write(extracted_text)
        
        print(f"Extracted text saved to: {text_filepath}")
        
    except Exception as e:
        print(f"Error taking screenshot or extracting text: {e}")

def exit_program():
    print("Exiting...")
    keyboard.unhook_all()
    sys.exit()

def regloop():
    # Take screenshot of first region
    take_screenshot(usereg=reg)
    time.sleep(0.5)
    
    # Take screenshot of second region
    take_screenshot(usereg=reg2)
    time.sleep(0.5)

    process_screenshots()
def process_screenshots():
    """Process the most recent pair of screenshots to extract and analyze data."""
    global timestamp
    text_file1 = os.path.join(screenshot_folder, f"text_{timestamp-1}.txt")
    text_file2 = os.path.join(screenshot_folder, f"text_{timestamp}.txt")
    try:
        # Read the text from both files
        with open(text_file1, 'r', encoding='utf-8') as f1, open(text_file2, 'r', encoding='utf-8') as f2:
            text1 = f1.read().strip()
            text2 = f2.read().strip()
        
        # Combine and analyze the data
        combined_data = f"\n{text1}\n{text2}"
        analysis_filename = f"analysis_{timestamp}.txt"
        os.makedirs('textfiles', exist_ok=True)
        analysis_filepath = os.path.join('textfiles', analysis_filename)
        with open(analysis_filepath, 'w', encoding='utf-8') as f:
            f.write(combined_data)
        print(f"Data analysis saved to: {analysis_filepath}")
    except Exception as e:
        print(f"Error processing screenshots: {e}")
        

#sending api request + files
def get_result():
    file_paths = glob.glob("textfiles/*.txt")
    uploaded_files = []
    for path in file_paths:
        print(f"Uploading {path}...")
        file_ref = client.files.upload(file=path)
        uploaded_files.append(file_ref)
    response = client.models.generate_content(
    model="gemini-2.5-flash", contents=["!RETURN ONLY THE FINAL LIST WRITE NOTHING ELSE! Truncate the names in the files. Make them readable, warning names can differ from file to file, Repeat the names in the files, print each one out. If name x was in the list more than 3 times it gets printed x-2(x is amount of same names in file) often.",
                                         uploaded_files]
    )

    print("=" * 40)
    print(response.text)
    print("=" * 40)

    # To delete all files after getting your answer:
    for f in uploaded_files:
        client.files.delete(name=f.name)
        print(f"Deleted temp file")

#main loop and listener
keyboard.add_hotkey('alt+ctrl+3', get_result)
keyboard.add_hotkey('alt+ctrl+1', regloop)
keyboard.add_hotkey('alt+ctrl+esc', exit_program)

try:
    print("Giveaway tracker running. Press Alt+Ctrl+1 to take a screenshot, Alt+Ctrl+Esc to exit.")
    print("Text extraction with psytesseract is enabled.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Program interrupted by user.")
    exit_program()  # Call exit_program if interrupted
