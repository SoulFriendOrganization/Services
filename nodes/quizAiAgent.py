from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
from typing import TypedDict, Optional, Literal
from logging_config import logger
import random
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END

load_dotenv()

class PossibleOptions(TypedDict):
    A: str
    B: str
    C: str
    D: str

class Question(TypedDict):
    question: str
    possible_answers: PossibleOptions
    question_type: Literal["multiple_choice", "multiple_answer"]
    correct_answer: list[str]

class QuizState(TypedDict):
    theme: str
    difficulty: str
    user_condition_summary: Optional[str]
    total_questions: int
    current_question: int
    current_question_type: str
    quiz_title: Optional[str] = None
    quiz_description: Optional[str] = None
    questions: list[Question]

class PossibleAnswers(BaseModel):
    A: str = Field(description="Option A")
    B: str = Field(description="Option B")
    C: str = Field(description="Option C")
    D: str = Field(description="Option D")

class QuestionModel(BaseModel):
    question: str = Field(description="The question text")
    possible_answers: PossibleAnswers = Field(description="Possible answers for the question")
    correct_answer: list[Literal["A", "B", "C", "D"]] = Field(
        description="List of correct answers (can only contain A, B, C, or D)",
        min_length=1
    )

class QuizAiAgent:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            deployment_name="gpt-4.1",
            model="gpt-4.1",
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            temperature=0.5,
            max_tokens=5000
        )
        self.quiz_agent = self._init_graph()

    def _init_graph(self):
        graph = StateGraph(QuizState)
        graph.add_node("theme_selection", lambda quiz_state: quiz_state)
        graph.add_node("process_mental_health", self._process_mental_health)
        graph.add_node("generate_quiz_mental_health", self._generate_quiz_mental_health)
        graph.add_node("process_judi_online", self._process_judi_online)
        graph.add_node("generate_quiz_judi_online", self._generate_quiz_judi_online)
        graph.add_node("title_and_description", self._generate_quiz_title_and_description)

        graph.set_entry_point("theme_selection")
        graph.add_conditional_edges(
            "theme_selection", 
            self._theme_pointer,
            {
            "mental_health": "process_mental_health",
            "judi_online": "process_judi_online"
            }
            )
        graph.add_conditional_edges(
            "process_mental_health",
            self._process_mental_health_condition, 
            {
                "continue": "generate_quiz_mental_health",
                "end": "title_and_description"
            }
        )
        graph.add_edge("generate_quiz_mental_health", "process_mental_health")
        graph.add_conditional_edges(
            "process_judi_online", 
            self._process_judi_online_condition,
            {
                "continue": "generate_quiz_judi_online",
                "end": "title_and_description"
            }
        )
        graph.add_edge("generate_quiz_judi_online", "process_judi_online")
        graph.add_edge("title_and_description", END)
        return graph.compile()

    def _generate_question_type(self) -> str:
        """
        Generates a random question type for the quiz.
        """
        question_types = ["multiple_choice", "multiple_answer"]
        return random.choices(
            question_types, 
            weights=[0.8, 0.2],  # 80% for multiple_choice, 20% for multiple_answer
            k=1
        )[0]
    
    def _theme_pointer(self, quiz_state: QuizState) -> str:
        """
        Processes the user condition summary and returns a formatted string.
        """
        if quiz_state.get("theme") == "mental_health":
            return "mental_health"
        return "judi_online"
    
    def _process_mental_health(self, quiz_state: QuizState) -> QuizState:
        """
        Processes the mental health condition and returns a formatted string.
        """
        logger.info("Processing mental health condition for quiz generation")
        if quiz_state.get("current_question") is None:
            logger.info("Starting a new quiz session")
            quiz_state["current_question"] = 1
        else:
            quiz_state["current_question"] += 1
        if quiz_state.get("total_questions") < quiz_state["current_question"]:
            return quiz_state
        logger.info(f"Advancing to question {quiz_state['current_question']}")
        question_type = self._generate_question_type()
        logger.info(f"Generated question type: {question_type}")
        quiz_state["current_question_type"] = question_type
        return quiz_state
    
    def _generate_quiz_mental_health(self, quiz_state: QuizState) -> QuizState:
        """
        Generates a quiz based on the mental health condition.
        """
        logger.info("Generating mental health quiz")
        generate_mental_health_quiz_prompt_template = """
        You are a quiz generator for mental health awareness.
        Generate a quiz question based on the user's condition summary so that the user can learn more about their mental health.
        The quiz should be engaging and informative. and make the user more aware of their mental health.
        And can help the user to improve their mental health condition.
        
        And make sure there are no duplicates questions in the quiz.
        this is the questions history:
        {questions_history}

        This is the information about the user:
        user_condition_summary: {user_condition_summary}

        and this is the quiz rules that you need to follow:
        difficulty: {difficulty}
        question_type: {question_type}
        Note:
            if the question_type is multiple_choice then you need to provide 4 possible answers (A, B, C, D) and only one correct answer.
            and only one correct answer is allowed.
            if the question_type is multiple_answer then you need to provide 4 possible answers (A, B, C, D) and at least two correct answers.
            and only two or three correct answers are allowed.
        """
        generate_mental_health_quiz_prompt = PromptTemplate(
            input_variables=["user_condition_summary", "difficulty", "question_type", "questions_history"],
            template=generate_mental_health_quiz_prompt_template
        )

        generate_mental_health_quiz = generate_mental_health_quiz_prompt | self.llm.with_structured_output(QuestionModel)
        logger.info("Sending request to generate mental health quiz question")
        response = generate_mental_health_quiz.invoke({
            "user_condition_summary": quiz_state.get("user_condition_summary", ""),
            "difficulty": quiz_state.get("difficulty", "easy"),
            "question_type": quiz_state.get("current_question_type", "multiple_choice"),
            "questions_history": "\n".join([q["question"] for q in quiz_state.get("questions", [])])
        })
        response_dict = response.model_dump()
        logger.info(f"Generated question: {response_dict['question']}")
        quiz_state["questions"].append({
            "question": response_dict["question"],
            "possible_answers": {
                "A": response_dict["possible_answers"].get("A"),
                "B": response_dict["possible_answers"].get("B"),
                "C": response_dict["possible_answers"].get("C"),
                "D": response_dict["possible_answers"].get("D")
            },
            "question_type": quiz_state.get("current_question_type", "multiple_choice"),
            "correct_answer": response_dict["correct_answer"]
        })

        return quiz_state

    def _process_mental_health_condition(self, quiz_state: QuizState) -> str:
        """
        Processes the mental health condition and returns a formatted string.
        """
        if quiz_state.get("current_question") > quiz_state.get("total_questions", 10):
            logger.info("Quiz completed")
            return "end"
        return "continue"

    def _process_judi_online(self, quiz_state: QuizState) -> QuizState:
        """
        Processes the judi online condition and returns a formatted string.
        """
        logger.info("Processing judi online condition for quiz generation")
        if quiz_state.get("current_question") is None:
            logger.info("Starting a new judi online quiz session")
            quiz_state["current_question"] = 1
        else:
            quiz_state["current_question"] += 1
            logger.info(f"Advancing to question {quiz_state['current_question']}")
        if quiz_state.get("total_questions") < quiz_state["current_question"]:
            return quiz_state
        question_type = self._generate_question_type()
        quiz_state["current_question_type"] = question_type
        return quiz_state
    
    def _generate_quiz_judi_online(self, quiz_state: QuizState) -> QuizState:
        """
        Generates a quiz based on the judi online condition.
        """
        logger.info("Generating judi online quiz")
        generate_judi_online_quiz_prompt_template = """
        You are a quiz generator for judi online awareness.
        The quiz should be engaging and informative. and make the user more aware of judi online.
        And can help the user to improve their judi online condition.
        
        And make sure there are no duplicates questions in the quiz.
        this is the questions history:
        {questions_history}

        and this is the quiz rules that you need to follow:
        difficulty: {difficulty}
        question_type: {question_type}
        Note:
            if the question_type is multiple_choice then you need to provide 4 possible answers (A, B, C, D) and only one correct answer.
            and only one correct answer is allowed.
            if the question_type is multiple_answer then you need to provide 4 possible answers (A, B, C, D) and at least two correct answers.
            and only two or three correct answers are allowed.
        """
        generate_judi_online_quiz_prompt = PromptTemplate(
            input_variables=["difficulty", "question_type", "questions_history"],
            template=generate_judi_online_quiz_prompt_template
        )

        generate_judi_online_quiz = generate_judi_online_quiz_prompt | self.llm.with_structured_output(QuestionModel)
        logger.info("Sending request to generate judi online quiz question")
        response = generate_judi_online_quiz.invoke({
            "difficulty": quiz_state.get("difficulty", "easy"),
            "question_type": quiz_state.get("current_question_type", "multiple_choice"),
            "questions_history": "\n".join([q["question"] for q in quiz_state.get("questions", [])])
        })
        response_dict = response.model_dump()
        logger.info(f"Generated question: {response_dict['question']}")
        quiz_state["questions"].append({
            "question": response_dict["question"],
            "possible_answers": {
                "A": response_dict["possible_answers"].get("A"),
                "B": response_dict["possible_answers"].get("B"),
                "C": response_dict["possible_answers"].get("C"),
                "D": response_dict["possible_answers"].get("D")
            },
            "question_type": quiz_state.get("current_question_type", "multiple_choice"),
            "correct_answer": response_dict["correct_answer"]
        })
        return quiz_state
    
    def _process_judi_online_condition(self, quiz_state: QuizState) -> str:
        """
        Processes the judi online condition and returns a formatted string.
        """
        if quiz_state.get("current_question") > quiz_state.get("total_questions", 10):
            logger.info("Quiz completed")
            return "end"
        return "continue"
    
    def _generate_quiz_title_and_description(self, QuizState: QuizState) -> QuizState:
        """
        Generates a title and description for the quiz based on the theme and difficulty.
        """
        class QuizTitleDescription(BaseModel):
            title: str = Field(description="Title of the quiz")
            description: str = Field(description="Description of the quiz")

        generate_quiz_title_description_prompt_template = """
        You are a quiz title and description generator.
        Generate a title and description for the quiz based on the theme and difficulty.
        The title should be catchy and relevant to the theme.
        The description should provide an overview of the quiz and its purpose.
        This is the theme of the quiz: {theme}
        This is the difficulty of the quiz: {difficulty}
        This is the questions:
        {questions_history}
        """
        generate_quiz_title_description_prompt = PromptTemplate(
            input_variables=["theme", "difficulty", "questions_history"],
            template=generate_quiz_title_description_prompt_template
        )
        generate_quiz_title_description = generate_quiz_title_description_prompt | self.llm.with_structured_output(QuizTitleDescription)
        response = generate_quiz_title_description.invoke({
            "theme": QuizState.get("theme", "mental_health"),
            "difficulty": QuizState.get("difficulty", "easy"),
            "questions_history": "\n".join([q["question"] for q in QuizState.get("questions", [])])
        })
        response_dict = response.model_dump()
        QuizState["quiz_title"] = response_dict["title"]
        QuizState["quiz_description"] = response_dict["description"]
        return QuizState

    
    def generate_quiz(self, theme: str, difficulty: str, user_condition_summary: Optional[str] = None, total_questions: int = 10) -> dict:
        """
        Generates a quiz based on the provided theme and difficulty.
        
        :param theme: The theme of the quiz (e.g., "mental_health", "judi_online")
        :param difficulty: The difficulty level of the quiz (e.g., "easy", "medium", "hard")
        :param user_condition_summary: Optional summary of the user's condition
        :param total_questions: Total number of questions in the quiz
        :return: QuizState containing the generated quiz questions
        """
        initial_state = {
            "theme": theme,
            "difficulty": difficulty,
            "user_condition_summary": user_condition_summary,
            "total_questions": total_questions,
            "current_question": None,
            "current_question_type": "multiple_choice",
            "questions": [],
            "quiz_title": None,
            "quiz_description": None
        }
        result = self.quiz_agent.invoke(initial_state)
        return {
            "quiz_title": result.get("quiz_title"),
            "quiz_description": result.get("quiz_description"),
            "questions": result.get("questions", [])
        } if result else {
            "quiz_title": None,
            "quiz_description": None,
            "questions": []
        }
    
quiz_agent = QuizAiAgent()

if __name__ == "__main__":
    quiz_agent = QuizAiAgent()
    quiz = quiz_agent.generate_quiz(
        theme="judi_online",
        difficulty="easy",
        user_condition_summary="User is feeling anxious and stressed.",
        total_questions=2
    )
    print(quiz)