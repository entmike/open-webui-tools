"""
title: System Message Augmented Filter
author: Mike Howles
author_url: https://github.com/open-webui
funding_url: https://github.com/open-webui
version: 0.1
"""

import pytz
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class Filter:
    class Valves(BaseModel):
        location: str = Field(default="United States", description="Location")
        timezone: str = Field(default="America/Chicago", description="Time Zone")
        system_message: str = Field(
            default="""You are a casual and helpful system assistant.  
        You use humor when appropriate to convey concepts and information.  Your answers should be straightforward and concise.  Only elaborate if prompted to do so.

        The following context can be used in your replies, but only if the user mentions or asks about it up in the conversation.
        
        <context>
        - You are chatting with {{USER_NAME}}.
        - Current date: {{CURRENT_DATE}}
        - Current time: {{CURRENT_TIME}}
        - Time Zone: {{TIMEZONE}}
        - Current Location: {{USER_LOCATION}}
        </context>

        Do not personalize responses with this context unless it is relevant.
        
        """.replace(
                "\n", " "
            ).strip(),
            description="System Message",
        )
        pass

    class UserValves(BaseModel):
        location: str = Field(default="United States", description="Location")
        timezone: str = Field(default="America/Chicago", description="Time Zone")
        pass

    def __init__(self):
        self.valves = self.Valves()
        self.userValves = self.UserValves()
        pass

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        user_name = __user__["name"]
        user_location = __user__["valves"].location
        messages = body["messages"]
        # print(messages)
        system_prompt = next(
            (message for message in messages if message.get("role") == "system"),
            None,
        )
        if system_prompt:
            template = system_prompt["content"]
        else:
            # print("No system message.  Using fallback.")
            template = self.valves.system_message

        # Get the current date
        current_date = datetime.now()
        tz = pytz.timezone(__user__["valves"].timezone)
        local_date = current_date.astimezone(tz)

        # Format the date to YYYY-MM-DD
        formatted_date = local_date.strftime("%Y-%m-%d")
        formatted_time = local_date.strftime("%I:%M:%S %p")

        template = template.replace("{{CURRENT_DATE}}", formatted_date)
        template = template.replace("{{CURRENT_TIME}}", formatted_time)
        template = template.replace(
            "{{CURRENT_DATETIME}}", f"{formatted_date} {formatted_time}"
        )
        template = template.replace("{{TIMEZONE}}", self.valves.timezone)
        if user_name:
            # Replace {{USER_NAME}} in the template with the user's name
            template = template.replace("{{USER_NAME}}", user_name)
        else:
            # Replace {{USER_NAME}} in the template with "Unknown"
            template = template.replace("{{USER_NAME}}", "Unknown")

        if user_location:
            # Replace {{USER_LOCATION}} in the template with the current location
            template = template.replace("{{USER_LOCATION}}", user_location)
        else:
            # Replace {{USER_LOCATION}} in the template with "Unknown"
            template = template.replace("{{USER_LOCATION}}", "Unknown")

        system_prompt = next(
            (message for message in messages if message.get("role") == "system"), None
        )

        if system_prompt:
            system_prompt["content"] = template
        else:
            system_prompt = {"role": "system", "content": template}

        filtered_messages = []
        filtered_messages = [system_prompt] + [
            message for message in messages if message["role"] != "system"
        ]
        body["messages"] = filtered_messages
        return body
