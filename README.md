# Firebase Cloud Function for Booking Reservations

## Project Overview

This project is centered around a cloud function hosted on Firebase, designed to store and process reservations from our hotel booking motor. The booking motor sends booking email notifications to an analytics email, and the function processes it every 30 minutes. The default booking motor database does not store phone numbers, which is what this function solves. Additionally this function reports the reservations to a Facebook Pixel as marketing data, using the Conversions API. 

### Key Features

- **Reservation Storage:** Automatically stores all incoming reservations from the booking motor into a Firestore NoSQL database.
- **Facebook Pixel Integration:** Utilizes the Facebook Conversions API to report reservations to the Facebook Pixel.
- **Data Accuracy and Value:** Improves the Facebook Pixel's accuracy by providing detailed reservation values.
- **OTA and Offline Reservation Tracking:** Captures and reports reservations made through Online Travel Agencies (OTAs) and offline methods.

### Benefits

- **Real-Time Data Syncing:** Ensures scheduled data flow between the booking system, Firestore, and Facebook Pixel.
- **Offline and OTA Inclusion:** Integrates traditionally harder-to-track reservation sources into the digital analytics fold.

## Getting Started

These instructions will guide you through the setup and deployment of the cloud function in your Firebase environment.

### Prerequisites

- Firebase account and project setup.
- Facebook Pixel setup for your marketing needs.

### Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Cortega13/reservation-reporter.git
   ```

2. **Navigate to the Function Directory:**
    ```bash
    cd reservation-reporter/functions
    ```
3. **Install Dependencies:**
    **On Windows:**
    ```bash
    venv/Scripts/activate
    pip install requirements.txt
    deactivate
    ```
    **On Linux:**
    ```bash
    source venv/Scripts/activate
    pip install requirements.txt
    deactivate
    ```

4. **Deploy the Function to Firebase:**
    ```bash
    firebase deploy --only functions
    ```
### Configuration

- In google secrets manager, configure a secret with json information on environmental variables. This ensures cheap retrieval of secret environmental variables. The format will be as follows.
    ```bash
    {"ACCESS_TOKEN":"", 
    "PIXEL_ID":,
    "IMAP_HOST":"",
    "IMAP_USER":"",
    "IMAP_PASS":"",
    "IMAP_PORT":}
    ```
- Ensure Firestore rules are set to allow necessary read/write operations.

## Usage

Once deployed, the function will automatically trigger on new reservations. No further action is needed unless there are updates or changes in the booking motor or Facebook Pixel configurations.