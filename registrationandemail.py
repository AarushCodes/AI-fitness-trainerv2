import tkinter as tk
from tkinter import ttk
import webbrowser
import customtkinter
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from openai import OpenAI
import datetime

key = 'YOUR_OPENAI_KEY'

def parse_workout_schedule(text):
    # Split the text into lines
    lines = text.split('\n')

    # Initialize an empty dictionary to store the workout schedule
    workout_schedule = {
        'Monday': None,
        'Tuesday': None,
        'Wednesday': None,
        'Thursday': None,
        'Friday': None,
        'Saturday': None,
        'Sunday': None
    }

    # Find the line containing the workouts
    for line in lines:
        if line.startswith('Workouts:'):
            workouts_line = line
            break

    # Extract the workouts
    workouts = workouts_line.split(': ')[1].split(', ')

    # Find the line containing the workout days
    for line in lines:
        if line.startswith('Workout Days:'):
            workout_days_line = line
            break

    # Extract the workout days
    workout_days = workout_days_line.split(': ')[1].split(', ')

    # Map workout days to workouts
    for day, workout in zip(workout_days, workouts):
        workout_schedule[day.strip()] = workout.strip()

    return workout_schedule

def get_today_workout(workout_schedule):
    # Get the current day of the week
    today = datetime.datetime.now().strftime('%A')

    # Get the workout for today, if any
    today_workout = workout_schedule.get(today)

    return today_workout


def get_tomorrow_workout(workout_schedule):
    # Get the current day of the week
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%A')

    # Get the workout for today, if any
    tomorrow_workout = workout_schedule.get(tomorrow)

    return tomorrow_workout

def get_yesterday_workout(workout_schedule):
    # Get the current day of the week
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%A')

    # Get the workout for today, if any
    yesterday_workout = workout_schedule.get(yesterday)

    return yesterday_workout



class SendEmail:
    def __init__(self, sender_email, apppassword):
        self.sender_email = sender_email
        self.apppassword = apppassword
    def Send_Email(self,recipient_email,subject,html_content,mode='html'):
        # Email configuration
            

        # Create a MIMEText object with HTML content
        '''
        html_content = """
        <html>
        <head></head>
        <body>
            <p>This  is your HTML email content.</p>
        </body>
        </html>
        """
        '''
        message = MIMEMultipart()
        if mode == 'html':
            message.attach(MIMEText(html_content, 'html'))
        else:
            message.attach(MIMEText(html_content, "plain"))
        # Set email headers
        message['From'] = self.sender_email
        message['To'] = recipient_email
        message['Subject'] = subject

        # Connect to the SMTP server (in this example, using Gmail)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "aarush.chirag@gmail.com"
        smtp_password = "bepk amjd xenu ganc"

        # Create a connection to the SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Start TLS for security
            server.starttls()

            # Log in to the SMTP server
            server.login(smtp_username, smtp_password)

            # Send the email
            server.sendmail(self.sender_email, recipient_email, message.as_string())

        print("Email sent successfully!")
        return True

client = OpenAI(api_key=key)

def askchatgpt(message):
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a dietician"},
        {"role": "user", "content": f"{message}"}
    ]
    )

    print(completion.choices[0].message)
    return completion.choices[0].message

email_sender = SendEmail(sender_email='aarush.chirag@gmail.com',apppassword='bepk amjd xenu ganc')

