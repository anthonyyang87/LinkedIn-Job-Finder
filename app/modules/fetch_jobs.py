#use linkedIn API to fetch jobs
import json
import os
from dotenv import load_dotenv
from linkedin_api import Linkedin
import configparser


#read linkedin credentials from environment variables
load_dotenv()

#Accessing the environment variables
EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")
PROFILE_ID = os.getenv("LINKEDIN_PROFILE_ID")

linkedin = Linkedin(EMAIL, PASSWORD)


##########Job Parameters##########

#Read from ini file
config = configparser.ConfigParser()
config.read('../config.ini')


KEYWORDS = config['JOB_PARAMETERS']['keywords']
LOCATION_NAME = config['JOB_PARAMETERS']['location_name']
LISTED_AT = config['JOB_PARAMETERS']['listed_at']
COMPANIES_LITERAL = config['JOB_PARAMETERS']['companies_literal']

#Data Export
jobs_file_path = "../data/jobs/jobs.json"
companies_file_path = "../data/companies/"

#utility functions
def write_to_file(data, filename):
    #write data to a file
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Data written to {filename}")

#LinkedIn API functions
def get_company_urn_id(name):
    company = linkedin.get_company(name)
   
    # example "entityUrn": "urn:li:fs_normalized_company:3608",

    entityUrn = company['entityUrn']
    company_id = entityUrn.split(':')[-1]
    
    return company_id

def get_multiple_companies_urn_id(companies: list):
    companies_urn_id = []
    for company in companies:
        companies_urn_id.append(get_company_urn_id(company))
    return companies_urn_id

def get_job(job_id):
    job = linkedin.get_job(job_id)
    return job

def get_multiple_jobs(job_ids: list):
    jobs = []
    for job_id in job_ids:
        jobs.append(get_job(job_id))
    return jobs

def save_job_to_file(job: dict, filename: str):
    write_to_file(job, filename)

def extract_job_ids(jobs: list):
    job_ids = []
    for job in jobs:
        job_id = job['entityUrn'].split(':')[-1]
        job_ids.append(job_id)

    return job_ids
        
def fetch_job_details(job_id: str):
    job_details = linkedin.get_job(job_id)
    return job_details

def search_jobs(keywords, location_name, listed_at, companies):
    print(f"*********Searching Jobs with User Defined Parameters********** \nKeyword: {keywords}, \nLocation:  {location_name}, \nListed at: {listed_at}, \nCompanies ID: {companies}")
    print("Searching.............")
    jobs = linkedin.search_jobs(keywords=keywords, location_name=location_name, listed_at=listed_at, companies=companies)
    print("Jobs Retrieval Completed")
    return jobs

def fetch_jobs_details(jobs: list):
    print("********Fetching Job Details For Each Job ID********")
    jobs_details = []
    for job in jobs:
        job_id = job['entityUrn'].split(':')[-1]
        job_details = fetch_job_details(job_id)
        jobs_details.append(job_details)
        print("Job Details Retrieved for Job ID : ", job_id)
    
    return jobs_details

def summarize_jobs_details(jobs_details: list):
    print("********Summarizing Jobs Details********")
    summarized_jobs_details = []
    for job in jobs_details:
        job_summary = {
            "job_title": job['title'],
            "job_id": job['entityUrn'].split(':')[-1],
            "company_name": job['companyDetails']['com.linkedin.voyager.deco.jobs.web.shared.WebCompactJobPostingCompany']['companyResolutionResult']['name'],
            "job_description": job['description']['text'],
            "job_url": "https://www.linkedin.com/jobs/view/" + job['entityUrn'].split(':')[-1], 
            "job_location": job['formattedLocation'], 
            "job_posted_at": job['listedAt'], 
            "workRemoteAllowed": job['workRemoteAllowed']
        }
        summarized_jobs_details.append(job_summary)
    print("Jobs Details Summarized Successfully")
    return summarized_jobs_details
#Test functions
def test_get_company_urn_id(name):
    print(f"Test get {name} urn_id: ", get_company_urn_id(name))

def test_get_multiple_companies_urn_id(companies: list):
    print(f"Test get {companies}urn_id: ", get_multiple_companies_urn_id(companies))

def test_search_jobs(keywords, location_name, listed_at, companies):
    jobs = linkedin.search_jobs(keywords=keywords, location_name=location_name, listed_at=listed_at, companies=companies)
    print(f"Test search jobs using keyword {keywords}, \nlocation {location_name}, \nlisted at {listed_at}, \ncompanies {companies}: \n", jobs)
    return jobs

def test_get_jobs_details(jobs: list):
    filepath = "../data/jobs/jobs_details.json"
    jobs_details = []
    for job in jobs:
        job_id = job['entityUrn'].split(':')[-1]
        print("Retrieved Job ID: ", job_id)
        job_details = fetch_job_details(job_id)
        print("Job Details Retrieved for Job ID: ", job_id)
        jobs_details.append(job_details)
    
    write_to_file(jobs_details, filepath)

def main():
    print("Fetching jobs using FREE LinkedIn API")
    
    #split companies string into a list and get their urn_id. remove any white spaces
    companies = COMPANIES_LITERAL.split(',')
    companies = [company.strip() for company in companies]
    companies_urn_id = get_multiple_companies_urn_id(companies)
    
    #search jobs
    jobs = search_jobs(KEYWORDS, LOCATION_NAME, LISTED_AT, companies_urn_id)
    if jobs:
        print(f"Jobs Retrieved Successfully with {len(jobs)} matched jobs")
    elif not jobs:
        print("No jobs found...Please refine your search parameters")
        return
    write_to_file(jobs, jobs_file_path)

    #get job details
    jobs_details = fetch_jobs_details(jobs)
    write_to_file(jobs_details, "../data/jobs/jobs_details.json")

    #get summarized job details
    summarized_jobs_details = summarize_jobs_details(jobs_details)
    write_to_file(summarized_jobs_details, "../data/jobs/jobs_search_summary.json")

    print("Jobs fetched successfully")
    
if __name__ == "__main__":
    main()