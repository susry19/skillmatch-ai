import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path, override=True)

API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)

def analyze_cv(text: str):
    """
    Analyzes CV text using Gemini 1.5 Pro to extract structured data.
    """
    if not API_KEY:
        # Return mock data if no API key is found
        return get_mock_data()

    model = genai.GenerativeModel('gemini-flash-latest', generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    You are an expert HR AI Assistant. Analyze the following CV text and extract structured information.
    Return the output strictly as a JSON object with the following schema:
    {{
        "name": "Candidate Name",
        "email": "email@example.com",
        "phone": "+123456789",
        "summary": "Professional summary...",
        "skills": ["Skill1", "Skill2"],
        "experience": [
            {{"title": "Job Title", "company": "Company", "years": "2020-2022", "description": "..."}}
        ],
        "education": [
            {{"degree": "Degree", "school": "School", "year": "2019"}}
        ],
        "certifications": ["Cert 1", "Cert 2"],
        "projects": ["Project 1", "Project 2"],
        "seniority_level": "Junior/Mid/Senior",
        "seniority_score": 85.5,
        "strengths": ["Strength 1", "Strength 2"],
        "areas_for_improvement": ["Area 1", "Area 2"]
    }}

    CV Text:
    {text}
    """
    
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"AI Analysis failed: {e}")
        return get_mock_data()

def get_mock_data():
    return {
        "name": "Mock Candidate",
        "email": "mock@example.com",
        "phone": "555-0123",
        "summary": "Experienced developer with a passion for AI.",
        "skills": ["Python", "React", "FastAPI", "Docker"],
        "experience": [
            {"title": "Senior Developer", "company": "Tech Corp", "years": "2020-Present", "description": "Leading backend team."}
        ],
        "education": [
            {"degree": "BS Computer Science", "school": "University of Tech", "year": "2018"}
        ],
        "certifications": ["AWS Certified"],
        "projects": ["SkillMatch AI"],
        "seniority_level": "Senior",
        "seniority_score": 90.0,
        "strengths": ["System Design", "Leadership"],
        "areas_for_improvement": ["Public Speaking"]
    }

def compare_candidates(candidate1: dict, candidate2: dict, position: dict = None) -> dict:
    """
    Compares two candidates using Gemini AI, optionally against a specific position.
    """
    if not API_KEY:
        return {
            "comparison": "API Key eksik. Mock karşılaştırma.",
            "recommendation": "API Key giriniz.",
            "candidate1_pros": ["Mock Pro 1"],
            "candidate2_pros": ["Mock Pro 2"],
            "comparison_table": []
        }

    model = genai.GenerativeModel('gemini-flash-latest', generation_config={"response_mime_type": "application/json"})
    
    position_context = ""
    if position:
        position_context = f"""
        CONTEXT:
        Compare these candidates specifically for the following position:
        Title: {position['title']}
        Department: {position['department']}
        Description: {position['description']}
        Required Skills: {', '.join(position['required_skills'])}
        
        Focus on how well each candidate fits THIS specific role.
        """

    prompt = f"""
    You are an expert HR AI assistant. Compare the following two candidates.
    {position_context}

    CANDIDATE 1:
    Name: {candidate1['name']}
    Summary: {candidate1['summary']}
    Skills: {', '.join(candidate1['skills'])}
    Experience: {json.dumps(candidate1['experience'])}

    CANDIDATE 2:
    Name: {candidate2['name']}
    Summary: {candidate2['summary']}
    Skills: {', '.join(candidate2['skills'])}
    Experience: {json.dumps(candidate2['experience'])}

    OUTPUT FORMAT (JSON):
    {{
        "comparison": "Detailed comparison text...",
        "recommendation": "Clear recommendation on who to hire and why...",
        "candidate1_pros": ["Pro 1", "Pro 2"],
        "candidate2_pros": ["Pro 1", "Pro 2"],
        "comparison_table": [
            {{"criteria": "Technical Skills", "candidate1_val": "Strong Python...", "candidate2_val": "Expert Java..."}},
            {{"criteria": "Experience", "candidate1_val": "5 years...", "candidate2_val": "3 years..."}},
            {{"criteria": "Education", "candidate1_val": "...", "candidate2_val": "..."}},
            {{"criteria": "Soft Skills", "candidate1_val": "...", "candidate2_val": "..."}},
            {{"criteria": "Overall Fit", "candidate1_val": "High", "candidate2_val": "Medium"}}
        ]
    }}
    Ensure the JSON is valid.
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean up potential markdown code blocks
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"Error comparing candidates: {e}")
        return {
            "comparison": "Error generating comparison.",
            "recommendation": "N/A",
            "candidate1_pros": [],
            "candidate2_pros": [],
            "comparison_table": []
        }

