import streamlit as st
import openai
import textwrap
import json

class LlamaAcademy:
    def __init__(self):
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'client' not in st.session_state:
            st.session_state.client = None
        if 'quiz_active' not in st.session_state:
            st.session_state.quiz_active = False
        if 'quiz_questions' not in st.session_state:
            st.session_state.quiz_questions = []
        if 'current_question' not in st.session_state:
            st.session_state.current_question = 0
        if 'score' not in st.session_state:
            st.session_state.score = 0

    def initialize_client(self, api_key: str, base_url: str):
        st.session_state.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    def format_teacher_prompt(self) -> str:
        return """You are a skilled and patient teacher. Your role is to:
1. Explain concepts clearly and thoroughly, starting from the basics
2. Use examples and analogies to make complex topics understandable
3. Break down information into digestible chunks
4. Maintain an encouraging and supportive tone
5. End your explanations with 1-2 review questions about the key points covered

Remember to teach as if you're speaking to a student who is encountering this topic for the first time."""

    def format_quizzer_prompt(self, conversation_history: str) -> str:
        return f"""Based on the following teaching conversation, create 5 multiple-choice questions to test the student's understanding. Format your response as a JSON array with this structure:
[{{
    "question": "Question text",
    "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
    "correct_answer": "A" 
}}]

Teaching conversation:
{conversation_history}"""

    def format_messages(self, query: str, is_quiz: bool = False) -> list:
        messages = [
            {"role": "system", "content": self.format_quizzer_prompt(query) if is_quiz 
             else self.format_teacher_prompt()},
        ]
        
        if not is_quiz:
            for msg in st.session_state.messages:
                if msg["role"] != "system":
                    messages.append(msg)
            messages.append({"role": "user", "content": query})
        
        return messages

    def generate_quiz(self, conversation_history: str, model: str):
        messages = self.format_messages(conversation_history, is_quiz=True)
        response = st.session_state.client.chat.completions.create(
            model=model,
            messages=messages
        )
        quiz_content = response.choices[0].message.content
        try:
            st.session_state.quiz_questions = json.loads(quiz_content)
            st.session_state.quiz_active = True
            st.session_state.current_question = 0
            st.session_state.score = 0
        except json.JSONDecodeError:
            st.error("Failed to generate quiz. Please try again.")

    def display_quiz(self):
        if st.session_state.current_question < len(st.session_state.quiz_questions):
            question = st.session_state.quiz_questions[st.session_state.current_question]
            st.write(f"Question {st.session_state.current_question + 1}:")
            st.write(question["question"])
            
            answer = st.radio("Select your answer:", question["options"], key=f"q_{st.session_state.current_question}")
            
            if st.button("Submit Answer"):
                selected_letter = answer[0]  # Get the letter (A, B, C, D)
                if selected_letter == question["correct_answer"]:
                    st.success("Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"Incorrect. The correct answer was {question['correct_answer']}")
                st.session_state.current_question += 1
                st.rerun()
        else:
            st.write(f"Quiz completed! Your score: {st.session_state.score}/{len(st.session_state.quiz_questions)}")
            if st.button("Return to Learning"):
                st.session_state.quiz_active = False
                st.rerun()

    def run(self):
        st.title("🦙 Llama Academy")
        
        with st.sidebar:
            st.header("Configuration")
            api_key = st.text_input("API Key", "sk-s2Hpm8x0MkhzV743Ecqzqw", type="password")
            base_url = st.text_input("Base URL", "https://chatapi.akash.network/api/v1")
            
            available_models = [
                "Meta-Llama-3-1-8B-Instruct-FP8",
                "Meta-Llama-3-1-405B-Instruct-FP8",
                "Meta-Llama-3-2-3B-Instruct",
                "nvidia-Llama-3-1-Nemotron-70B-Instruct-HF",
            ]
            
            model = st.selectbox("Select Model", options=available_models, index=0)
            
            if st.button("Clear Chat History"):
                st.session_state.messages = []
                st.session_state.quiz_active = False
            
            if api_key and base_url:
                self.initialize_client(api_key, base_url)

        if st.session_state.quiz_active:
            self.display_quiz()
        else:
            for message in st.session_state.messages:
                if message["role"] != "system":
                    with st.chat_message(message["role"]):
                        st.write(textwrap.fill(message["content"], 100))
            
            if len(st.session_state.messages) > 0:
                if st.button("Take Quiz"):
                    conversation = "\n".join([msg["content"] for msg in st.session_state.messages 
                                           if msg["role"] != "system"])
                    self.generate_quiz(conversation, model)
                    st.rerun()

            if prompt := st.chat_input("What would you like to learn about?"):
                if st.session_state.client is None:
                    st.error("Please configure API settings in the sidebar first.")
                    return
                
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.write(prompt)
                
                try:
                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            messages = self.format_messages(prompt)
                            response = st.session_state.client.chat.completions.create(
                                model=model,
                                messages=messages
                            )
                            assistant_response = response.choices[0].message.content
                            
                            st.write(textwrap.fill(assistant_response, 100))
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": assistant_response
                            })
                            
                except Exception as e:
                    st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    llama_academy = LlamaAcademy()
    llama_academy.run()
