import json
import random

skills_pool = ["Python", "Java", "React", "Angular", "Vue", "AWS", "GCP", "Azure", "Docker", "Kubernetes", "C++", "C#", "SQL", "NoSQL", "MongoDB", "Redis", "Elasticsearch", "Machine Learning", "Data Science", "Kafka", "FastAPI", "Django", "Spring Boot", "TypeScript"]
companies_pool = ["Google", "Amazon", "Microsoft", "Meta", "Apple", "Netflix", "Uber", "Airbnb", "Stripe", "Square", "Spotify", "Snap", "Twitter", "LinkedIn", "Salesforce", "Flipkart", "Zomato", "Swiggy", "PhonePe", "Zerodha"]
roles_pool = ["Software Engineer", "Senior Software Engineer", "Data Scientist", "Frontend Developer", "Backend Developer", "Full Stack Developer", "DevOps Engineer", "ML Engineer", "Data Engineer", "SRE"]
first_names = ["Rahul", "Priya", "Amit", "Neha", "Vikram", "Sneha", "Rohan", "Ananya", "Arjun", "Kavitha", "Manish", "Shreya", "Deepak", "Divya", "Aditya", "Ritu", "Rajesh", "Pooja", "Saurabh", "Tanvi"]
last_names = ["Sharma", "Patel", "Gupta", "Reddy", "Singh", "Iyer", "Nair", "Joshi", "Mehta", "Krishnan", "Desai", "Banerjee", "Kumar", "Agarwal", "Tiwari", "Saxena", "Verma", "Chauhan", "Menon", "Jain"]

try:
    with open("data/candidates.json", "r", encoding="utf-8") as f:
        candidates = json.load(f)
except Exception as e:
    print("Error loading candidates:", e)
    candidates = []

start_id = max([c["id"] for c in candidates]) + 1 if candidates else 1

for i in range(50):
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    skills = random.sample(skills_pool, k=random.randint(5, 9))
    experience = random.randint(1, 12)
    company = random.choice(companies_pool)
    role = random.choice(roles_pool)
    
    cand = {
        "id": start_id + i,
        "name": name,
        "skills": skills,
        "experience_years": experience,
        "current_company": company,
        "joined_current_job": f"202{random.randint(0, 3)}-0{random.randint(1, 9)}-15",
        "work_experience": [
            {"company": company, "role": role, "duration": f"202{random.randint(0, 3)}-present"}
        ],
        "projects": [f"Built scalable system for {company}", f"Optimized performance at {company}"],
        "raw_resume_text": f"{name} — {role} at {company} with {experience} years of experience. Expert in {', '.join(skills)}. Worked on building scalable systems and optimizing performance."
    }
    candidates.append(cand)

with open("data/candidates.json", "w", encoding="utf-8") as f:
    json.dump(candidates, f, indent=2)

print(f"Added 50 candidates. Total candidates: {len(candidates)}")
