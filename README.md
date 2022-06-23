# sora-webapp

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/yongdetan/sora-webapp/sora.py)

![image](https://user-images.githubusercontent.com/61530179/175294332-c23d21e7-dfa2-4978-83c2-5168ffd1eb2d.png)


# Description 

This is a web application that allows you to retrieve, filter, and visualize the Singapore Overnight Rate Average (SORA) interest rate. 

All data shown in this web application is directly extracted from [MAS' API for Domestic Interest Rates](https://secure.mas.gov.sg/api/APIDESCPAGE.ASPX?RESOURCE_ID=9a0bf149-308c-4bd2-832d-76c8e6cb47ed).

### More information about SORA

- What is SORA? - SORA is the volume-weighted average rate of actual borrowing transactions in the unsecured overnight interbank SGD cash market in Singapore.

- What is the fuss over SORA? - It is the new benchmark interest rate introduced by the MAS that will replace the Singapore Interbank Offer Rate (SIBOR) and Swap Offer Rate (SOR) when they are phased out by 2024.


# Purpose

Currently, majority of home loan interest rates are pegged to SIBOR. However, as mentioned, SIBOR is going to be phased out by 2024 and replaced by SORA. This means that in the future, most of the home loan interest rates in Singapore will be based on the SORA rate. 

As such, it is important for people, especially those who would like to purchase a home, to be able to analyse past and current SORA rates in addition to research they have done on the current state of the economy before making their decision to take up a home loan.


# Libraries used

- Streamlit
- SQLite3
- requests
- pandas
- altair
- math

#
