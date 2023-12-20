import csv
import hashlib
import re
from datetime import datetime

def clean_and_hash_email(email):
    # Lowercase the email
    email = email.lower()
    
    # Remove all non-alphanumeric characters except for ., @, and -
    email = re.sub(r"[^a-zA-Z0-9.@-]", "", email)
    
    # Remove any leading or trailing whitespace
    email = email.strip()
    
    # Hash the email with sha256
    hashed_email = hashlib.sha256(email.encode()).hexdigest()
    
    return hashed_email

def extract_emails_from_csv(filename):
    cleaned_and_hashed_emails = []
    
    with open(filename, mode="r") as file:
        reader = csv.reader(file)
        for row in reader:
            for field in row:
                # Assuming that the email might be anywhere in the row
                # The below regex checks for a simple pattern which is generally followed by email addresses.
                if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", field):
                    cleaned_and_hashed_emails.append(clean_and_hash_email(field))
    
    return cleaned_and_hashed_emails

def write_hashed_emails_to_csv(emails, output_filename):
    with open(output_filename, mode="w", newline='') as file:
        writer = csv.writer(file)
        for email in emails:
            writer.writerow([email])

if __name__ == "__main__":
    input_filename = "path_to_your_input_csv.csv"
    
    # Add a timestamp to the output filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = f"hashed_emails_{timestamp}.csv"
    
    hashed_emails = extract_emails_from_csv(input_filename)
    write_hashed_emails_to_csv(hashed_emails, output_filename)
    print(f"Processed and saved hashed emails to {output_filename}")
