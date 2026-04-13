import json


class MockAIClient:
    def __init__(self):
        self.call_count = 0

    def chat_completion(self, messages, **kwargs):
        self.call_count += 1
        if self.call_count == 1:
            class MockResponse:
                def __init__(self):
                    class Choice:
                        def __init__(self):
                            class Message:
                                def __init__(self):
                                    self.content = "التفكير: fake block ```python\npass\n``` الناتج: done"
                                    self.tool_calls = []
                            self.message = Message()
                    self.choices = [Choice()]
            return MockResponse()

        class MockResponse:
            def __init__(self):
                class Choice:
                    def __init__(self):
                        class Message:
                            def __init__(self):
                                self.content = "التفكير: سأستخدم الأداة"
                                class ToolCall:
                                    def __init__(self):
                                        self.id = "call_123"
                                        class Func:
                                            def __init__(self):
                                                self.name = "trigger_jules_autonomous_agent"
                                                self.arguments = json.dumps({"task_type": "general", "plan": "test"})
                                        self.function = Func()
                                self.tool_calls = [ToolCall()]
                        self.message = Message()
                self.choices = [Choice()]
        return MockResponse()


def test_sentinel_logic():
    attempts = 0
    max_sentinel_retries = 2
    require_high = True
    messages = [{"role": "user", "content": "test"}]
    ai_client = MockAIClient()

    tool_calls = []
    while attempts <= max_sentinel_retries:
        response = ai_client.chat_completion(messages=messages, require_high_capability=require_high)
        content = response.choices[0].message.content
        tool_calls = response.choices[0].message.tool_calls

        has_fake_results = ("```" in content or "Result:" in content or "الناتج:" in content)
        if not tool_calls and has_fake_results and require_high:
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": "CRITICAL ERROR: Use the tool!"})
            attempts += 1
            continue
        break

    assert attempts == 1
    assert tool_calls
    assert tool_calls[0].function.name == "trigger_jules_autonomous_agent"
