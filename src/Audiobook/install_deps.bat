@echo off
cd /d "C:\Users\Minor Bonilla G\Desktop\PHP\NEVEM_STUDIO"
call venv\Scripts\activate.bat
pip install ebooklib PyMuPDF pyttsx3 flask qrcode comtypes lxml edge-tts
pip list
pause