def generate_html(data,name):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{name}'s Data</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
            }}
            h1 {{
                color: #333;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>
        <h1>{name}'s Data</h1>
        <table>
            {data}
        </table>
    </body>
    </html>
    """
    with open('user_data.html', 'w') as html_file:
        html_file.write(html_content)
    return html_content

def calculate_bmr(weight, height, age, gender):
    if gender.lower() == 'male':
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    elif gender.lower() == 'female':
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    else:
        raise ValueError("Invalid gender. Use 'male' or 'female'.")
    return bmr

def calculate_tdee(bmr, active_days):
    if active_days <= 2:
        tdee = bmr * 1.375
    elif active_days <= 5:
        tdee = bmr * 1.55
    else:
        tdee = bmr * 1.725
    return tdee

def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def is_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False

def start():
    def submit_form():
        name = name_entry.get()
        email = email_entry.get()
        age = age_entry.get()
        gender = gender_var.get()
        height = height_entry.get()
        weight = weight_entry.get()
        diet_type = diet_type_var.get()
        food_preferences = food_preferences_entry.get()
        state = state_var.get()
        country = country_var.get()
        dietary_restrictions = dietary_restrictions_entry.get()

        if not (is_int(age) and is_float(height) and is_float(weight)):
            confirmation_label.configure(text="Invalid input for age, height, or weight. Please enter valid values.")
            return

        selected_days = [days_of_week[i] for i, day_var in enumerate(day_vars) if day_var.get()]
        workouts = []

        if len(selected_days) == 1:
            workouts.append("Full Body")
        elif len(selected_days) == 2:
            workouts.extend(["Upper Body", "Lower Body"])
        elif len(selected_days) == 3:
            workouts.extend(["Full Body", "Upper Body", "Lower Body"])
        elif len(selected_days) == 4:
            workouts.extend(["Upper Body", "Upper Body"])
        elif len(selected_days) == 5:
            workouts.extend(["Upper Body", "Lower Body", "Full Body", "Upper Body", "Lower Body"])
        elif len(selected_days) == 7:
            workouts.extend(["Full Body", "Upper Body", "Lower Body", "Full Body", "Upper Body", "Lower Body", "Full Body"])

        fitness_goal = fitness_goal_var.get()
        bmr = calculate_bmr(int(weight), float(height), int(age), gender)
        tdee = calculate_tdee(bmr, len(selected_days))

        if fitness_goal == 'Lose Weight' or fitness_goal == 'Both(Weight loss and Gain Muscle)':
            recommended_calories = tdee * 85 / 100
        elif fitness_goal =='Gain Muscle':
            recommended_calories = tdee * 115/100
        else:
            recommended_calories = tdee

        with open('user_data.txt', 'a') as file:
            file.write(f"Name: {name}\n")
            file.write(f"Email: {email}\n")
            file.write(f"Age: {age}\n")
            file.write(f"Gender: {gender}\n")
            file.write(f"Height: {height}\n")
            file.write(f"Weight: {weight}\n")
            file.write(f"Dietary Information:\n")
            file.write(f"    Diet Type: {diet_type}\n")
            file.write(f"    Food Preferences: {food_preferences}\n")
            file.write(f"    Dietary Restrictions: {dietary_restrictions}\n")
            file.write(f"Location:\n")
            file.write(f"    State: {state}\n")
            file.write(f"    Country: {country}\n")
            file.write(f"Fitness Details:\n")
            file.write(f"    Number of Workout Days: {len(selected_days)}\n")
            file.write(f"    Workout Days: {', '.join(selected_days)}\n")
            file.write(f"    Workouts: {', '.join(workouts)}\n")
            file.write(f"   Fitness Goal: {fitness_goal}\n")
            file.write(f"    BMR: {bmr}\n")
            file.write(f"    No of calories burnt in day (including workout)/TDEE: {tdee}\n")
            file.write(f"    Recommended Calorie intake: {recommended_calories}\n")
            file.write("\n")

        confirmation_label.configure(text="Making your personalized meal plan, saving your data and sending both to your email!")
        html_data = ""
        with open('user_data.txt', 'r') as file:
            firsttime = True
            for line in file:
                parts = line.strip().split(':')
                if len(parts) >= 2:
                    if firsttime:
                        name = parts[1].strip()
                        html_data += f"<tr><td>{parts[0]}</td><td>{parts[1]}</td></tr>\n"
                        firsttime = False
                    elif parts[1].strip() == '':
                        html_data += f"<tr><td><b>{parts[0]}</b></td><td>{parts[1]}</td></tr>\n"
                    else:
                        html_data += f"<tr><td>{parts[0]}</td><td>{parts[1]}</td></tr>\n"
        if diet_type == 'Vegetarian':
            diet_type_for_query = 'Vegetarian,does not eat eggs,no omelette'
        location = f'{country},{state}'
        html_content = generate_html(html_data,name)
        diet_plan_query = f'''Generate a 7-day meal plan for:
    1. Diet type: {diet_type_for_query}
    2. Food preferences: {food_preferences}
    3. daily Calorie goal: {recommended_calories}
    4. Fitness goal: {fitness_goal}
    5. Dietary restrictions: {dietary_restrictions}
    6: Location: {location}

    Ensure variety, nutrition, and alignment with diet type, preferences, restrictions, Foods easily available at the location fitness goals, calorie goals. Aim for balanced macronutrient distribution. inculde number of calories for each meal
    Note: output only the meal plan, no header,footer'''
        print(diet_plan_query)
        meal_plan = askchatgpt(diet_plan_query)
        with open('meal_plan.txt', 'w') as file:
            file.write(meal_plan.content)
        view_button.configure(state=tk.NORMAL)
        email_sender.Send_Email(recipient_email=email,subject=f"{name}'s data",html_content=html_content)
        email_sender.Send_Email(recipient_email=email,subject=f"{name}'s personalized meal plan",html_content=meal_plan.content,mode='text')
        confirmation_label.configure(text="Completed Successfully! Now you can close this and restart the program.")
    def open_in_browser():
        webbrowser.open('user_data.html')

    # Create main window
    root = customtkinter.CTk()
    root.title("User Registration Form")

    # Create and place form elements
    customtkinter.CTkLabel(root, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    name_entry = customtkinter.CTkEntry(root)
    name_entry.grid(row=0, column=1, padx=10, pady=10)

    customtkinter.CTkLabel(root, text="Email:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    email_entry = customtkinter.CTkEntry(root)
    email_entry.grid(row=1, column=1, padx=10, pady=10)

    customtkinter.CTkLabel(root, text="Age:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
    age_entry = customtkinter.CTkEntry(root)
    age_entry.grid(row=2, column=1, padx=10, pady=10)

    customtkinter.CTkLabel(root, text="Gender:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
    gender_var = customtkinter.StringVar()
    gender_combobox = customtkinter.CTkOptionMenu(root, variable=gender_var, values=['Male', 'Female'], state="readonly")
    gender_combobox.grid(row=3, column=1, padx=10, pady=10)

    customtkinter.CTkLabel(root, text="Height(cms):").grid(row=4, column=0, padx=10, pady=10, sticky="w")
    height_entry = customtkinter.CTkEntry(root)
    height_entry.grid(row=4, column=1, padx=10, pady=10)

    customtkinter.CTkLabel(root, text="Weight(kgs):").grid(row=5, column=0, padx=10, pady=10, sticky="w")
    weight_entry = customtkinter.CTkEntry(root)
    weight_entry.grid(row=5, column=1, padx=10, pady=10)

    customtkinter.CTkLabel(root, text="Diet Type:").grid(row=6, column=0, padx=10, pady=10, sticky="w")
    diet_type_var = customtkinter.StringVar()
    diet_type_combobox = customtkinter.CTkOptionMenu(root, variable=diet_type_var, values=['Vegetarian', 'Non-veg', 'Vegan', 'Eggetarian', 'Keto'], state="readonly")
    diet_type_combobox.grid(row=6, column=1, padx=10, pady=10)

    customtkinter.CTkLabel(root, text="Food Preferences:").grid(row=7, column=0, padx=10, pady=10, sticky="w")
    food_preferences_entry = customtkinter.CTkEntry(root)
    food_preferences_entry.grid(row=7, column=1, padx=10, pady=10)

    customtkinter.CTkLabel(root, text="Country:").grid(row=8, column=0, padx=10, pady=10, sticky="w")
    country_var = customtkinter.StringVar()
    country_entry = customtkinter.CTkEntry(root, textvariable=country_var)
    country_entry.grid(row=9, column=1, padx=10, pady=10)

    customtkinter.CTkLabel(root, text="State:").grid(row=9, column=0, padx=10, pady=10, sticky="w")
    state_var = customtkinter.StringVar()
    state_entry = customtkinter.CTkEntry(root, textvariable=state_var)
    state_entry.grid(row=8, column=1, padx=10, pady=10)



    customtkinter.CTkLabel(root, text="Dietary Restrictions:").grid(row=10, column=0, padx=10, pady=10, sticky="w")
    dietary_restrictions_entry = customtkinter.CTkEntry(root)
    dietary_restrictions_entry.grid(row=10, column=1, padx=10, pady=10)

    customtkinter.CTkLabel(root, text="Workout Days:").grid(row=11, column=0, padx=10, pady=10, sticky="w")
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_vars = [tk.IntVar() for _ in days_of_week]
    for i, day in enumerate(days_of_week):
        customtkinter.CTkCheckBox(root, text=day, variable=day_vars[i]).grid(row=11, column=i+1, padx=5, pady=5, sticky="w")

    customtkinter.CTkLabel(root, text="Fitness Goal:").grid(row=12, column=0, padx=10, pady=10, sticky="w")
    fitness_goal_var = customtkinter.StringVar()
    fitness_goal_combobox = customtkinter.CTkOptionMenu(root, variable=fitness_goal_var, values=['Lose Weight', 'Gain Muscle', 'Both(Weight loss and Gain Muscle)', 'Staying Fit/Maintainence'], state="readonly")
    fitness_goal_combobox.grid(row=12, column=1, columnspan=2, padx=10, pady=10)

    confirmation_label = customtkinter.CTkLabel(root, text="")
    confirmation_label.grid(row=13, column=0, columnspan=3)

    submit_button = customtkinter.CTkButton(root, text="Submit", command=submit_form)
    submit_button.grid(row=14, column=0, columnspan=3, pady=20)

    # Add a button to view details in a browser
    view_button = customtkinter.CTkButton(root, text="View Details in Browser", command=open_in_browser, state=tk.DISABLED)
    view_button.grid(row=14, column=2, columnspan=3, pady=10)
        
    # Start the GUI main loop
    root.mainloop()
