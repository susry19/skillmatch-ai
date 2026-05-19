import google.generativeai as genai
from sqlalchemy.orm import Session
from .. import models
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path, override=True)

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

class ChatbotService:
    def __init__(self):
        # Use a model confirmed to be in the user's available list
        self.model = genai.GenerativeModel('gemini-flash-latest')
        # We don't use stateful history list here anymore for robustness in this simple structure.
        # We will build prompt per request.

    def get_context(self, db: Session):
        """Retrieves all candidates and positions to form the context."""
        candidates = db.query(models.Candidate).all()
        positions = db.query(models.Position).all()
        
        context_str = "--- CURRENT DATABASE CONTEXT ---\n"
        context_str += "CANDIDATES:\n"
        for c in candidates:
            skills = ", ".join(c.skills) if c.skills else "None"
            context_str += f"- {c.name} ({c.seniority_level}): {skills}. Summary: {c.summary}\n"
        
        context_str += "\nPOSITIONS:\n"
        for p in positions:
            req_skills = ", ".join(p.required_skills) if p.required_skills else "None"
            context_str += f"- {p.title} ({p.department}): {req_skills}\n"
        
        context_str += "--- END CONTEXT ---\n"
        return context_str

    def search_web(self, query: str):
        """Performs a web search using DuckDuckGo."""
        if not HAS_DDG:
            return "\n[Web Search Unavailable]\n"
            
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=2))
            return f"\n--- WEB SEARCH RESULTS FOR '{query}' ---\n{results}\n--- END WEB SEARCH ---\n"
        except Exception as e:
            return f"\n[Web Search Failed: {e}]\n"

    def chat(self, user_message: str, db: Session):
        if not API_KEY:
            return "Demo Modu: API Anahtarı bulunamadı (GEMINI_API_KEY)."

        try:
            # 1. Build Context
            db_context = self.get_context(db)
            
            # 2. Web Search (Trigger based)
            search_keywords = ["hava", "haber", "maaş", "nedir", "kimdir", "fiyat", "borsa", "trend"]
            web_context = ""
            if any(keyword in user_message.lower() for keyword in search_keywords):
                web_context = self.search_web(user_message)

            # 3. Construct System Prompt
            system_instruction = f"""Sen 'SkillMatch AI' adında profesyonel bir İK Asistanısın.
            Aşağıdaki veritabanı bağlamını kullanarak kullanıcın sorularını yanıtla.
            
            {db_context}
            
            {web_context}
            
            Kurallar:
            - Adaylar veya pozisyonlar hakkında soru gelirse veritabanını kullan.
            - Genel kültür veya dış bilgi gerekirse web sonuçlarını veya kendi bilgini kullan.
            - Yanıtların kısa, öz ve profesyonel olsun.
            - Türkçe yanıt ver.
            """
            
            # 4. Generate Content (Stateless Mode)
            # Sends the full context + instructions + user message as a single prompt.
            # This avoids "Message role must be user" errors with accumulating contexts.
            
            full_prompt = f"{system_instruction}\n\nKullanıcı: {user_message}"
            
            response = self.model.generate_content(full_prompt)
            
            return response.text
        except Exception as e:
            # Safe error printing for Windows Console
            try:
                print(f"Chat Error: {str(e).encode('utf-8', errors='ignore')}")
            except:
                print("Chat Error: (Encoding Failed)")
            return f"Üzgünüm, şu an yanıt veremiyorum. (AI Servis Hatası: {e})"

chatbot_service = ChatbotService()
