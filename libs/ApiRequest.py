import json
import sys
import logging
import requests
from logging.handlers import RotatingFileHandler
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from io import BytesIO
import os
from tkinter import simpledialog



#LOG File for Debugging Purpose

log_file = "../logs/app.log"
max_log_size = 5 * 1024 * 1024  # 5 MB (You can adjust this value based on your needs)
backup_count = 3  # Keep 3 backup files


logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format='%(asctime)s - %(levelname)s - %(message)s',  # Format for the logs
    handlers=[

        RotatingFileHandler(log_file, maxBytes=max_log_size, backupCount=backup_count),  # Log to a file with rotation

    ]
)


#API Key Fetch Code
try:
    with open("../apikey/API_KEY.txt", "r") as api_key_file:
        api_key = api_key_file.read()
        logging.info("API key successfully loaded.")

except FileNotFoundError:
    print("API file not found")
    logging.error("API key file not found.")
    sys.exit()



#Checking Internet Connection
def checkInternetConnection():
    try:
        logging.info("Checking internet connection...")
        response = requests.get("https://8.8.8.8", timeout=5)

        if response.status_code == 200 :
            logging.info("Internet connection is available.")
            return True
        else :
            logging.warning(f"Internet connection check failed with status code {response.status_code}.")
            return False
    except requests.ConnectionError as e:
        logging.error(f"Internet connection check failed: {e}")  # Log error if connection fails
        return False



#Getting IP Address
def getIP():
    try:
        logging.info("Fetching IP address...")
        response_ip = requests.get('https://httpbin.org/ip')
        ip_address = response_ip.json()['origin']
        return ip_address
    except requests.RequestException as e:
        logging.error(f"Error fetching IP address: {e}")  # Log error if IP fetch fails
        return None



#Fetching Data from Internet
def getData(args):
    try :
        host = "https://api.weatherapi.com/v1"
        path = "/current.json"
        url = f"{host}{path}?key={api_key}&q={args}"
        weather_response_data = requests.get(url)
        status_code = weather_response_data.status_code
        print(f"Status Code: {status_code}")
        if status_code == 200:
            logging.info("Data successfully retrieved from API.")
            return weather_response_data.json()  # Return JSON data if successful
        elif status_code == 400:
            logging.warning("Bad Request - Invalid parameters or missing data.")
            return {"error": "Bad Request - Invalid parameters or missing data"}
        else:
            logging.error(f"Error {status_code} - Location is incorrect or server issue.")
            return {"error": f"Error {status_code} - Location is incorrect or server issue"}
    except requests.RequestException as e:
        logging.error(f"Error making API request: {e}")  # Log any exception raised during the API request
        return {"error": f"Request Exception: {e}"}



#Extracting Weather Data
def extract_weather_data(data):
    logging.info("Extracting weather data...")  # Log data extraction
    """Extract specific weather details from the JSON response."""
    return {
        "Location Name": data['location']['name'],
        "Local Time": data['location']['localtime'],
        "Condition": data['current']['condition']['text'],
        "Condition Icon URL": data['current']['condition']['icon'],
        "Condition Code": data['current']['condition']['code'],
        "Wind Speed (kph)": data['current']['wind_kph'],
        "Humidity (%)": data['current']['humidity'],
        "Feels Like (°C)": data['current']['feelslike_c'],
        "UV Index": data['current']['uv'],
        "Temp Celsius":data['current']['temp_c']
    }
values_for_data_extraction = dict()



#Getting Pre Weather Data
def preWeatherData():
    global values_for_data_extraction
    logging.info("Starting weather data retrieval process...")
    if not checkInternetConnection():
        logging.error("Internet connection is not available.")
        print("Internet Connection is not available ")
        return

    ip = getIP()
    print(ip)
    weather_fetched_data = getData(ip)
    if "error" in weather_fetched_data:
        logging.error(f"Error in getting weather data: {weather_fetched_data['error']}")
        print(weather_fetched_data["error"])  # Print the error message
    else:
        values_for_data_extraction = extract_weather_data(weather_fetched_data)
        for key, value in extract_weather_data(weather_fetched_data).items():
            print(f"{key} : {value}")
            logging.info(f"{key} : {value}")



