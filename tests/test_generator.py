import unittest
from unittest.mock import MagicMock
from src.agents.generator import Generator
from src.core.engine import CognitiveEngine

class TestGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_engine = MagicMock(spec=CognitiveEngine)
        self.generator = Generator(self.mock_engine)

    def test_generate_with_memories(self):
        user_query = "How to make a cake?"
        context_memories = ["Cake needs flour.", "Cake needs sugar."]
        self.mock_engine.generate.return_value = "Drafted solution for cake."

        result = self.generator.generate(user_query, context_memories)

        expected_prompt = "Context Memories:\nCake needs flour.\nCake needs sugar.\n\nTask:\nHow to make a cake?\n\nDraft a comprehensive solution:"
        self.mock_engine.generate.assert_called_once_with(
            prompt=expected_prompt,
            system_prompt=self.generator.system_prompt,
            temperature=0.7
        )
        self.assertEqual(result, "Drafted solution for cake.")

    def test_generate_without_memories(self):
        user_query = "How to make a cake?"
        context_memories = []
        self.mock_engine.generate.return_value = "Drafted solution for cake."

        result = self.generator.generate(user_query, context_memories)

        expected_prompt = "Context Memories:\nNo prior memories.\n\nTask:\nHow to make a cake?\n\nDraft a comprehensive solution:"
        self.mock_engine.generate.assert_called_once_with(
            prompt=expected_prompt,
            system_prompt=self.generator.system_prompt,
            temperature=0.7
        )
        self.assertEqual(result, "Drafted solution for cake.")

    def test_generate_with_none_memories(self):
        user_query = "How to make a cake?"
        context_memories = None
        self.mock_engine.generate.return_value = "Drafted solution for cake."

        result = self.generator.generate(user_query, context_memories)

        expected_prompt = "Context Memories:\nNo prior memories.\n\nTask:\nHow to make a cake?\n\nDraft a comprehensive solution:"
        self.mock_engine.generate.assert_called_once_with(
            prompt=expected_prompt,
            system_prompt=self.generator.system_prompt,
            temperature=0.7
        )
        self.assertEqual(result, "Drafted solution for cake.")
