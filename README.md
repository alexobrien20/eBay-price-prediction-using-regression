# eBay Iphone 7 Price Prediction Using Regression
It's difficult to tell when using eBay whether the item you are bidding on is overpriced, underpriced or about right. Wouldn't it be easier if there was a better way to find out what price an item will sell for? That way you don't over pay for an item, waste time bidding for an item that wil eventually exceed your price range and can identify underpriced items.

This project aims to solve that problem. The goal of this project is to use regression to predict the price of eBay items (specifically Iphone 7s) so that you can know instantly what price an item will sell for, making the whole eBay process easier.

I got the idea to try and use machine learning to predict ebay price items after seeing @NathanZorndorf repo [here](https://github.com/NathanZorndorf/ebay-price-predictor) where he did something similar.
# Web Scraping
To get the required information from eBay I used gthe eBay API along with the python wrapper [link](https://github.com/timotheus/ebaysdk-python). eBay only lets you see information for items that were listed in the last 90 days, so I collected data for about 21,000 completed listings. I used the keyword 'iPhone 7' and set the categoryId equal to 9355 (Cell Phones & Smartphones). I then saved all of the data in a postgres database.

![](Images/iphonedb.PNG)

I collected all of the standard information for each item using the Ebay Finding API, such as the title, postage price, final price, etc. Then I used the eBay Trading API to get the item specifics, for each itemId, such as 
* Colour
* Model
* Storage
* Network

My code limits the user to making a limited number of calls for a 24 hour period (10,000 for Finding and 5,000 for Trading) but if you were to collect data on a larger scale you can apply to extend this limit on the eBay API website. [API call limits](https://developer.ebay.com/support/api-call-limits)

# Data Cleaning
For the data cleaning I used the python module Pandas. 
![](Images/pandasdb.PNG)

Out of a total of 380 columns, 305 were missing more than 50 of there data, I decided to drop the columns that had more than 50% of there data missing. I then filled in the remaining missing data points with the keyword 'None'. I also tried to remove data entires that had words unrelated to the keyword 'Iphone 7' for example if the item had the words 'case' or 'screen protector' they were dropped from the database. After all of the missing values were fixed I exported the data table to a pickle.

# Data pre-processing
I thought that if a title had the word 'Plus' (relating to an Iphone 7 plus) in the title it would sell for more, but if the seller hadn't specifically specified that it was a Iphone 7 Plus in the item specifics the model might not make use of that fact. So I used Sklearn's TfidfVectorizer and CountVectorizer on the item title and description. I then used the top 100 words to create an extra 200 columns in the database to signify if a word appear in the title or descipriton e.g. 'Plus in title'. I then calcualted the correlation between each new cateogry and the price then I kept the columns that showed any sort of correlation. Using this technique I managed to add an extra 21 columns. 
e.g.

# Initial Modeling


# Hyperparameter optimization
# Conclusion
