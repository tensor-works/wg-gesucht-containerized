# WG-Gesucht Bot 
*Let's face it, looking for a new WG is a pain, so why not just automate the process?*


## Note on GPT use:

Option to use OpenAI GPT model to create more personalised messages!

So far only language classification and keyword detection are supported.

You can easily add more functionality. Simply process the listing text (`config['listing_text']`) with GPT by writing a function which uses the `OpenAIHelper` class. Look at the `gpt_get_language` function inside the `src/submit_wg.py` file to get an idea.

## Getting Started

### 1 Create virtual environment and install Python packages

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
playwright install
```

### 2 Ensure `chromedriver` is installed

Running `which chromedriver` should return a path like `/usr/bin/chromedriver`.

If not simply check this website: https://chromedriver.chromium.org/downloads

Note: Ensure that your Chrome version matches the chromedriver version.

### 3 Setup config file

Rename `config_template.yaml` to `config.yaml`, enter your email and password for wg-gesucht.de and your token for OpenAI (optional).

```yaml
messages:
  german: "message_de.txt" # add this file
  english: "message_en.txt" # add this file
wg_gesucht_credentials:
  email: "my-email@email.com" # change
  password: "password1234" # change
chromedriver_path: "/usr/bin/chromedriver" # change!
url: "" # change!
openai_credentials:
  api_key: ""
run_headless: false
min_listing_length_months: 6
rental_start:
  year: 2024
  month: 3
  day: 1
  buffer_days: 14

```

If you wish to send messages in e.g. english ONLY, simply delete `german: "message_de.txt` from the `messages` list in `config.yaml` file.

If no OpenAI token is provided, the bot will simply pick the first element from the `messages` list.

You also need to enter the `url`. Just go to `wg-gesucht.de`, enter all your filter requirements, apply filter and simply copy the url you get.

### 4 Write message into `message_de.txt` and `message_en.txt`

Make sure you use the format of `Hello receipient`. Since the code automatically replaces `receipient` with the name of the user.

### 5 Finally, simply run:

```
bash run.sh
```

To change configs edit the `config.yaml` file.


## Acknowledgements

Thanks to the code by [nickirk](https://github.com/nickirk/immo), which served as a starting point for this project.

Note: Most of the code has been completely rewritten for simplicity and speed improvements.