curl -L -o driver.zip https://github.com/mozilla/geckodriver/releases/download/v0.35.0/geckodriver-v0.35.0-win64.zip
tar -xf driver.zip
if not exist driver mkdir driver
move geckodriver.exe driver

curl -L -o chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/133.0.6943.53/win64/chromedriver-win64.zip
tar -xf chromedriver.zip
move chromedriver-win64\chromedriver.exe driver