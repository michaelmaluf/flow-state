from abc import ABC, abstractmethod

import anthropic


class AIClient(ABC):
    def __init__(self):
        self.client = self.create_client()

    @abstractmethod
    def create_client(self):
        pass

    @abstractmethod
    def send_message(self, message: str) -> str:
        pass


class ClaudeClient(AIClient):
    def __init__(self):
        super().__init__()

    def create_client(self):
        return anthropic.Anthropic(
            api_key="CLAUDE_API_KEY",
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
