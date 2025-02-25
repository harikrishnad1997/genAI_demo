# from openai import OpenAI
import google.generativeai as genai
from ics import Calendar, Event
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
import os
import pytz


# Load environment variables from .env file
load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  }
]

def get_time_blocked_schedule(tasks: str, preferences: str, start_time=None):
    if start_time is None: # default to the next half hour
        now = datetime.now()
        minute = (now.minute // 30 + 1) * 30 % 60
        hour = now.hour + (now.minute // 30 + 1) // 2
        start_time = now.replace(minute=minute, hour=hour, second=0, microsecond=0).strftime("%H:%M")
    
    prompt = f"""
    Break down the following tasks into specific 30-minute or 60-minute tasks based on their size, adding 15-min breaks every 90 minutes. Include start and end times, using the provided start time as a reference. 
    If start time is not mentioned, assume a start time based on the activity.
    Tasks: {tasks}
    Preferences: {preferences}
    Starting Time: {start_time}

    Respond with a schedule in a structured format suitable for creating a calendar file (e.g., Task Name, Start Time, End Time).
    Use 24 hour notation for times to make it unambiguous.
    Directly and only answer with the follow format:
    1. Task: Research for Report
    Start: 09:00
    End: 09:30

    2. Task: Write Draft
    Start: 09:30
    End: 10:00
    ...
    """

    # client = OpenAI()
    # response = client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=[
    #         {"role": "user", "content": prompt}
    #         ]
    # )
    model = genai.GenerativeModel(model_name="gemini-2.0-flash-001",
                              generation_config=generation_config,
                              safety_settings=safety_settings)
    response = model.generate_content(prompt)
    return response.text

def create_ics_file(schedule_text, file_name="Daily_Schedule.ics"):
    # Initialize the calendar
    calendar = Calendar()
    
    # Assume all tasks are scheduled for today
    today = datetime.now().date()

    # Define the EST Timezone
    est = pytz.timezone('US/Eastern')

    # Parsing the GPT response
    for line in schedule_text.splitlines():
        if "Task:" in line:
            task_name = line.split(": ")[1].strip()
        elif "Start:" in line:
            start_time_str = line.split(": ")[1].strip()
            # Parse the start time, adding today's date
            start_time = est.localize(datetime.strptime(f"{today} {start_time_str}", "%Y-%m-%d %H:%M"))
        elif "End:" in line:
            end_time_str = line.split(": ")[1].strip()
            # Parse the end time, adding today's date
            end_time = est.localize(datetime.strptime(f"{today} {end_time_str}", "%Y-%m-%d %H:%M"))
            
            # Create a calendar event
            event = Event()
            event.name = task_name
            event.begin = start_time
            event.end = end_time
            calendar.events.add(event)

    # Write to .ics file
    with open(file_name, "w") as f:
        f.writelines(calendar)

    return file_name

# User input section
st.title("Daily Productivity Planner with Calendar Export")
tasks = st.text_area("Enter your goals for the day")
preferences = st.text_area("Any additional preferences? (e.g., start time, break intervals)")
start_time = st.text_input("[Optional]: Preferred Start Time (HH:MM)")

# Button to generate schedule and export
if st.button("Generate Schedule and Export to Calendar"):
    # Generate schedule text
    schedule_text = get_time_blocked_schedule(tasks, preferences, start_time)
    st.write("### Your Optimized Schedule")
    st.write(schedule_text)

    # Create and download .ics file
    file_name = create_ics_file(schedule_text)
    with open(file_name, "rb") as f:
        st.download_button("Download Calendar File", f, file_name, "text/calendar")
