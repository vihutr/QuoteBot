import datetime
import discord
import logging
import os
import random
import sqlite3

chance_limit = 500
help_msg = """```
Commands\n
Use any command without any input to see more info
+q: add a quote, automatically timestamped
+m: add a quote, manually timestamped
+r: get a random quote from the database
+a: get all quotes (doesn't actually work lmao)
+help or +h: this thing

if you add a dumb quote I kill you instantly
```"""

handler = logging.FileHandler(filename='discord.log',
                              encoding='utf-8', mode='w')
database_folder = 'database'
database = os.path.join(database_folder, 'database.db')
qc_path = os.path.join(database_folder, 'qc.txt')
print(qc_path)


def check_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def save_to_dir(path, data):
    with open(path, "w", encoding="utf-8") as file:
        file.write(data)


def retrieveToken():
    check_dir("secret")
    with open("secret/token", "r") as file:
        token = file.read()
        token = token.splitlines()[0]
        file.close()
        return token


check_dir(database_folder)
qc = 0
with open(qc_path, "r") as f:
    print("reading qc")
    data = int(f.read().splitlines()[0])
    if not data:
        print("no data")
    else:
        qc = data
        print('qc: ' + str(qc))


class MyClient(discord.Client):
    def start_db(self):
        self.conn = sqlite3.connect(database)
        self.cur = self.conn.cursor()
        self.cur.execute('''CREATE TABLE if not exists Quote
                         (quote TEXT, quotee TEXT, datetime TEXT)''')
        self.conn.commit()
        print(f"Connected to {database}")
        self.quote_chance = qc
        self.quote = ''
        self.quotee = ''
        self.date_time = ''
        self.session_state = 0
        self.session_user = ''
        self.all_quotes = self.get_all_quotes()

    def add_quote(self):
        print("adding quote")
        insert_query = '''INSERT INTO Quote
            (quote, quotee, datetime)
            VALUES (?, ?, ?);'''
        data_tuple = (self.quote, self.quotee, self.date_time)
        self.cur.execute(insert_query, data_tuple)
        self.conn.commit()
        print("finished add_quote func")

    def random_quote(self):
        query = '''SELECT * FROM Quote ORDER BY RANDOM() LIMIT 1;'''
        self.cur.execute(query)
        print("quote obtained!")
        data = self.cur.fetchall()[0]
        self.quote = data[0]
        self.quotee = data[1]
        self.date_time = data[2]
        print(self.format_quote())

    def get_all_quotes(self):
        query = '''SELECT * FROM Quote;'''
        self.cur.execute(query)
        print("quotes obtained!")
        data = self.cur.fetchall()
        return data

    def format_quote(self):
        return f'{self.quote} - {self.quotee}, {self.date_time}'

    async def send_quote(self, channel):
        await channel.send(self.format_quote())

    async def all(self, message):
        # fix for discord message limit
        print("get all quotes")
        self.get_all_quotes()
        everything = '```'
        for q in self.all_quotes:
            self.quote = q[0]
            self.quotee = q[1]
            self.date_time = q[2]
            current = f'{self.format_quote()}\n'
            print(current)
            everything += current
        everything += '```'
        await message.channel.send(everything)

    async def quote_process(self, message):
        print("stripping message")
        msg = message.content.strip('+q ')
        if not msg or msg == 'help':
            await message.channel.send('use \'+q\' followed by a space, the quotee|quote i.e:\n```+q Joey|I can\'t hear you over doing that thing you just said```')
        else:
            print("start quote process")
            self.session_user = message.author
            self.date_time = datetime.datetime.now()
            self.date_time = self.date_time.strftime(r"%H:%M %m/%d/%Y")
            msg = msg.split('|')
            self.quotee = msg[0].strip()
            self.quote = msg[1].strip()
            self.session_state = 1
            await message.channel.send('are you sure you want to add the quote? (y/n)')
            await message.channel.send(f'```{self.format_quote()}```')

    async def manual_process(self, message):
        msg = message.content.strip('+m ')
        if not msg or msg == 'help':
            await message.channel.send('use \'+m\' followed by a space and the quotee|quote|date i.e:\n```+m Joey|I can\'t hear you over doing that thing you just said|2:00 04/20/69```')
        else:
            print("start manual process")
            self.session_user = message.author
            msg = msg.split('|')
            self.quotee = msg[0].strip()
            self.quote = msg[1].strip()
            self.date_time = msg[2].strip()
            self.session_state = 1
            await message.channel.send(f'```{self.format_quote()}```')
            await message.channel.send('are you sure you want to add the quote? (y/n)')

    async def lets_go_gambling(self, message):
        print("checking random")
        print(chance_limit - self.quote_chance)
        calc = random.randint(0, (chance_limit - self.quote_chance))
        if calc < random.randint(1, 5):
            print("success, getting a random quote")
            self.random_quote()
            self.quote_chance = 0
            await message.channel.send(self.format_quote())
        else:
            print("failure, iterating chance")
            self.quote_chance += random.randint(1, 5)
            print(f'qc: {self.quote_chance}')
            if self.quote_chance % 10 == 0:
                with open(qc_path, "w") as f:
                    f.write(str(self.quote_chance))

    async def on_ready(self):
        print(f'Logged on as {self.user}')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        print(f'Current state: {self.session_state}')
        if message.author.bot:
            print("bot msg")
        elif self.session_state == 0:
            if message.content.startswith('+a'):
                await self.all(message)
            elif message.content.startswith('+r'):
                print("getting a random quote")
                self.random_quote()
                await message.channel.send(self.format_quote())
            elif message.content == '+help' or message.content == '+h':
                print("sending help block")
                await message.channel.send(help_msg)
            elif message.content.startswith('+q'):
                await self.quote_process(message)
            elif message.content.startswith('+m'):
                await self.manual_process(message)
            else:
                await self.lets_go_gambling(message)
        elif self.session_state == 1 and self.session_user == message.author:
            if message.content == 'y':
                self.add_quote()
                await message.channel.send('quote added successfully')
                self.session_state = 0
                self.session_user == ''
            elif message.content == 'n':
                await message.channel.send('quote reset')
                self.session_state = 0
                self.session_user == ''


token = retrieveToken()
intents = discord.Intents(messages=True)
intents.message_content = True
client = MyClient(intents=intents)
client.start_db()
client.run(token, log_handler=handler, log_level=logging.DEBUG)
