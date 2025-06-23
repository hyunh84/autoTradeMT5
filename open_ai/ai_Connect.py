# openai/ai_Connect.py

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()  # .env에서 API 키 불러오기

class AIConnect:
	def __init__(self):
		self.status = "fail"
		self.model = "gpt-3.5-turbo"  # ✅ 나중에 gpt-4로 바꾸면 바로 적용됨

		try:
			api_key = os.getenv("OPENAI_API_KEY")
			if not api_key:
				raise ValueError("환경변수 OPENAI_API_KEY가 설정되지 않았습니다.")
			
			# ✅ 최신 방식 클라이언트 객체 생성
			self.client = OpenAI(api_key=api_key)

			# ✅ 연결 테스트 (ping)
			self.client.chat.completions.create(
				model=self.model,
				messages=[{"role": "user", "content": "ping"}],
				max_tokens=1
			)
			self.status = "success"

		except Exception as e:
			self.status = f"fail: {str(e)}"

	def ask(self, prompt: str) -> str:
		try:
			response = self.client.chat.completions.create(
				model=self.model,
				messages=[{"role": "user", "content": prompt}],
				temperature=0.7,
			)
			return response.choices[0].message.content.strip()

		except Exception as e:
			return f"[OpenAI 오류] {e}"
