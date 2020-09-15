# eBay Iphone 7 Price Prediction Using Regression
The goal of this project is to predcit the price of 

I got the idea to try and use machine learning to predict ebay price items after seeing @NathanZorndorf repo [here](https://github.com/NathanZorndorf/ebay-price-predictor) where he did something similar.
# Web Scraping
To get the required information from eBay I used gthe eBay API along with the python wrapper [link](https://github.com/timotheus/ebaysdk-python). eBay only lets you see information for items that were listed in the last 90 days, so I collected data for about 21,000 completed listings. I used the keyword 'iPhone 7' and set the categoryId equal to 9355 (Cell Phones & Smartphones). I then saved all of the data in a postgres database.
![](Images/iphonedb.PNG)
# Data Cleaning
I used Pandas for the data cleaning in jupyter notebooks.
# Data pre-processing
Titles ect.
# Initial Modeling

# Hyperparameter optimization
# Conclusion
