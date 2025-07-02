# bypass2fa
Used to bypass an institution's microsoft SSO and 2FA requirments by automatically inputting the user's credentials in a custom browser session.

## Setup
### Python Packages
Install required packages with:
```shell
pip install -r ./requirements.txt
```

If playwright is being installed for the first time, you may also need to run:
```shell
playwright install
```

### Generate a secret key
1. Goto your [micrsoft account settings](https://myaccount.microsoft.com/?ref=amc).\
-> [Security Info](https://mysignins.microsoft.com/security-info) / UPDATE INFO \
-> Add sign-in method \
-> Microsoft Authenticator \
-> I want to use a different authenticator app \
-> Next \
-> Can't scan image? \
-> Secret Key

2. Copy this secret key as it'll be used later

    -> Next

3. Continue with the rest of setup and return here after

4. Run `python3 main.py` in your terminal

5. Ignore the opened browser window (Don't close it for now)

6. Copy the "Current" value ouput in the terminal and put it into the still open settings window where it says "Enter Code".

    Note the code might change as your typing it in (there is a countdown in the teminal), if the code doesn't work, retry from step 4.

    -> Next

7. Close the browser / stop the program.

### Environment File
1. Make a copy of the `.env.example` file naming it `.env`.  \
(Commonly used terminal command `cp .env.example .env`)
2. Edit the new `.env` file
    - Set 'LOGIN_USER' to be your email / username used to login 
    - Set 'LOGIN_PASS' to be your password used to login
    - Set '2FA_SECRET' to be the secret key generated in the previous section.


## Run
Execute in the terminal
```shell
python main.py
```

### Example Terminal Output
In the terminal there will be a persistant output showing the time before the OTP code expires, the current OTP code and the next OTP code.
```
  11| Current: 261625 -> Next: 115230
```
- `11` is how many seconds before the current code expires
- `261625` is the current code to use as a OTP
- `115230` is the next code which will be active after the current one expires
