@echo off
echo =======================================================
echo GitHub Par Images Upload (Push) Ho Rahi Hain...
echo =======================================================
echo.
cd /d "E:\Paresh\Auto Post\Auto-Insta-Pooja"

echo 1. Nayi aur cropped images ko Add kar rahe hain...
git add images/
git commit -m "Move web images to images folder and crop to 4:5"

echo.
echo 2. Puraani root images delete kar rahe hain...
git rm 179*.png 2>nul
git commit -m "Remove loose root images" 2>nul

echo.
echo 3. GitHub par Push kar rahe hain (Please login if prompted)...
git push origin master --force

echo.
echo =======================================================
echo Done! Saari images GitHub par update ho gayi hain!
echo =======================================================
pause
