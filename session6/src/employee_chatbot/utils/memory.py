import itertools
import json
import os
from typing import List
from bedrock_agentcore.memory import MemoryClient

class MemoryUtils:
    sessionId:str = None
    actorId:str = None

    def __init__(self, sessionId:str, actorId:str):
        self.sessionId = sessionId
        self.actorId = actorId

    def saveMemory(self, userPrompt:str, assistantResponse:str):
        userPrompt = userPrompt[:9000]
        assistantResponse = assistantResponse[:9000]
        
        payload = [
            [userPrompt, "USER"],
            [assistantResponse, "ASSISTANT"]
        ]

        params = {
            "memory_id": os.getenv("MEMORY_ID"),
            "actor_id": self.actorId,
            "session_id": self.sessionId,
            "messages": payload
        }
        MemoryClient().create_event(**params)

    def loadShortTermMemory(self, count:int=10) -> str:
        params = {
            "memory_id": os.getenv("MEMORY_ID"),
            "actor_id": self.actorId,
            "session_id": self.sessionId,
            "k": count
        }
        turns = MemoryClient().get_last_k_turns(**params)
        flattened_list = list(itertools.chain.from_iterable(turns))
        response = ""
        for item in flattened_list:
            response += item['role'] + ": " + item['content']['text'] + " \n\n"
        return response

        
