# Instagram Automation Bot README

## Overview
This project is a Python-based automation tool that uploads videos to Instagram as posts and stories using the `instagrapi` library. It reads a schedule from `media_schedule.csv` to determine which media file to upload each day and uses a caption from `caption.txt`.

## Features
- **Automated daily posting and story updates** based on a predefined schedule.
- Uses secure environment variables for authentication.
- Reads captions from an external text file (`caption.txt`).

## Prerequisites
- Python 3.7 or higher
- An Instagram account
- The following Python packages:
  - `pandas`
  - `instagrapi`
  - `datetime`

## Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/instagram-automation-bot.git
   cd instagram-automation-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   - Add your Instagram username and password as environment variables:
     ```bash
     export INSTAGRAM_USERNAME='your_username'
     export INSTAGRAM_PASSWORD='your_password'
     ```

## Usage
1. **Prepare your schedule**:
   Ensure `media_schedule.csv` exists and has columns `Date` and `File Path` with the correct media file paths.

2. **Prepare the caption**:
   Create or update `caption.txt` in the root folder with your desired caption.

3. **Run the script**:
   ```bash
   python script.py
   ```

## File Structure
```
root/
|-- script.py
|-- caption.txt
|-- media_schedule.csv
|-- requirements.txt
```

## Troubleshooting
- Ensure `caption.txt` contains the caption text with no unexpected characters.
- Check logs for successful login and media upload status.
- Verify `media_schedule.csv` has a valid path for today's date.

## License
This project is licensed under the MIT License.

---

### Note:
Use this tool responsibly, keeping in mind Instagram's terms of service and automation policies.

