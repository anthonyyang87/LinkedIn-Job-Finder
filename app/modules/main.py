import google.generativeai as genai
import json
import os
import sys
import time
import subprocess
import pdfplumber
import asyncio
import threading
import configparser
from dotenv import load_dotenv

#read from .env file
load_dotenv()

#Accessing the environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


#read from ini file
config = configparser.ConfigParser()
config.read('../config.ini')

#Should store sensitive information in .env file
#GEMINI_API_KEY = config['AI_PARAMETERS']['gemini_api_key']
MODEL_NAME = config['AI_PARAMETERS']['model_name']

RESUME_NAME = config['USER_PARAMETERS']['resume_name']
YEARS_OF_EXPERIENCE = config['USER_PARAMETERS']['years_of_experience']
EDUCATION_LEVEL = config['USER_PARAMETERS']['education_level']
EDUCATION_FIELD = config['USER_PARAMETERS']['education_field']
MINIMUM_SALARY = config['USER_PARAMETERS']['minimum_salary']
NUMBER_OF_RECOMMENDATIONS = config['USER_PARAMETERS']['number_of_recommendations']

def getjob__url(job_id):
    return f"https://www.linkedin.com/jobs/view/{job_id}/"

def read_user_resume(filepath):
    with pdfplumber.open(filepath) as pdf:
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        return text

def show_loading_indicator():
    while not done:
        print(".", end="", flush=True)
        time.sleep(0.5)

def stream_with_subprocess_run(command):
    global done 
    done = False
    
    # Start a thread to show a loading indicator
    loading_thread = threading.Thread(target=show_loading_indicator)
    loading_thread.start()

    process = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True  # Ensures output is text (not bytes)
    )
    
    done = True
    loading_thread.join()

    # Split output into lines for real-time printing
    for line in process.stdout.splitlines():
        print(line)

    for line in process.stderr.splitlines():
        print(line, file=sys.stderr)
    
    print(f"{command} Process completed")
    return process

def find_top_jobs_with_AI(resume, jobs):
    return jobs

def dump_json_to_text_file(json_file, text_file):
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Write JSON data to a text file
    with open(text_file, 'w') as file:
        json.dump(data, file, indent=2)

def write_to_text_file(data, filename):
    #append data to text file
    with open(filename, 'a') as f:
        #add current time
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        f.write("\n\n\n")
        f.write(current_time + "\n")
        f.write(data)
        f.write("*****************************************************")
    print(f"Data written to {filename}")

def main():
    
    #configure gemini
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)

    #run fetch_jobs.py
    print("Running fetch_jobs.py.....Please wait a moment to fetch jobs.....")
    command = ["python", "fetch_jobs.py"]
    result = stream_with_subprocess_run(command)
    if result.returncode == 0:
        print("fetch_jobs.py ran successfully")
    else:
        print("fetch_jobs.py failed.....exiting program")
        return 1

    print("\n\n\n****************Uploading User Files, Forming Queries and Generating Responses Using AI****************\n\n\n")
    #read user resume
    print("Reading user resume.....")

    #get current directory
    jobs_summary_path = "../data/jobs/jobs_search_summary.json"
    jobs_summary_text_path = "../data/jobs/jobs_search_summary.txt"

    #convert json to text file
    dump_json_to_text_file(jobs_summary_path, jobs_summary_text_path)

    resume_path = "../resources/" + RESUME_NAME
    resume_text = read_user_resume(resume_path)
    
    resume = genai.upload_file(resume_path)
    jobs = genai.upload_file(jobs_summary_text_path)

    conversations_path = "../data/conversations/conversations.txt"
    
    
    print("Files uploaded: ")
    for f in genai.list_files():
        print(" ", f.display_name)
    
    query = f"Tell me, what are the job titles of the jobs_search_summary?Let me give you a hint, you can find 'job_title' and the assigned value. I also want you to tell me the company_name, and job_url of each job title. By summarizing the job_description, also list the skill sets, experience that the candidate must acquire to succeed in this job. If salary range is mentioned, please also include it in the summary. To summarize my prompt, I want you to list the job_title, company_name, job_url, job_description, skill sets, experience, and salary range of each job in the jobs_search_summary."

    print("*******************User Query********************\n", query)
    response = model.generate_content([query, jobs])

    print("*******************AI response********************\n")
    print(response.text)

    #write to text file also inlucde current time
    
    write_to_text_file("User Query: \n" + query, conversations_path)
    write_to_text_file("AI Response: \n" + response.text, conversations_path)

    query = f"Now you have a summary of the jobs_search_summary. Can you tell me which job is the best fit for me? I have {YEARS_OF_EXPERIENCE} years of experience, {EDUCATION_LEVEL} in {EDUCATION_FIELD}, and I am looking for a job with a minimum salary of {MINIMUM_SALARY}. Please assess the following text and take into consideration: {resume_text}. I want you pick the top 10 jobs from the list you generated earlier. Please also provide the job_url of each job."

    print("*******************User Query********************\n", query)
    response = model.generate_content([query, jobs])

    print("*******************AI response********************\n")
    print(response.text)

    write_to_text_file("User Query: \n" + query, conversations_path)
    write_to_text_file("AI Response: \n" + response.text, conversations_path)

    print("\n\n****************End of Conversation****************\n\n")

    #delete all files
    print("\n\nDeleting all uploaded files.....\n\n")
    for f in genai.list_files():
        print("Deleting file: ", f.display_name)
        f.delete()
    print("All files deleted!")

    print(f"\n\n\nJob recommendations completed successfully. Powered by https://github.com/tomquirk/linkedin-api and {MODEL_NAME}. Thank you  and have a great day!\n\n\n")


if __name__ == "__main__":
    main()
