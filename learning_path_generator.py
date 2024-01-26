import ast
import json
import re

from api.openai_api import OpenAIAPI
from typing import Dict, List


class LearningPathGenerator:
    def __init__(self, openai_api: OpenAIAPI):
        self._openai_api = openai_api

    def generate_topics_curriculum_list(self, user_profile: Dict[str, str], subject: str) -> List[str]:
        profile_json = json.dumps(user_profile)

        learning_goal = user_profile.get("primary_goal", "")
        knowledge_level = user_profile.get("knowledge_level", "")

        standard_safe_response = ["Sorry, I can NOT generate harmful learning content"]

        prompts = [
            {
                "role": "system",
                "content": f"""You are an experienced Instructional Designer that is experienced in multiple subjects and disciplines.
In case you identify the subject: "{subject}" as HARMFUL or INAPPROPRIATE YOU MUST OUTPUT "{standard_safe_response}" and IMMEDIATELY STOP.
If the subject: "{subject}" is acceptable, then your MAIN objective is to generate a learning path of TOPIC TITLES for a user with the following profile: {profile_json}
"""
            },
            {
                "role": "user",
                "content": f"""Generate a Python list of strings representing a sequential learning curriculum for the "{subject}" topic STRICTLY FOLLOWING these rules:
1. If YOU IDENTIFY THE subject: "{subject}" as HARMFUL or INAPPROPRIATE, YOU MUST OUTPUT "{standard_safe_response}" and IMMEDIATELY STOP.
2. The FIRST item in the list SHOULD BE a foundational topic RELEVANT to the "{subject}" subject matter.
3. Subsequent items MUST follow in a LOGICAL and STRUCTURED order, reflecting an effective and smooth learning progression.
    - 3.1 The items MUST BE RELEVANT to the user's "{learning_goal}" learning goal and "{knowledge_level}" knowledge level.
    - 3.2 There MUST BE NO duplicate topics in the list.
4. The items MUST ONLY be the TITLES of the topics, WITHOUT descriptions or any additional text.
5. YOU MUST create a list of 10 items (NO MORE, NO LESS) relevant to the "{subject}" subject.
6. Ensure the list is relevant to the user profile and comprehensive to learn steadily about the "{subject}" subject matter.
7. YOUR OUTPUT MUST STRICTLY BE a Python list of 10 strings ['Topic 1', 'Topic 2', ...] WITHOUT any variable declarations in front!"""
            }
        ]

        response = self._openai_api.get_chat_completion(prompts)

        curriculum = self._extract_and_parse_list_from_response(response)

        return curriculum

    @staticmethod
    def _extract_and_parse_list_from_response(response: str) -> List[str]:
        if "```" in response:
            list_str = response.split("```")[1]
            if list_str.startswith("python"):
                list_str = list_str[6:].strip()
        else:
            list_str = response.strip()

        match = re.search(r'(?<=\=\s)\[.*\]', list_str) or re.search(r'\[.*\]', list_str)
        if match:
            list_str = match.group(0)

        try:
            parsed_list = ast.literal_eval(list_str)
            standard_safe_response = ["Sorry, I can NOT generate harmful learning content"]

            if parsed_list == standard_safe_response:
                return parsed_list

            if not isinstance(parsed_list, list) or len(parsed_list) != 10:
                raise ValueError("The output is not a valid list of 10 items.")
            return parsed_list
        except (SyntaxError, ValueError) as e:
            raise ValueError(f"Failed to parse the list from response: {list_str}\nError: {e}")

    def generate_topic_theory(self, user_profile: Dict[str, str], subject: str) -> str:
        study_time = user_profile.get("study_time_per_day", "")
        if study_time in ["Less than 30 minutes", "30 minutes to 1 hour"]:
            section_count = 2
            lines_per_section = "2 lines"
        elif study_time == "1 to 2 hours":
            section_count = 4
            lines_per_section = "4-5 lines"
        else:
            section_count = 5
            lines_per_section = "about 6-7 lines"

        prompts = [
            {
                "role": "system",
                "content": f"""You are an experienced Instructional Designer that is experienced in multiple subjects and disciplines. 
                Your MAIN objective is to generate COMPREHENSIVE but CONCISE theory explanation for the topic '{subject}'"""
            },
            {
                "role": "user",
                "content": f"""Create a structured theoretical topic on the "{subject}" topic, organized into sections STRICTLY FOLLOWING these rules:
1. The topic theory MUST BE FOCUSED on the "{subject}" topic.
2. The topic theory MUST HAVE {section_count} sections, each with a heading wrapped in h4 MARKDOWN TAGS that develops the content in a LOGICAL order.
    - 2.1 IT IS PROHIBITED TO USE 'Title:', 'Section 1:', 'Section 2:', before the section titles in the text. YOU MUST OUTPUT the section title DIRECTLY!
    - 2.2 Each section MUST ONLY HAVE {lines_per_section} of text.
3. Each section MUST HAVE theory that is COMPREHENSIVE yet CONCISE, WITHOUT filler content!
    - 3.1 Each theory section MUST ALWAYS FOLLOW a smooth transition from the previous section!
4. The final section MUST BE "Conclusion" recapping the main points of the topic.
5. Use clear and informative language suitable for someone new to the "{subject}".
6. YOU MUST use simple words and AVOID advanced vocabulary or formal expressions in the generated theory!
7. Output MUST STRICTLY be the topic theory content ONLY WITH NO ADDITIONAL REMARKS, CHATTY MESSAGES or META-TEXT!"""
            }
        ]

        response = self._openai_api.get_chat_completion(prompts)
        return response.strip()
