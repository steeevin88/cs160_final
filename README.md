# Denial-of-Service Attacks and Prevention Methods

Final Project for SJSU's CS 160: Information Security

## Instructions

### Frontend Setup

1. Navigate to the `dos-simulator` directory:
   ```bash
   cd dos-simulator
   ```
2. Install the dependencies:
   ```bash
   npm install --legacy-peer-deps
   ```

### Backend Setup

1. Create a virtual environment in the `server` directory:
   ```bash
   cd server
   python3 -m venv venv
   ```
2. Activate the virtual environment:
   - On macOS and Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     .\venv\Scripts\activate
     ```
3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

   - Note: `slowapi` sometimes requires an explicit install. If needed, run the following command again to ensure it works.

   ```
   pip install slowapi
   ```

4. Run the FastAPI server:
   ```bash
   python3 app.py
   ```

## Team Members - Group 13

- Brandon Nguyen, Daphne Dao, Gurshan Warya, Jonathan Nguyen, Nicholas Le, Steven Le
