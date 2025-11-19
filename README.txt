Markdown

# ⏳ ChronoWeaver

**A Relational World-Building & Timeline Management Tool**

ChronoWeaver is a Python-based application designed for writers, gamemasters, and world-builders. Unlike standard wikis or flat text files, ChronoWeaver uses a relational database to link Characters, Events, and Locations dynamically.

> "Weave the threads of history into a tapestry of fate."

## ✨ Features

* **Interactive Visual Timeline:** Zoomable, scrollable timeline charts powered by Plotly.
* **Relational Lore:**
    * **Event Participation:** Automatically link characters to events (e.g., "General Kaelen" was at "The Battle of Twin Moons").
    * **Character Connections:** Define recursive relationships (e.g., Rivals, Family, Mentors).
* **The Dungeon Master Console:** Full CRUD (Create, Read, Update, Delete) capabilities for all data entries.
* **Multi-Timeline Support:** Manage multiple different worlds or stories within a single application.
* **Immersive UI:** A custom Dark/Neon aesthetic built on Streamlit.

## 🛠️ Tech Stack

* **Frontend:** [Streamlit](https://streamlit.io/) (Python)
* **Backend:** Python 3.x
* **Database:** MySQL
* **Visualization:** Plotly Express
* **Data Handling:** Pandas, MySQL-Connector

---

## 🚀 Installation & Setup

### Prerequisites
1.  **Python 3.8+** installed on your machine.
2.  **MySQL Server** installed and running.

### Step 1: Clone or Download
Download the project files to a folder named `chronoweaver`.

### Step 2: Database Setup
1.  Open your MySQL management tool (Workbench, CLI, phpMyAdmin).
2.  Run the following SQL script to create the database and necessary tables:

```sql
CREATE DATABASE IF NOT EXISTS chronoweaver;
USE chronoweaver;

CREATE TABLE IF NOT EXISTS timelines (
    id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), description TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY, timeline_id INT, title VARCHAR(255), 
    event_year INT, description TEXT, 
    FOREIGN KEY (timeline_id) REFERENCES timelines(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS characters (
    id INT AUTO_INCREMENT PRIMARY KEY, timeline_id INT, name VARCHAR(255), 
    role VARCHAR(255), bio TEXT, 
    FOREIGN KEY (timeline_id) REFERENCES timelines(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS locations (
    id INT AUTO_INCREMENT PRIMARY KEY, timeline_id INT, name VARCHAR(255), 
    description TEXT, 
    FOREIGN KEY (timeline_id) REFERENCES timelines(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_characters (
    event_id INT, character_id INT, role_note VARCHAR(255),
    PRIMARY KEY (event_id, character_id),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_relationships (
    char1_id INT, char2_id INT, relationship_type VARCHAR(100),
    PRIMARY KEY (char1_id, char2_id),
    FOREIGN KEY (char1_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (char2_id) REFERENCES characters(id) ON DELETE CASCADE
);
Step 3: Install Dependencies
Open your terminal/command prompt in the project folder and run:

Bash

pip install streamlit mysql-connector-python plotly pandas
Step 4: Configure Database Connection
Open app.py in a text editor. Find the get_db_connection function (around line 12) and update the user and password to match your local MySQL credentials:

Python

return mysql.connector.connect(
    host='localhost',
    user='root',          # <--- Update this
    password='your_password', # <--- Update this
    database='chronoweaver'
)
🎮 Usage
To launch the application, run the following command in your terminal:

Bash

streamlit run app.py
The application will open automatically in your default web browser at http://localhost:8501.

Navigation Guide
Home: Select an existing timeline or Create a new one.

Dashboard: Once inside a timeline, you have three tabs:

📜 The Saga: View the visual timeline and read lore cards.

🛠️ Dungeon Master: Create, Edit, or Delete Events, Characters, and Locations.

🕸️ Connections: Link Characters to Events or define Relationships between Characters.

📂 Project Structure
chronoweaver/
├── app.py              # The main application logic (Frontend & Backend)
├── requirements.txt    # Python dependencies
└── README.md           # Documentation