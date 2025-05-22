from abc import ABC, abstractmethod

import anthropic


class AIClient(ABC):
    def __init__(self, api_key):
        self.client = self.create_client(api_key)

    @abstractmethod
    def create_client(self, api_key):
        pass

    @abstractmethod
    def send_message(self, message: str) -> str:
        pass


class ClaudeClient(AIClient):
    def __init__(self, api_key):
        super().__init__(api_key)

    def create_client(self, api_key):
        return anthropic.Anthropic(
            api_key=api_key,
        )

    def send_message(self, message: str):
        message = self.client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=5,
            messages=[
                {"role": "user", "content": message}
            ]
        )
        return message.content[0].text