def deep_rank_candidates(position_dict: dict, candidates_list: list, all_positions_list: list = None) -> list:
    """
    Explainable AI for Recruitment Decision Support System.
    Deeply analyzes and ranks multiple candidates for a specific position.
    """
    if not API_KEY:
        raise Exception("API Key eksik. Explainable AI çalıştırılamıyor.")

    model = genai.GenerativeModel('gemini-1.5-pro-latest', generation_config={"response_mime_type": "application/json"})
    
    # Trim candidate data to fit within reasonable prompt size
    trimmed_candidates = []
    for c in candidates_list:
        trimmed_candidates.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "summary": c.get("summary"),
            "skills": c.get("skills"),
            "experience": c.get("experience", [])[:3], # keep last 3 experiences
            "education": c.get("education", [])[:2],
            "seniority_level": c.get("seniority_level")
        })

    alt_positions_str = ""
    if all_positions_list:
        alt_pos_short = [{"id": p.get("id"), "title": p.get("title")} for p in all_positions_list if p.get("id") != position_dict.get("id")]
        alt_positions_str = f"Available alternative positions in the company: {json.dumps(alt_pos_short)}\n"

    prompt = f"""
    You are an expert "Explainable AI for Recruitment Decision Support System".
    Evaluate, rank, and deeply analyze the provided candidates against the job position.

    JOB POSITION:
    Title: {position_dict.get('title')}
    Department: {position_dict.get('department')}
    Description: {position_dict.get('description')}
    Required Skills: {', '.join(position_dict.get('required_skills', []))}
    Seniority Level: {position_dict.get('seniority_level')}

    CANDIDATES:
    {json.dumps(trimmed_candidates, ensure_ascii=False)}

    {alt_positions_str}
    
    INSTRUCTIONS:
    1. Analyze each candidate against the job position.
    2. Rank them from best to worst based on their fit.
    3. Generate a match score between 0 and 100 for each.
    4. Provide Explainable AI reasoning: strengths, weaknesses, risks, skill gap analysis, and a natural language explanation of why they got this rank.
    5. Provide a 'future_potential_score' (0-100) estimating how suitable they could become in 6 months.
    6. Generate 3 specific interview questions tailored to the candidate's profile and the job position's requirements.
    7. If a candidate is a poor fit for this job but might fit an alternative position provided, suggest the alternative position's title.

    OUTPUT FORMAT: Return a JSON array of objects strictly matching this schema:
    [
      {{
        "candidate_id": 123,
        "rank": 1,
        "match_score": 95,
        "strengths": ["Strong Python", "Leadership"],
        "weaknesses": ["No AWS experience"],
        "risks": ["Job hopping risk (3 jobs in 2 years)"],
        "skill_gap": "Missing cloud deployment skills (AWS/GCP).",
        "explanation": "Candidate is highly ranked because of their perfect match in backend tech stack, though they lack cloud experience.",
        "future_potential_score": 98,
        "interview_questions": ["How would you handle...", "Can you describe..."],
        "alternative_position": null
      }}
    ]
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"Error in deep ranking: {e}")
        raise e
