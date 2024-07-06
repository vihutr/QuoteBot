import datetime
import discord
import logging
import os
import random
import sqlite3

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
database_folder = 'database'
database = os.path.join(database_folder, 'database.db')


def retrieveToken():
    with open("secret/token", "r") as file:
        token = file.read()
        token = token.splitlines()[0]
        file.close()
        return token


class MyClient(discord.Client):
    def start_db(self):
        self.conn = sqlite3.connect(database)
        self.cur = self.conn.cursor()
        self.cur.execute('''CREATE TABLE if not exists Quote
                         (quote TEXT, quotee TEXT, datetime TEXT)''')
        self.conn.commit()
        print(f"Connected to {database}")
        self.quote_chance = 0
        self.quote = ''
        self.quotee = ''
        self.date_time = ''
        self.msg_state = 0
        self.sess_auth = ''
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

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        if message.content == '+help' or message.content == '+h' and self.msg_state == 0:
            await message.channel.send(
"""```
Commands\n
Use any command without any input to see more info
+q: add a quote, automatically timestamped
+m: add a quote and add a timestamp after
+r: get a random quote from the database
+a: get all quotes (doesn't actually work lmao)
+help or +h: this thing

if you add a dumb quote I kill you instantly
```"""
                    )
        elif message.content.startswith('+q') and self.msg_state == 0:
            msg = message.content.strip('+q ')
            if not msg or msg == 'help':
                await message.channel.send('use \'+q\' followed by a space, the quotee|quote i.e:\n```+q Joey|I can\'t hear you over doing that thing you just said```')
            else:
                self.sess_auth = message.author
                self.date_time = datetime.datetime.now()
                self.date_time = self.date_time.strftime(r" %H:%M %m/%d/%Y")
                msg = msg.split('|')
                self.quotee = msg[0]
                self.quote = msg[1]
                self.msg_state = 1
                await message.channel.send('Are you sure you want to add the quote? (y/n)')
                await message.channel.send(f'```{self.format_quote()}```')
        elif self.msg_state == 1 and self.sess_auth == message.author:
            if message.content == 'y':
                self.add_quote()
                await message.channel.send('quote added successfully')
                self.msg_state = 0
                self.sess_auth == ''
            elif message.content == 'n':
                await message.channel.send('quote reset')
                self.msg_state = 0
                self.sess_auth == ''

        elif message.author.bot:
            print("bot msg")
        elif message.content.startswith('+m') and self.msg_state == 0:
            msg = message.content.strip('+m ')
            if not msg:
                await message.channel.send('use \'+m\' followed by a space and the quotee|quote i.e:\n```+m Joey|I can\'t hear you over doing that thing you just said```\n then add the date for your next input')
            else:
                self.msg_state = 2
                self.sess_auth = message.author
                msg = msg.split('|')
                self.quotee = msg[0]
                self.quote = msg[1]
                await message.channel.send('Add the date manually, preferably in the format "Hours:Minutes Month/Day/Year"')
        elif self.msg_state == 2 and self.sess_auth == message.author:
            self.date_time = message.content
            self.msg_state = 3
            await message.channel.send('Are you sure you want to add the quote? (y/n)')
            await message.channel.send(f'```{self.format_quote()}```')
        elif self.msg_state == 3 and self.sess_auth == message.author:
            if message.content == 'y':
                self.add_quote()
                await message.channel.send('quote added successfully')
                self.msg_state = 0
                self.sess_auth == ''
            elif message.content == 'n':
                await message.channel.send('quote reset')
                self.msg_state = 0
        elif message.content.startswith('+a') and self.msg_state == 0:
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
        else:
            if message.content.startswith('+r') and self.msg_state == 0:
                print("getting a random quote")
                self.random_quote()
                await message.channel.send(self.format_quote())
            elif random.randint(0, 1000-self.quote_chance) < 1:
                self.random_quote()
                self.quote_chance = 0
                await message.channel.send(self.format_quote())
            else:
                self.quote_chance += 1
                print(f'qc: {self.quote_chance}')


token = retrieveToken()
intents = discord.Intents(messages=True)
intents.message_content = True
client = MyClient(intents=intents)
client.start_db()
client.run(token, log_handler=handler, log_level=logging.DEBUG)
