import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import time

import bot


class TestBotCommands(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.ctx_mock = MagicMock()
        self.ctx_mock.send = AsyncMock()
        bot.ulubione_widoki.clear()

    @patch(
        "bot.views",
        {
            "morskie_oko": [
                {
                    "name": "morskie_oko",
                    "full_name": "Morskie Oko",
                    "link": "https://example.com/morskie_oko.jpeg",
                }
            ]
        },
    )
    async def test_widok_valid_single_camera(self):
        await bot.widok(self.ctx_mock, "morskie_oko")
        self.ctx_mock.send.assert_any_call(
            "Aby dodać ten widok do ulubionych, użyj komendy: !dodaj_ulubione w odpowiedzi na tę wiadomość."
        )

    async def test_ulubione_tatry_empty(self):
        await bot.ulubione_tatry(self.ctx_mock)
        self.ctx_mock.send.assert_called_once_with(
            "📭 Nie masz żadnych ulubionych widoków."
        )

    async def test_ulubione_tatry_nonempty(self):
        bot.ulubione_widoki.append(
            {
                "name": "morskie_oko",
                "full_name": "Morskie Oko",
                "link": "https://example.com/morskie_oko.jpeg",
            }
        )
        await bot.ulubione_tatry(self.ctx_mock)

        found = False
        for call in self.ctx_mock.send.call_args_list:
            if "Morskie Oko" in call.args[0]:
                found = True
                break
        self.assertTrue(found)