# Define the image_label globally
image_label = None
def display_image(url_or_path):
    global image_label  # Access the global image_label

    # Check if the input is a local file path
    if os.path.isfile(url_or_path):
        # Load the image from the local file system
        image = Image.open(url_or_path)
    else:
        # Fetch image from URL
        response = requests.get(url_or_path)
        image_data = response.content
        image = Image.open(BytesIO(image_data))

    # Resize the image (if needed)
    image = image.resize((250, 250), Image.LANCZOS)

    # Convert the Image object to a format tkinter can use
    tk_image = ImageTk.PhotoImage(image)

    # If image_label exists, update the image
    if image_label:
        image_label.config(image=tk_image)  # Update the image
        image_label.image = tk_image  # Update the image reference
    else:
        # If image_label does not exist yet, create it
        image_label = tk.Label(window, image=tk_image)
        image_label.image = tk_image  # Store the image reference
        image_label.pack()


#Custom Dialog Box Created by developer
def custom_dialog() -> str:
    # Define user_input to ensure it's available for returning
    user_input = None  # Initialize user_input

    # Create a new Toplevel window for the custom dialog box
    dialog = tk.Toplevel(window)
    dialog.geometry("400x200")  # Set the size of the dialog box (Width x Height)
    dialog.title("City")
    dialog.focus_set()

    # Add a label asking for input
    title_label = tk.Label(dialog, text="Enter the city name:", font=("Arial", 14))
    title_label.pack(pady=10)

    # Add an Entry widget for text input
    entry = tk.Entry(dialog, font=("Arial", 14))
    entry.pack(pady=10)

    entry.focus_set()

    # Function to handle the input and close the dialog
    def submit():
        nonlocal user_input
        user_input = entry.get()  # Set the user_input value
        if user_input:
            print(f"User input: {user_input}")
            fetchUserData(user_input)
        dialog.destroy()  # Close the dialog

    # Add a button to submit the input
    submit_button = tk.Button(dialog, text="Submit", command=submit, font=("Arial", 12))
    submit_button.pack(pady=10)

    dialog.grab_set()  # Prevent interaction with other windows while the dialog is open
    dialog.wait_window()  # Wait until the dialog is closed

    return user_input or ""  # Return the user input or an empty string



#Fetching Data Input by user
def fetchUserData(arg):
    # Fetch weather data for the city entered by the user
    print(f"Fetching weather data for: {arg}")

    weather_fetched_data = getData(arg)
    if "error" in weather_fetched_data:
        logging.error(f"Error in getting weather data: {weather_fetched_data['error']}")
        print(weather_fetched_data["error"])  # Print the error message
        messagebox.showerror("Error", f"Failed to fetch weather data: {weather_fetched_data['error']}")

    else:
        global values_for_data_extraction
        values_for_data_extraction = extract_weather_data(weather_fetched_data)

        # Update the UI with the new data
        try:
            # Update the StringVar values
            temp_var_cel.set(f"Temperature : {values_for_data_extraction['Temp Celsius']}°C")
            temp_var_fl.set(f"Feels Like : {values_for_data_extraction['Feels Like (°C)']}°C")
            humidity_var.set(f"Humidity : {values_for_data_extraction['Humidity (%)']}%")
            wind_speed_var.set(f"Wind Speed : {values_for_data_extraction['Wind Speed (kph)']} km/h")
            uv_index_var.set(f"UV Index : {values_for_data_extraction['UV Index']}")
            local_date_var.set(f"Date : {values_for_data_extraction['Local Time'][0:10]}")
            local_time_var.set(f"Time : {values_for_data_extraction['Local Time'][10:]}")
            condition_text.set(values_for_data_extraction['Condition'])
            description_label.config(text=values_for_data_extraction["Location Name"])

            # Update the weather icon
            image_url = "https:" + values_for_data_extraction["Condition Icon URL"]
            display_image(image_url)

        except KeyError:
            # Handle case if some data is missing
            logging.error("Error in updating the UI with new data")



