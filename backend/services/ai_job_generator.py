import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path, override=True)

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

class AIJobGenerator:
    def __init__(self):
        # Using gemini-flash-latest as verified working
        self.model = genai.GenerativeModel('gemini-flash-latest')

    def generate_job_specs(self, title: str):
        """
        Generates a professional job description and required skills for a given position title.
        Returns a dictionary: { "description": str, "skills": List[str] }
        """
        if not API_KEY:
            return {
                "description": f"{title} pozisyonu için deneyimli ve yetenekli bir takım arkadaşı arıyoruz.",
                "skills": ["İletişim", "Takım Çalışması"],
                "salary": {"min": 0, "max": 0, "currency": "TRY", "source": "Mod (No Key)"}
            }

        prompt = f"""
        Act as an expert HR Consultant for the Turkish Tech Market (Istanbul based).
        Analyze the job title: "{title}"
        
        1. Create a professional, concise job description (in Turkish).
        2. List exactly 5 key technical skills required (comma separated).
        3. Estimate the CURRENT monthly NET salary range (in TRY) for this role in Istanbul, Turkey (2025 Market Rates).
           - Consider high inflation and current competitive tech wages.
           - If seniority is not specified, assume 'Mid-Senior' level.
           - Realistic ranges for 2025 (Reference):
             * Junior: 35,000 - 55,000 TRY
             * Mid: 65,000 - 95,000 TRY
             * Senior: 110,000 - 160,000+ TRY
           - Do NOT give generic low numbers. Give aggressive, real-world private sector wages.

        Output strictly in JSON format with the following structure:
        {{
            "description": "A concise, professional, and inviting job description in Turkish (2-3 sentences max).",
            "skills": ["Skill1", "Skill2", "Skill3", "Skill4", "Skill5"],
            "salary": {{
                "min": 0,
                "max": 0,
                "currency": "TRY",
                "source": "AI Market Analysis (Istanbul 2025)"
            }}
        }}
        
        Ensure the content is high quality and relevant to the specific role.
        """

        try:
            response = self.model.generate_content(prompt)
            # Clean up potential markdown code blocks if the model adds them
            text = response.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(text)
            
            # Fallback validation
            if "description" not in data:
                data["description"] = f"{title} için arayışımız sürmektedir."
            if "skills" not in data or not isinstance(data["skills"], list):
                data["skills"] = ["İletişim"]
            if "salary" not in data:
                 data["salary"] = {"min": 0, "max": 0, "currency": "TRY", "source": "Estimation"}
                
            return data
            
        except Exception as e:
            print(f"[AIJobGenerator] Generation failed: {e}")
            return {
                "description": f"{title} pozisyonu için ekibimize güç katacak yeni arkadaşlar arıyoruz.",
                "skills": ["İletişim", "Problem Çözme"],
                "salary": {"min": 0, "max": 0, "currency": "TRY", "source": "Hata (Fallback)"} 
            }

ai_job_generator = AIJobGenerator()
