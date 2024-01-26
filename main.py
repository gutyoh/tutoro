import streamlit as st
from api.openai_api import OpenAIAPI
from learning_path_generator import LearningPathGenerator

OTHER_SPECIFY = "Other (please specify)"


class TuturoApp:
    def __init__(self):
        self.openai_api = None
        self.openai_api_key = None
        self.openai_model = "gpt-3.5-turbo-1106"

        self.learning_path_generator = None

        self.initialize_openai_api()
        self.initialize_session_state()
        self.onboarding_questions = self.define_onboarding_questions()
        self.additional_questions = self.define_additional_questions()
        initial_topics = self.define_topics()
        self.topics = initial_topics + [OTHER_SPECIFY]

    def initialize_openai_api(self):
        self.openai_api_key = st.sidebar.text_input("Enter your OpenAI API Key below!", type="password").strip()
        if not self.openai_api_key:
            st.error("Please enter a valid OpenAI API key in the sidebar to proceed!")
            st.stop()

        self.openai_api = OpenAIAPI(self.openai_api_key, self.openai_model)
        self.learning_path_generator = LearningPathGenerator(self.openai_api)

    @staticmethod
    def initialize_session_state():
        if 'onboarding_completed' not in st.session_state:
            st.session_state['onboarding_completed'] = False
            st.session_state['user_profile'] = {}
            st.session_state['selected_topic'] = None

            if 'sub_curriculums' not in st.session_state:
                st.session_state['sub_curriculums'] = {}

    @staticmethod
    def define_onboarding_questions():
        return [
            {"key": "age_group", "question": "What is your age group?",
             "options": ["Under 18 👶", "18-35 🧑", "36-50 👨", "51 or older 👴"]},
            {"key": "educational_background", "question": "What is your educational background?",
             "options": ["High school 🎒", "Bachelor's degree 🎓", "Master's degree 🏫", "Doctorate or higher 🔬"]},
            {"key": "preferred_learning_resources", "question": "What type of learning resources do you prefer?",
             "options": ["Text content (theory topics) 📚", "Video content (videos, info-graphics) 📺",
                         "Interactive content (quizzes, tests) ⌨️", "All mentioned before 📊"]}
        ]

    @staticmethod
    def define_topics():
        return [
            "House Plants", OTHER_SPECIFY, "Product Management",
            "Math", "History", "Languages", "Science",
            "Geography", "Computer Science", "Business", "Art", "P.E.",
            "Literature", "Music", "Self-improvement", "Health", "Psychology",
            "Technology", "Creativity", "Social Sciences", "Teenage Mutant Ninja Turtles",
        ]

    @staticmethod
    def define_additional_questions():
        return [
            {"key": "primary_goal", "question": "What is your primary learning goal?",
             "options": ["Personal interest", "Professional development", "Curiosity"]},
            {"key": "knowledge_level", "question": "How well do you know this subject already?",
             "options": ["Beginner", "Intermediate", "Advanced"]},
            {"key": "study_time_per_day", "question": "How much time do you want to study per day?",
             "options": ["Less than 30 minutes", "1 to 2 hours", "More than 2 hours"]}
        ]

    def onboarding_quiz(self):
        st.title("Onboarding Quiz")
        for question in self.onboarding_questions:
            response = st.radio(question["question"], question["options"])
            st.session_state.user_profile[question["key"]] = response
        if st.button('Complete Onboarding'):
            st.session_state.onboarding_completed = True

    def display_topic_selection_and_additional_questions(self):
        st.sidebar.title("Learning Path Selection")
        selected_topic = st.sidebar.selectbox(
            "Choose a subject you want to learn about:",
            options=self.topics
        )

        custom_topic = ""
        if selected_topic == OTHER_SPECIFY:
            custom_topic = st.sidebar.text_input("Please specify your subject")
            selected_topic = custom_topic if custom_topic else OTHER_SPECIFY

        st.session_state['selected_topic'] = selected_topic

        for question in self.additional_questions:
            response = st.sidebar.selectbox(question["question"], question["options"])
            st.session_state.user_profile[question["key"]] = response

        if st.sidebar.button('Generate Curriculum'):
            user_profile = st.session_state.user_profile
            curriculum_data = self.learning_path_generator.generate_topics_curriculum_list(
                user_profile,
                custom_topic if custom_topic else selected_topic
            )

            if curriculum_data[0].startswith("Sorry"):
                st.error(
                    "😕 Sorry, I cannot generate harmful learning content. Please try again using another subject.\n"
                    "However, if you think this is a mistake/false positive please click on the Generate Curriculum button again!",
                    icon="⚠️"
                )
                return

            if selected_topic not in st.session_state['sub_curriculums']:
                st.session_state['sub_curriculums'][selected_topic] = {
                    "curriculum": [],
                    "current_topic": None,
                    "topic_index": 0,
                    "topic_theories": {},
                    "visited_topics": set(),
                    "topic_states": {}
                }

            curriculum_info = st.session_state['sub_curriculums'][selected_topic]
            curriculum_info['curriculum'] = curriculum_data
            curriculum_info['current_topic'] = None
            curriculum_info['topic_index'] = 0
            curriculum_info['topic_theories'] = {topic: None for topic in curriculum_data}
            curriculum_info['visited_topics'] = set()
            curriculum_info['topic_states'] = {}
            st.session_state.view_curriculum = True
            st.rerun()

    def display_curriculum(self):
        st.title(f"Your Custom Curriculum for: {st.session_state['selected_topic']}")
        selected_topic = st.session_state['selected_topic']

        if selected_topic not in st.session_state['sub_curriculums']:
            st.warning("Please generate a curriculum first.")
            return

        curriculum_info = st.session_state['sub_curriculums'].get(selected_topic)

        if not curriculum_info or "curriculum" not in curriculum_info or not curriculum_info['curriculum']:
            st.warning("Curriculum data is missing or incomplete.")
            return

        curriculum = curriculum_info['curriculum']

        for idx, topic in enumerate(curriculum):
            topic_state = curriculum_info['topic_states'].get(topic, "")
            label = self.generate_topic_label(topic, topic_state)

            if st.button(label):
                curriculum_info['current_topic'] = topic
                curriculum_info['topic_index'] = idx
                curriculum_info['visited_topics'].add(topic)
                curriculum_info['topic_states'][topic] = "in_progress"
                st.session_state.view_curriculum = False
                st.rerun()

    @staticmethod
    def generate_topic_label(topic, state):
        state_icon = {
            "completed": "✅",
            "in_progress": "⏳",
            "to_retry": "⚠️"
        }.get(state, "")
        return f"{topic} {state_icon}"

    @staticmethod
    def navigate_topics():
        if 'selected_topic' in st.session_state:
            curriculum_info = st.session_state['sub_curriculums'][st.session_state['selected_topic']]
            curriculum = curriculum_info['curriculum']
            topic_index = curriculum_info['topic_index']

            col1, col2 = st.columns([1, 1])

            if topic_index > 0 and col1.button(f'← Previous: {curriculum[topic_index - 1]}'):
                curriculum_info['topic_index'] -= 1
                curriculum_info['current_topic'] = curriculum[curriculum_info['topic_index']]
                st.rerun()

            if topic_index < len(curriculum) - 1 and col2.button(f'Next: {curriculum[topic_index + 1]} →'):
                curriculum_info['topic_index'] += 1
                curriculum_info['current_topic'] = curriculum[curriculum_info['topic_index']]
                st.rerun()

            if st.button('🔙 Back to Curriculum Overview'):
                curriculum_info['current_topic'] = None
                curriculum_info['topic_index'] = 0
                st.session_state.view_curriculum = True
                st.rerun()

    def display_theory(self):
        selected_topic = st.session_state.get('selected_topic')

        if not selected_topic or selected_topic not in st.session_state['sub_curriculums']:
            st.warning("Please select a topic and generate a curriculum first.")
            return

        curriculum_info = st.session_state['sub_curriculums'][selected_topic]

        if not curriculum_info or not curriculum_info.get('curriculum'):
            st.error(
                "There seems to be an issue with the curriculum data for this topic. Please regenerate the curriculum.")
            return

        current_topic = curriculum_info.get('current_topic')

        if current_topic is None:
            st.info("Please select a topic from the curriculum to view its theory.")
            if st.button('🔙 Back to Curriculum Overview'):
                curriculum_info['current_topic'] = None
                curriculum_info['topic_index'] = 0
                st.session_state.view_curriculum = True
                st.rerun()
            return

        if current_topic not in curriculum_info['topic_theories'] or curriculum_info['topic_theories'][
            current_topic] is None:
            theory = self.learning_path_generator.generate_topic_theory(st.session_state.user_profile, current_topic)
            curriculum_info['topic_theories'][current_topic] = theory
        else:
            theory = curriculum_info['topic_theories'][current_topic]

        st.title(f"{current_topic}")
        st.write(theory)

        if st.button("Take Quiz"):
            st.write("Quiz functionality coming soon!")

        self.navigate_topics()

    def run(self):
        if not st.session_state.onboarding_completed:
            self.onboarding_quiz()
        else:
            self.display_topic_selection_and_additional_questions()
            if 'view_curriculum' in st.session_state and st.session_state.view_curriculum:
                self.display_curriculum()
            else:
                self.display_theory()


if __name__ == "__main__":
    tuturo_app = TuturoApp()
    tuturo_app.run()
