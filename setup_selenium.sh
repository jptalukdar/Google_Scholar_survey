curl -L -o driver.zip https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-win64.zip
unzip driver.zip
mkdir -p driver
mv geckodriver.exe driver

curl -L -o chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/133.0.6943.53/win64/chromedriver-win64.zip
unzip chromedriver.zip
mv chromedriver-win64/chromedriver.exe driver