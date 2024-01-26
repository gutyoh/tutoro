from openai import OpenAI


class OpenAIAPI:
    def __init__(self, openai_api_key: str, openai_model: str):
        self.__openai_model = openai_model
        self.__openai_client = OpenAI(
            api_key=openai_api_key,
        )

    def get_chat_completion(self, messages: list[dict[str, str]]) -> str:
        return (
            self.__openai_client.chat.completions.create(
                messages=messages,
                model=self.__openai_model,
            )
            .choices[0]
            .message.content
        )

    def get_model(self):
        return self.__openai_model