#Taking Input from custom dialog box
def get_input():
    # Open an input dialog box to take user input for the city name
    user_input = custom_dialog()

    if user_input:
        logging.info(f"Fetching weather data for: {user_input}")
        print(f"Fetching weather data for: {user_input}")

        # Fetch data using the user-provided city name
        weather_fetched_data = getData(user_input)
        if "error" in weather_fetched_data:
            logging.error(f"Error in getting weather data: {weather_fetched_data['error']}")
            print(weather_fetched_data["error"])  # Print the error message
        else:
            global values_for_data_extraction
            values_for_data_extraction = extract_weather_data(weather_fetched_data)



#Setting Data to UI on Initialization
preWeatherData()



# Extracting Values for setting Images:
try :
    climate_image_url = "https:" +values_for_data_extraction["Condition Icon URL"]
except KeyError :
    climate_image_url = "../assets/error.png"



# Create tkinter window
window = tk.Tk()
window.title("Weather")
# Set the initial size of the window
window.geometry("400x600")
# Optionally, prevent resizing if you want a fixed size window
window.resizable(False, False)
display_image(climate_image_url)




#Variable Text Fields for Data
temp_var_cel = tk.StringVar()
temp_var_fl = tk.StringVar()
condition_text = tk.StringVar()
humidity_var = tk.StringVar()
wind_speed_var = tk.StringVar()
uv_index_var = tk.StringVar()
local_date_var = tk.StringVar()
local_time_var = tk.StringVar()


#Setting in Try-Except for Data in Fields
try :
    temp_var_cel.set("Temperature : " + str(values_for_data_extraction["Temp Celsius"])+"°C" )
    temp_var_fl.set("Feels Like : " + str(values_for_data_extraction["Feels Like (°C)"])+"°C")
    humidity_var.set("Humidity : " + str(values_for_data_extraction["Humidity (%)"])+"%")
    wind_speed_var.set("Wind Speed : " + str(values_for_data_extraction["Wind Speed (kph)"])+" km/h")
    uv_index_var.set("UV Index : " + str(values_for_data_extraction['UV Index']))
    local_date_var.set("Date : " + str(values_for_data_extraction["Local Time"][0:10]))
    local_time_var.set("Time : " + str(values_for_data_extraction["Local Time"][10:]))
    condition_text.set(values_for_data_extraction["Condition"])
    location_name = values_for_data_extraction["Location Name"]
except KeyError:
    location_name = "  No Internet Connection"


#Labels for Tkinter GUI



condition_label = tk.Label(window, textvariable=condition_text, font=("Arial", 14))
condition_label.pack(pady = 5)

# Add another label below the image
description_label = tk.Label(window, text=location_name, font=("Arial", 14))
description_label.pack()
temp_cel_label = tk.Label(window, textvariable=temp_var_cel, font=("Arial", 14))
temp_cel_label.pack()
temp_fl_label = tk.Label(window, textvariable=temp_var_fl, font=("Arial", 14))
temp_fl_label.pack()
humidity_label = tk.Label(window, textvariable=humidity_var, font=("Arial", 14))
humidity_label.pack()
wind_speed_label = tk.Label(window, textvariable=wind_speed_var, font=("Arial", 14))
wind_speed_label.pack()
uv_index_label = tk.Label(window, textvariable=uv_index_var, font=("Arial", 14))
uv_index_label.pack()
padder_label = tk.Label(window, text=" ", font=("Arial", 14))
padder_label.pack(pady = 5)
local_date_label = tk.Label(window, textvariable=local_date_var, font=("Arial", 10))
local_date_label.pack()
local_time_label = tk.Label(window, textvariable=local_time_var, font=("Arial", 10))
local_time_label.pack()
# Add a button at the bottom that prints "Button pressed" when clicked
test_button = tk.Button(window, text="Search Weather", command=get_input, font=("Arial", 12))
test_button.pack(pady=20)
# Start the tkinter main loop
window.mainloop()