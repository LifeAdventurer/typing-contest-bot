# Typing Contest Discord Bot

This is a Discord bot built with `discord.py` to facilitate typing contests in a server. The bot enables users to start contests, join them, submit WPM (words per minute) results, and display rankings based on average WPM.


## Prerequisties

- Python 3.11+
- Poetry (recommended) or pip

## Installation


### 1. Clone the repository:

```sh
git clone https://github.com/your-username/typing-contest-bot.git
cd typing-contest-bot
```

### 2. Install dependencies:

#### Using Poetry (recommended)

If you don't have Poetry installed, you can install it using the following command:

```sh
curl -sSL https://install.python-poetry.org | python3 -
```

Then, to install all dependencies, run:

```sh
poetry install
```

Activate the virtual environment:

```sh
poetry shell
```

#### Using pip

Create and activate a virtual environment:

```sh
python -m venv venv
source venv/bin/activate # On Windows use `venv\Scripts\activate`
```

Then, to install all dependencies, run:

```sh
pip install -r requirements.txt
```

### 3. Configure the bot:

Create a `config.json` file under `./config/`:

```json
{
    "token": "your-discord-bot-token",
    "typist_role_name": "your-server-typist-role"
}
```

### 4. Run the bot:

To start the bot, run:

```sh
python main.py # Or `poetry run python main.py` if using Poetry
```

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the [`LICENSE`](./LICENSE) file for details.
