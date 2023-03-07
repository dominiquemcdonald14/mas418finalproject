# Import necessary libraries
# standard libraries
import argparse
import json
import os
import sys
from os.path import exists
from datetime import datetime
from time import time
import csv
# 3rd-party libraries
import enlighten

# custom functions from packaged folder
from packaged.common import requestAndParse
from packaged.page import extract_maximums, extract_listings
from packaged.listing import extract_listing

###################################
class glassdoor_scraper():

    def __init__(self, configfile, baseurl, targetnum) -> None:

        # load first
        base_url, target_num = self.load_configs(path=configfile)
        # overwrite those that are not none
        if type(baseurl) != type(None):
            base_url = baseurl
            print("Using supplied baseurl")
        if type(targetnum) != type(None):
            target_num = targetnum
            print("Using supplied targetnum")
        print(configfile, baseurl, targetnum)
        
        if not os.path.exists('output'):
            os.makedirs('output')
        now = datetime.now() # current date and time
        output_fileName = "./output/output_" + ".csv" #+ now.strftime("%d-%m-%Y")
        csv_header = [("companyName", "company_starRating", "company_offeredRole", "company_roleLocation", "company_salary" , "listing_jobDesc", "requested_url")]
        self.fileWriter(listOfTuples=csv_header, output_fileName=output_fileName)
        
        if os.path.exists('output'):
            output_fileName = "./output/output_" + ".csv"
            os.remove(output_fileName)
        
         # initialises output directory and file
        if not os.path.exists('output'):
            os.makedirs('output')
        now = datetime.now() # current date and time
        output_fileName = "./output/output_" + ".csv" #+ now.strftime("%d-%m-%Y") I changed the name of our output
        csv_header = [("companyName", "company_starRating", "company_offeredRole", "company_roleLocation", "company_salary" , "listing_jobDesc", "requested_url")]
        self.fileWriter(listOfTuples=csv_header, output_fileName=output_fileName) #change header here

        maxJobs, maxPages = extract_maximums(base_url)
        # print("[INFO] Maximum number of jobs in range: {}, number of pages in range: {}".format(maxJobs, maxPages))
        if (target_num >= maxJobs):
            print("[ERROR] Target number larger than maximum number of jobs. Exiting program...\n")
            os._exit(0)

        # initialises enlighten_manager
        enlighten_manager = enlighten.get_manager()
        progress_outer = enlighten_manager.counter(total=target_num, desc="Total progress", unit="listings", color="green", leave=False)
        # initialise variables
        page_index = 1
        total_listingCount = 0

        # initialises prev_url as base_url
        prev_url = base_url

        while total_listingCount <= target_num:
            # clean up buffer
            list_returnedTuple = []

            new_url = self.update_url(prev_url, page_index)
            page_soup,_ = requestAndParse(new_url)
            listings_set, jobCount = extract_listings(page_soup)
            progress_inner = enlighten_manager.counter(total=len(listings_set), desc="Listings scraped from page", unit="listings", color="blue", leave=False)

            print("\n[INFO] Processing page index {}: {}".format(page_index, new_url))
            print("[INFO] Found {} links in page index {}".format(jobCount, page_index))

            for listing_url in listings_set:

                # to implement cache here

                returned_tuple = extract_listing(listing_url)
                list_returnedTuple.append(returned_tuple)
                # print(returned_tuple)
                progress_inner.update()

            progress_inner.close()

            self.fileWriter(listOfTuples=list_returnedTuple, output_fileName=output_fileName)

            # done with page, moving onto next page
            total_listingCount = total_listingCount + jobCount
            print("[INFO] Finished processing page index {}; Total number of jobs processed: {}".format(page_index, total_listingCount))
            page_index = page_index + 1
            prev_url = new_url
            progress_outer.update(jobCount)

        progress_outer.close()

            # loads user defined parameters
    def load_configs(self, path):
        with open(path) as config_file:
            configurations = json.load(config_file)

        base_url = configurations['base_url']
        target_num = int(configurations["target_num"])
        return base_url, target_num


    # appends list of tuples in specified output csv file
    # a tuple is written as a single row in csv file 
    def fileWriter(self, listOfTuples, output_fileName):
        with open(output_fileName,'a', newline='') as out:
            csv_out=csv.writer(out)
            for row_tuple in listOfTuples:
                try:
                    csv_out.writerow(row_tuple)
                    # can also do csv_out.writerows(data) instead of the for loop
                except Exception as e:
                    print("[WARN] In filewriter: {}".format(e))


    # updates url according to the page_index desired
    def update_url(self, prev_url, page_index):
        if page_index == 1:
            prev_substring = ".htm"
            new_substring = "_IP" + str(page_index) + ".htm"
        else:
            prev_substring = "_IP" + str(page_index - 1) + ".htm"
            new_substring = "_IP" + str(page_index) + ".htm"

        new_url = prev_url.replace(prev_substring, new_substring)
        return new_url

###################################

#run the scraper  
glassdoor_scraper(configfile = "config.json",baseurl = "https://www.glassdoor.com/Job/data-scientist-jobs-SRCH_KO0,14.htm?context=Jobs&clickSource=searchBox", targetnum = 900)
#request to scrape the maximum amount of jobs listed on glassdoor website = 900 (30 listings per page, 30 pages total)
