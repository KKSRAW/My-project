# streamlit run proj.py      add this to run

import streamlit as st
import pandas as pd
import seaborn as sns
import numpy as np
import re
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import hashlib
import matplotlib.pyplot as plt
from email_validator import validate_email, EmailNotValidError
import base64
from fpdf import FPDF
import tempfile
import os
import io
import datetime
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'U8GOJNKCH3NC1MP7')

# Initialize database
def init_db():
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS industry_data (
            industry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            industry_name TEXT NOT NULL,
            sector TEXT NOT NULL,
            description TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_data (
            company_id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            industry_id INTEGER,
            financial_data TEXT,
            FOREIGN KEY (industry_id) REFERENCES industry_data (industry_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_reports (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            industry_id INTEGER,
            report_date DATE NOT NULL,
            report_data TEXT,
            FOREIGN KEY (industry_id) REFERENCES industry_data (industry_id)
        )
    """)
    conn.commit()
    conn.close()

# Hashing function for secure passwords
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

# Add new user to the database
def add_user(username, email, password):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                   (username, email, hash_password(password)))
    conn.commit()
    conn.close()
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed
# Authenticate user
def authenticate_user(username, password):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                   (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    return user

# Fetch industry-specific data
def fetch_industry_data():
    conn = sqlite3.connect("market_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM industry_data")
    data = cursor.fetchall()
    conn.close()
    return pd.DataFrame(data, columns=['Industry ID', 'Industry Name', 'Sector', 'Description'])

# Insert new market reports
def insert_market_report(industry_id, report_date, report_data):
    conn = sqlite3.connect("market_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO market_reports (industry_id, report_date, report_data) VALUES (?, ?, ?)", 
                   (industry_id, report_date, report_data))
    conn.commit()
    conn.close()

# Fetch user data
def fetch_user_data(username):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

# Update profile picture
def update_profile_pic(username, profile_pic):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET profile_pic = ? WHERE username = ?", 
                   (profile_pic, username))
    conn.commit()
    conn.close()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'user_data' not in st.session_state:
    st.session_state['user_data'] = {}

# Apply custom CSS for styling
def apply_custom_css():
    st.markdown(
        """
        <style>
        body {
            background-color: #1e1e2f;
            color: #ffffff;
        }
        .profile-pic {
            display: block;
            margin: 0 auto;
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
        }
        .stButton > button {
            background: linear-gradient(90deg, #27AE60, #1E90FF);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.3s;
        }
        .stButton > button:hover {
            background: linear-gradient(90deg, #1E90FF, #27AE60);
            transform: scale(1.05);
        }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th {
            background-color: #4CAF50;
            color: white;
            padding: 8px;
            text-align: center;
        }
        tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        tr:hover {
            background-color: #ddd;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
def validate_password(password):
    # Password must have at least one lowercase letter, one uppercase letter, one digit, one special character, and be at least 8 characters long
    password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
    
    if re.match(password_pattern, password):
        return True
    else:
        return False
# Registration function
def register():
    st.title("Register")
    
    username = st.text_input("Username", key="register_username")
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Password", type="password", key="register_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm_password")

    if st.button("Register", key="register_button"):
        if not username or not email or not password:
            st.warning("Please fill in all fields.")
        elif username in st.session_state.get('user_data', {}):
            st.warning("Username already exists!")
        elif password != confirm_password:
            st.warning("Passwords do not match!")
        elif not validate_password(password):  # Validate the password constraints
            st.warning("Password must be at least 8 characters long, contain an uppercase letter, a lowercase letter, a number, and a special character.")
        else:
            # Initialize the user_data in session state if it doesn't exist
            if 'user_data' not in st.session_state:
                st.session_state['user_data'] = {}

            # Store the user details with hashed password
            st.session_state['user_data'][username] = {
                "email": email,
                "password": hash_password(password),  # Store the hashed password
                "profile_pic": None,  # No profile pic initially
            }
            
            st.success("Registration successful! You can now log in.")
            
            

# Login function
def login():
    st.title("Login")
    
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="login_button"):
        # Ensure user_data is available in session state
        if 'user_data' in st.session_state and username in st.session_state['user_data']:
            user = st.session_state['user_data'][username]
            # Check if the password is correct by comparing with the stored hash
            if 'password' in user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success(f"Welcome {username}!")
            else:
                st.warning("Incorrect password!")
        else:
            st.warning("Username not found!")
# Logout function
def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.info("You have logged out.")

# Profile Section
def profile_section():
    username = st.session_state['username']
    user_data = st.session_state['user_data'][username]

    st.title("My Profile")
    
    # Allow the user to change their username
    new_username = st.text_input("Change Username", value=username)
    if new_username != username:
        if st.button("Update Username"):
            # Check if new username is already taken
            if new_username in st.session_state['user_data']:
                st.error("This username is already taken.")
            else:
                # Update username in session state
                st.session_state['username'] = new_username
                st.session_state['user_data'][new_username] = st.session_state['user_data'].pop(username)
                st.success(f"Username updated to {new_username}!")
                username = new_username  # Update the local username variable to reflect the new username
                user_data = st.session_state['user_data'][username]  # Fetch new user data

    # Display Profile Picture if available
    if user_data['profile_pic']:
        profile_pic_base64 = base64.b64encode(user_data['profile_pic']).decode('utf-8')
        profile_pic_html = f'<img class="profile-pic" src="data:image/png;base64,{profile_pic_base64}" alt="Profile Picture">'
        st.markdown(profile_pic_html, unsafe_allow_html=True)
    else:
        st.info("No profile picture uploaded yet.")

    # Allow the user to upload a new profile picture
    uploaded_file = st.file_uploader("Upload Profile Picture", type=["jpg", "jpeg", "png"], key="upload_profile_pic")
    if uploaded_file:
        user_data['profile_pic'] = uploaded_file.read()
        st.session_state['user_data'][username] = user_data
        st.success("Profile picture updated!")

    # Display User Details
    st.subheader("User Details")
    st.write(f"*Username:* {username}")
    st.write(f"*Email:* {user_data['email']}")

# Display Profile Picture at Top
def display_top_profile():
    username = st.session_state['username']
    user_data = st.session_state['user_data'][username]

    if user_data['profile_pic']:
        profile_pic_base64 = base64.b64encode(user_data['profile_pic']).decode('utf-8')
        profile_pic_html = f'<img class="profile-pic" src="data:image/png;base64,{profile_pic_base64}" alt="Profile Picture">'
    else:
        profile_pic_html = '<img class="profile-pic" src="https://via.placeholder.com/80" alt="Default Profile Picture">'

    st.markdown(profile_pic_html, unsafe_allow_html=True)
    

# Forecast Stock Prices
def forecast_prices(df):
    df['Days'] = (df['Date'] - df['Date'].min()).dt.days
    X = df[['Days']]
    y = df['Price']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    st.write(f"#### Model Mean Squared Error (MSE): {mse:.2f}")

    forecast_days = 30
    future_dates = pd.date_range(start=df['Date'].max() + datetime.timedelta(days=1), periods=forecast_days)
    future_days = (future_dates - df['Date'].min()).days
    future_prices = model.predict(future_days.values.reshape(-1, 1))

    forecast_df = pd.DataFrame({
        "Date": future_dates,
        "Predicted Price": future_prices
    })
    st.write("### 🔮 Forecasted Prices for the Next 30 Days")
    st.dataframe(forecast_df.style.format({"Predicted Price": "${:,.2f}"}))
    
    fig_forecast = px.line(
        forecast_df, x="Date", y="Predicted Price", title="Forecasted Price Trend",
        color_discrete_sequence=["#27AE60"], markers=True
    )
    st.plotly_chart(fig_forecast)
# for sending emails
def send_email_notification(to_email, symbol, message):
    sender_email = "22nn1a0526shailaja@gmail.com"  # Replace with your email
    sender_password = "k7032985975"  # Replace with your email password or app password

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = f"Stock Update: {symbol}"

    # Email body
    body = f"Hi, \n\n{message}\n\nBest regards,\nStock Price Tracker"
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Set up the SMTP server (using Gmail as an example)
        server = smtplib.SMTP('smtp.gmail.com', 587)  # For Gmail
        server.starttls()  # Secure the connection
        server.login(sender_email, sender_password)  # Log in with email and password
        text = msg.as_string()  # Convert the email message to string format
        server.sendmail(sender_email, to_email, text)  # Send the email
        server.quit()  # Close the server connection

        print(f"Email sent successfully to {to_email}.")
        return True  # Return True when email is successfully sent
    except Exception as e:
        # Handle any errors that occur during sending the email
        print(f"Error sending email: {e}")
        return False  # Return False if there was an error
# Simulate fetching stock prices
def fetch_stock_price(stock_symbol):
    # Replace with API call to fetch stock prices
    return np.random.randint(100, 500)  # Random price for demonstration

# Track stock prices and notify user
def track_stock_price(user_email, stock_symbol, current_price):
    # In a real application, use a database to store and compare prices over time
    previous_price = st.session_state.get(f"{stock_symbol}_price", current_price)

    # Check for price changes
    if current_price > previous_price:
        send_email(user_email, stock_symbol, "increased")
    elif current_price < previous_price:
        send_email(user_email, stock_symbol, "decreased")

    # Update the last recorded price
    st.session_state[f"{stock_symbol}_price"] = current_price

    # Simulate periodic updates
    time.sleep(60)  # Run every minute (adjust for production)
    
# Market Trends Analysis
def market_trends_analysis():
    st.title("Market Trends Analysis")
    date_range = st.date_input("Select Date Range", [])
    market_symbol = st.text_input("Enter Market Symbol", "SPX")
    user_email = st.text_input("Enter your email for stock updates", "")  # Email input field

    if st.button("Fetch Market Data"):
        if len(date_range) == 2:
            start_date, end_date = date_range
            dates = pd.date_range(start=start_date, end=end_date)

            # Simulated market data (Replace with actual data fetching logic)
            data = {
                "Date": dates,
                "Price": np.random.randint(1000, 5000, len(dates)),
                "Volume": np.random.randint(10000, 100000, len(dates))
            }
            df = pd.DataFrame(data)

            st.write(f"### Data for {market_symbol} ({start_date} to {end_date})")
            st.dataframe(df.style.highlight_max(subset="Price", axis=0))

            st.markdown("### 📈 Price and Volume Trends")
            fig_price = px.line(df, x="Date", y="Price", title="Price Trend Over Time")
            st.plotly_chart(fig_price)

            fig_vol = px.bar(df, x="Date", y="Volume", title="Volume Trend Over Time", color="Volume", color_continuous_scale="Viridis")
            st.plotly_chart(fig_vol)

            forecast_prices(df)

            # Trigger email notification if the price changes
            if len(df) > 1:
                latest_price = df['Price'].iloc[-1]
                previous_price = df['Price'].iloc[-2]

                # Only send email if the price changes
                if latest_price > previous_price and user_email:
                    send_email_notification(user_email, market_symbol, f"The price has increased to ${latest_price}.")
                elif latest_price < previous_price and user_email:
                    send_email_notification(user_email, market_symbol, f"The price has decreased to ${latest_price}.")
                else:
                    st.warning("No significant price change detected.")
        else:
            st.error("Please select a valid date range.")


# Function to upload and compare datasets           
import seaborn as sns
import matplotlib.pyplot as plt

def upload_and_compare_multiple_datasets():
    st.title("Dataset Comparison Tool")

    # Upload multiple datasets
    uploaded_files = st.file_uploader("Upload two or more datasets", type=["csv", "xlsx"], accept_multiple_files=True)

    if len(uploaded_files) >= 2:
        # Load the datasets into a list of DataFrames
        datasets = []
        for file in uploaded_files:
            if file.name.endswith('.csv'):
                datasets.append(pd.read_csv(file))
            elif file.name.endswith('.xlsx'):
                datasets.append(pd.read_excel(file))
        
        st.success(f"Successfully loaded {len(datasets)} datasets.")

        # Display the first two datasets for comparison
        df1, df2 = datasets[0], datasets[1]
        st.write("### Dataset 1 Preview")
        st.dataframe(df1.head())

        st.write("### Dataset 2 Preview")
        st.dataframe(df2.head())

        # Find common columns
        common_columns = set(df1.columns).intersection(set(df2.columns))
        st.write(f"### Common Columns: {common_columns}")

        if common_columns:
            # Separate numerical and categorical columns
            numerical_cols = [col for col in common_columns if pd.api.types.is_numeric_dtype(df1[col]) and pd.api.types.is_numeric_dtype(df2[col])]
            categorical_cols = [col for col in common_columns if pd.api.types.is_string_dtype(df1[col]) and pd.api.types.is_string_dtype(df2[col])]

            # Numerical Columns Visualizations
            if numerical_cols:
                st.write("### Numerical Column Comparisons")
                for col in numerical_cols:
                    st.write(f"#### Column: {col}")
                    
                    # Combine data for visualization
                    combined_df = pd.DataFrame({
                        "Dataset": ["Dataset 1"] * len(df1[col]) + ["Dataset 2"] * len(df2[col]),
                        col: pd.concat([df1[col], df2[col]]).values
                    })

                    # Generate boxplot
                    fig_box = px.box(combined_df, x="Dataset", y=col, title=f"Boxplot of {col}")
                    st.plotly_chart(fig_box, use_container_width=True)

                    # Generate line graph
                    fig_line = px.line(combined_df, x=combined_df.index, y=col, color="Dataset", title=f"Line Graph of {col}")
                    st.plotly_chart(fig_line, use_container_width=True)

            # Categorical Columns Visualizations
            if categorical_cols:
                st.write("### Categorical Column Comparisons")
                for col in categorical_cols:
                    st.write(f"#### Column: {col}")
                    
                    # Combine data for visualization
                    combined_df = pd.DataFrame({
                        "Value": pd.concat([df1[col], df2[col]]).values,
                        "Dataset": ["Dataset 1"] * len(df1[col]) + ["Dataset 2"] * len(df2[col])
                    })

                    # Generate histogram
                    fig_hist = px.histogram(combined_df, x="Value", color="Dataset", barmode="group", title=f"Histogram of {col}")
                    st.plotly_chart(fig_hist, use_container_width=True)

                    # Generate pie chart
                    pie_data = combined_df["Value"].value_counts().reset_index()
                    pie_data.columns = ["Category", "Count"]
                    fig_pie = px.pie(pie_data, names="Category", values="Count", title=f"Pie Chart of {col} (Combined)")
                    st.plotly_chart(fig_pie, use_container_width=True)

        else:
            st.warning("No common columns found for comparison.")

    else:
        st.info("Please upload at least two datasets for comparison.")


def generate_comparative_visualizations(df):
    # Visualize the entire dataset
    st.subheader("Data Visualizations")
    
    # Histogram for numerical columns
    numerical_cols = df.select_dtypes(include=['float64', 'int64']).columns
    for col in numerical_cols:
        fig = px.histogram(df, x=col, title=f"Distribution of {col}")
        # Adding a unique key using the column name
        st.plotly_chart(fig, key=f"histogram_{col}")
    
    # Box plot for numerical columns to spot outliers
    fig = px.box(df, y=numerical_cols.tolist(), title="Boxplot for Numerical Columns")
    # Adding a unique key for the box plot
    st.plotly_chart(fig, key="boxplot_numerical")
    
    # Scatter plot matrix for correlations
    fig = px.scatter_matrix(df, dimensions=numerical_cols.tolist(), title="Scatter Matrix")
    # Adding a unique key for the scatter matrix
    st.plotly_chart(fig, key="scatter_matrix")


def perform_predictive_analysis(df, column):
    # Ensure sample size does not exceed the number of columns available
     

    # Separate numerical, datetime, and categorical columns
    numerical_cols = df.select_dtypes(include=['float64', 'int64']).columns
    datetime_cols = df.select_dtypes(include=['datetime64']).columns
    categorical_cols = df.select_dtypes(include=['object']).columns  # Categorical columns

    # Fill NaN values for numerical columns with the mean
    X = df[numerical_cols].fillna(df[numerical_cols].mean())

    # For datetime columns, fill them with the most frequent value
    for dt_col in datetime_cols:
        most_frequent_datetime = df[dt_col].mode()[0]  # Most frequent datetime value
        df[dt_col] = df[dt_col].fillna(most_frequent_datetime)

    # Handle categorical columns by encoding them
    X = pd.get_dummies(df[numerical_cols.tolist() + categorical_cols.tolist()], drop_first=True)

    # Define the target variable (assumes column exists in the dataframe)
    y = df[column]

    # Splitting the data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize the model and train it
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Make predictions
    y_pred = model.predict(X_test)

    # Calculate the Mean Squared Error
    mse = mean_squared_error(y_test, y_pred)
    st.write(f"Mean Squared Error (MSE): {mse}")

    # Visualizing Predicted vs Actual values using Scatter Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(y_test, y_pred)
    ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'k--', lw=2)
    ax.set_xlabel('Actual Values')
    ax.set_ylabel('Predicted Values')
    ax.set_title('Predicted vs Actual Values')
    st.pyplot(fig)

    # Visualize distribution of the target variable using a Histogram
    st.subheader(f"Distribution of {column}")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(y, bins=30, color='skyblue', edgecolor='black')
    ax.set_title(f'Distribution of {column}')
    ax.set_xlabel(column)
    ax.set_ylabel('Frequency')
    st.pyplot(fig)

    # Visualize feature importance using a bar chart (coefficients of linear regression)
    st.subheader("Feature Importance (Model Coefficients)")
    feature_importance = pd.DataFrame({
        'Feature': X.columns,
        'Coefficient': model.coef_
    }).sort_values(by='Coefficient', ascending=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x='Coefficient', y='Feature', data=feature_importance, ax=ax, palette='viridis')
    ax.set_title('Feature Importance')
    st.pyplot(fig)

    # Visualizing correlations using a heatmap
    st.subheader("Correlation Heatmap")
    fig, ax = plt.subplots(figsize=(10, 6))
    corr_matrix = df[numerical_cols].corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax)
    ax.set_title('Correlation Matrix')
    st.pyplot(fig)

    # Pie chart visualization for categorical data (if any)
    if categorical_cols.size > 0:
        st.subheader("Pie Chart of Categorical Column Values")
        pie_data = df[categorical_cols[0]].value_counts()
        fig = px.pie(pie_data, names=pie_data.index, values=pie_data.values, title=f"Distribution of {categorical_cols[0]}")
        st.plotly_chart(fig)

    # Line plot visualization (e.g., Time Series if there's a datetime column)
    if datetime_cols.size > 0:
        st.subheader("Time Series Line Plot")
        df_sorted = df.sort_values(by=datetime_cols[0])
        df_sorted[datetime_cols[0]] = pd.to_datetime(df_sorted[datetime_cols[0]])
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(df_sorted[datetime_cols[0]], df_sorted[column], label=column)
        ax.set_title(f'Time Series of {column}')
        ax.set_xlabel('Time')
        ax.set_ylabel(column)
        ax.legend()
        st.pyplot(fig)

    # Additional visualizations like boxplots, and pairplots can be added similarly:
    # Boxplot for a feature
    st.subheader(f"Boxplot for {column}")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(x=df[column], ax=ax)
    ax.set_title(f'Boxplot of {column}')
    st.pyplot(fig)

    # Pairplot of some selected features (if applicable)
    st.subheader("Pairplot of Selected Features")
    selected_features = df[numerical_cols.tolist() + categorical_cols.tolist()].sample(10, axis=1)
    fig = sns.pairplot(selected_features)
    st.pyplot(fig)



# Function to perform sector-wise comparison and analysis
def sector_comparison_analysis():
    st.title("Sector-wise Comparison and Analysis")
    uploaded_file = st.file_uploader("Upload CSV for Sector Analysis", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write(f"### Data from {uploaded_file.name}")
        st.dataframe(df.head())

        # Assuming data has a 'Sector' column and 'Price'
        sectors = df['Sector'].unique()
        sector = st.selectbox("Select Sector for Analysis", sectors)

        sector_data = df[df['Sector'] == sector]

        # Visualize data for the selected sector
        st.write(f"### {sector} Sector Data")
        fig = px.line(sector_data, x="Date", y="Price", title=f"Price Trend for {sector} Sector")
        st.plotly_chart(fig)

        # Perform predictive modeling on sector data
        forecast_prices(sector_data)


# Function to upload and display both CSV and Excel files

def upload_and_display_file():
    # Allow user to upload an Excel or CSV file
    uploaded_file = st.file_uploader("Upload an Excel or CSV file", type=["xlsx", "csv"])
    
    if uploaded_file is not None:
        # Load the file based on the extension
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.write("Data Preview:")
        st.dataframe(df.head())  # Show a preview of the data
        
        # Allow user to select a column for detailed analysis
        column = st.selectbox("Select a column to analyze", df.columns)
        
        # Generate visualizations for the selected column and entire dataset
        generate_visualizations(df, column)






def generate_visualizations(df, column):
    # Visualizing the entire data (for numerical columns, histograms)
    st.subheader("Visualization for Entire Data")
    st.write("### Distribution of Data")
    
    # Plot a bar chart for categorical data
    if df[column].dtype == 'object':
        # Reset index and rename columns for clarity
        value_counts = df[column].value_counts().reset_index()
        value_counts.columns = ['Category', 'Count']  # Rename columns
        
        # Plot Bar chart
        fig_bar = px.bar(value_counts, x='Category', y='Count',
                         labels={'Category': 'Categories', 'Count': 'Count'},
                         title=f"Bar Chart of {column}")
        st.plotly_chart(fig_bar)
        
        # Plot Pie chart
        fig_pie = px.pie(value_counts, names='Category', values='Count',
                         labels={'Category': 'Categories', 'Count': 'Count'},
                         title=f"Pie Chart of {column}")
        st.plotly_chart(fig_pie)
    
    # Plot a histogram for numerical columns
    elif df[column].dtype in ['int64', 'float64']:
        fig_hist = px.histogram(df, x=column, title=f"Histogram of {column}")
        st.plotly_chart(fig_hist)
    
    # Filter numerical columns for correlation
    numeric_df = df.select_dtypes(include=['int64', 'float64'])
    
    if numeric_df.shape[1] > 1:  # Ensure there are at least two numerical columns
        fig_corr = px.imshow(numeric_df.corr(), text_auto=True, title="Correlation Heatmap")
        st.plotly_chart(fig_corr)


def create_dashboard(df):
    # Create a section to display dashboard-like components
    st.title("Interactive Data Dashboard")

    # Display summary
    st.subheader("Data Summary")
    st.write(df.describe())

    # Select columns for trend analysis
    column = st.selectbox("Select a Column for Trend Analysis", df.columns)
    
    # Show trend analysis for the selected column
    if column:
        generate_visualizations(df, column)

    # Additional Visualizations - Pie chart for categorical data
    categorical_columns = df.select_dtypes(include='object').columns
    for cat_col in categorical_columns:
        st.subheader(f"{cat_col} Distribution")
        fig_pie = px.pie(df[cat_col].value_counts().reset_index(), names='index', values=cat_col,
                         title=f'{cat_col} Pie Chart')
        st.plotly_chart(fig_pie)

    # Correlation Matrix Heatmap (useful for numeric data)
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
    if len(numeric_columns) > 1:
        st.subheader("Correlation Matrix")
        corr_matrix = df[numeric_columns].corr()
        fig_corr = px.imshow(corr_matrix, text_auto=True, color_continuous_scale='Viridis', title="Correlation Heatmap")
        st.plotly_chart(fig_corr)  

#custom reports by user
def load_data(uploaded_file):
    """Load dataset from the uploaded file."""
    if uploaded_file.name.endswith("xlsx"):
        try:
            df = pd.read_excel(uploaded_file)
        except ImportError:
            st.error("Missing the 'openpyxl' module. Please install it with pip.")
            return None
    else:
        df = pd.read_csv(uploaded_file)

    # Check if the dataset is empty
    if df.empty:
        st.error("The uploaded dataset is empty. Please upload a valid file.")
        return None

    st.write("### Data Preview")
    st.write(df.head())  # Show the first few rows to debug the uploaded data
    return df


def customize_report(df):
    """Allow users to customize the dataset for reporting."""
    st.write("### Customize Your Report")
    st.write("Use the options below to filter, sort, and select specific columns for your report.")

    # Column selection
    selected_columns = st.multiselect(
        "Select columns to include in the report", 
        df.columns, 
        default=df.columns
    )

    # Sorting
    sort_column = st.selectbox("Select a column to sort by", df.columns)
    sort_ascending = st.radio("Sort order", ["Ascending", "Descending"]) == "Ascending"

    # Ensure consistent data type for the sort column
    if pd.api.types.is_numeric_dtype(df[sort_column]):
        pass  # Numeric column, no conversion needed
    elif pd.api.types.is_datetime64_any_dtype(df[sort_column]):
        df[sort_column] = pd.to_datetime(df[sort_column], errors='coerce')  # Convert to datetime
    else:
        df[sort_column] = df[sort_column].astype(str)  # Convert to string for sorting

    # Filtering
    filter_column = st.selectbox("Select a column to filter by", df.columns)
    unique_values = df[filter_column].unique()
    selected_values = st.multiselect(
        f"Filter `{filter_column}` by value", 
        unique_values, 
        default=unique_values
    )

    # Apply customization
    customized_df = df[selected_columns]
    customized_df = customized_df[customized_df[filter_column].isin(selected_values)]
    customized_df = customized_df.sort_values(by=sort_column, ascending=sort_ascending)

    st.write("### Customized Report Preview")
    st.write(customized_df)

    return customized_df


def download_button(customized_df):
    """Provides a download button for the customized report."""
    if customized_df is not None:
        # Convert the DataFrame to CSV for downloading
        buffer = io.StringIO()
        customized_df.to_csv(buffer, index=False)
        buffer.seek(0)
        csv_data = buffer.getvalue()

        st.download_button(
            label="Download Customized Report",
            data=csv_data,
            file_name="custom_report.csv",
            mime="text/csv",
        )
def create_custom_reports():
    """Allows the user to upload a dataset, customize a report, and download it."""
    st.title("Create Custom Reports")

    st.write("Upload a dataset and create a customized report, similar to Power BI.")
    uploaded_file = st.file_uploader("Upload your dataset (CSV or Excel)", type=["csv", "xlsx"])

    if uploaded_file is not None:
        df = load_data(uploaded_file)

        if df is not None:
            # Allow customization of the report
            customized_df = customize_report(df)

            # Provide a download button for the customized report
            download_button(customized_df)
# for allowing users to create a dashboard 
def upload_dataset_section():
    """Allow users to upload a dataset and create a dashboard."""
    st.title("Create Your Custom Dashboard")

    # Dataset upload
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file is not None:
        # Load the dataset
        df = pd.read_csv(uploaded_file)
        st.write("Dataset Preview:")
        st.write(df)

        st.sidebar.title("Dashboard Configuration")
        graph_type = st.sidebar.selectbox(
            "Select Visualization Type", ["Bar Chart", "Line Chart", "Scatter Plot", "Pie Chart"]
        )
        x_axis = st.sidebar.selectbox("Select X-Axis", df.columns)
        y_axis = st.sidebar.selectbox("Select Y-Axis", df.columns)

        # Placeholder for the dashboard
        dashboard_placeholder = st.container()

        if st.sidebar.button("Generate Visualization"):
            with dashboard_placeholder:
                st.subheader("Your Visualization")
                if graph_type == "Bar Chart":
                    fig, ax = plt.subplots()
                    ax.bar(df[x_axis], df[y_axis], color="skyblue")
                    ax.set_title(f"{graph_type} of {y_axis} vs {x_axis}")
                    ax.set_xlabel(x_axis)
                    ax.set_ylabel(y_axis)
                    st.pyplot(fig)

                elif graph_type == "Line Chart":
                    fig, ax = plt.subplots()
                    ax.plot(df[x_axis], df[y_axis], marker="o", color="green")
                    ax.set_title(f"{graph_type} of {y_axis} vs {x_axis}")
                    ax.set_xlabel(x_axis)
                    ax.set_ylabel(y_axis)
                    st.pyplot(fig)

                elif graph_type == "Scatter Plot":
                    fig, ax = plt.subplots()
                    ax.scatter(df[x_axis], df[y_axis], color="red")
                    ax.set_title(f"{graph_type} of {y_axis} vs {x_axis}")
                    ax.set_xlabel(x_axis)
                    ax.set_ylabel(y_axis)
                    st.pyplot(fig)

                elif graph_type == "Pie Chart":
                    fig, ax = plt.subplots()
                    ax.pie(
                        df[y_axis].value_counts(),
                        labels=df[y_axis].value_counts().index,
                        autopct="%1.1f%%",
                        startangle=90,
                        colors=plt.cm.Paired.colors,
                    )
                    ax.set_title(f"{graph_type} of {y_axis}")
                    st.pyplot(fig)

        # Save Dashboard Button
        if st.button("Save Dashboard as PDF"):
            save_dashboard_as_pdf(df, graph_type, x_axis, y_axis)

def save_dashboard_as_pdf(df, graph_type, x_axis, y_axis):
    """Save the created dashboard as a PDF."""
    # Create a new PDF object
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add title to PDF
    pdf.cell(200, 10, txt="Custom Dashboard", ln=True, align="C")

    # Add Dataset Summary
    pdf.cell(200, 10, txt="Dataset Summary:", ln=True)
    summary = df.describe().to_string()
    pdf.multi_cell(0, 10, summary)

    # Create the plot based on the selected chart type
    fig, ax = plt.subplots()
    if graph_type == "Bar Chart":
        ax.bar(df[x_axis], df[y_axis], color="skyblue")
    elif graph_type == "Line Chart":
        ax.plot(df[x_axis], df[y_axis], marker="o", color="green")
    elif graph_type == "Scatter Plot":
        ax.scatter(df[x_axis], df[y_axis], color="red")
    elif graph_type == "Pie Chart":
        ax.pie(
            df[y_axis].value_counts(),
            labels=df[y_axis].value_counts().index,
            autopct="%1.1f%%",
            startangle=90,
            colors=plt.cm.Paired.colors,
        )
    ax.set_title(f"{graph_type} of {y_axis} vs {x_axis}")
    ax.set_xlabel(x_axis)
    ax.set_ylabel(y_axis)

    # Save plot to a temporary image file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_file_path = temp_file.name
        fig.savefig(temp_file_path, format="png", bbox_inches="tight")
        plt.close(fig)

    # Add the image to the PDF
    pdf.image(temp_file_path, x=10, y=60, w=180)

    # Clean up the temporary image file
    os.remove(temp_file_path)

    # Save PDF to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf_file:
        temp_pdf_path = temp_pdf_file.name
        pdf.output(temp_pdf_path)

    # Read the generated PDF into a BytesIO object
    with open(temp_pdf_path, "rb") as pdf_file:
        pdf_output = io.BytesIO(pdf_file.read())

    # Clean up the temporary PDF file
    os.remove(temp_pdf_path)

    # Provide a download button for the PDF
    st.download_button(
        label="Download Dashboard PDF",
        data=pdf_output,
        file_name="custom_dashboard.pdf",
        mime="application/pdf",
    )
# Main Function
def main():
    apply_custom_css()
    
    # Check if user is logged in or show the login/register options
    if not st.session_state.get('logged_in', False):
        if 'show_login' in st.session_state and st.session_state['show_login']:
            # If the flag is set, show the login page
            st.session_state['show_login'] = False  # Reset the flag
            login()  # Automatically open the login section
        else:
            st.sidebar.title("Please Login or Register")
            
            # Sidebar radio for login or register
            option = st.sidebar.radio("Choose an Option", ("Login", "Register"))
            
            if option == "Register":
                register()  # Call register function
            elif option == "Login":
                login()  # Call login function
    else:
        # Show profile if logged in
        display_top_profile()
        st.sidebar.title(f"Welcome {st.session_state['username']}")
        
        # Sidebar menu options after login
        menu_option = st.sidebar.radio(
            "Menu", 
            ["Upload and Compare Datasets", "Sector Analysis", "Market Trends", "Create Custom Reports", "Create a dashboard", "My Profile"]
        )
        
        # Handle each menu option
        if menu_option == "Upload and Compare Datasets":
            upload_and_compare_multiple_datasets()
        elif menu_option == "Sector Analysis":
            upload_and_display_file()
        elif menu_option == "Market Trends":
            market_trends_analysis()  
        elif menu_option == "Create Custom Reports":
            create_custom_reports() 
        elif menu_option == "Create a dashboard":
            upload_dataset_section()
        elif menu_option == "My Profile":
            profile_section()

        
       
if __name__ == "__main__":
    init_db()
    main()
