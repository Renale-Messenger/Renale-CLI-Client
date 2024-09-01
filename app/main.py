from rich.console import Console, Group
from rich import print, get_console
from rich.align import Align
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner

import click
from asyncio import sleep as async_sleep, run as async_run
from typing import List
from datetime import datetime
from pynput import keyboard
from time import sleep
import threading
import requests
from sys import exit


#keyboard.add_hotkey("escape", lambda: print("Succesfuly escaped"))

SERVER_URL: str = "http://127.0.0.1:9789"


def print_err(exc: str):
    print(Panel.fit(f'An error occurred:\n{exc}', style='#ff0000'))


def input(prompt: str = '') -> str:
    return get_console().input(prompt)


class RenaleClient:
    after: int = 0
    in_chat: bool = False

    name: str
    password: str
    token: str

    def __init__(self):
        get_console().clear()
        sign_table = Group(
            Panel(Align.center('Sign In'), style='#1133ff', width=80),
            Panel(Align.center('Sign Up'), style='#00ff00', width=80),
            )
        print(Panel(Align.center(sign_table), title='Authorisation', width=25))
        input("Make a choice: ")

    def login(self):
        while True:
            get_console().clear()
            self.name = input('Enter your name: ')

            if not self.name: 
                print('Name can\'t be empty!')
                continue

            self.password = input('Enter your password: ', password=True)

            if not self.password: 
                print('Password can\'t be empty!')
                continue

            response = requests.post(url=f'{SERVER_URL}/login',
                                     json={'name': self.name, 'password': self.password})
            if response.status_code != 200:
                print_err(f'Wrong name or password!')
                sleep(5)
                continue
            break

    def print_messages(self, messages: List):
        for message in messages:
            dt = datetime.fromtimestamp(message['time'])

            print(Panel.fit(f'{message["text"]}', title=f"{dt.strftime('%H:%M:%S')} - {message['name']}", title_align='left'))
            print(' ')

    async def recieve_msg(self, chat):
        print(chat)
        while True:
            response = requests.get(url=f'{SERVER_URL}/messages',
                                    params={'after': self.after})
            try:
                messages = list(filter(lambda a: a['chat'] == chat, response.json()['messages']))
            except requests.exceptions.JSONDecodeError as e:
                messages = []
            if messages:
                self.print_messages(messages)
                self.after = messages[-1]['time']

            await async_sleep(1)

    def send_msg(self, chat: str):
        if not self.in_chat:
            print('You need to be in a chat to send messages!')
            return
        while True:
            text = input()
            formated_text = text.split()
            formated_text = ''.join(formated_text)
            if formated_text == "":
                print("\033[FDon't write empty messages!")
                return self.send_msg(chat)

            response = requests.post(url=f'{SERVER_URL}/send',
                                     json={'chat': chat, 'id': self.name, 'text': text})

    async def back(self):
        if self.in_chat:
            self.in_chat = False
            self.send_thread._stop()
            self.recieve_thread._stop()
        await self.start()

    def on_press(self, key):
        try:
            if key == keyboard.Key.esc:
                async_run(self.back())
        except AttributeError as e:
            print(f"Invalid key {key}!\n{e}")

    async def open_chat(self, chat):
        self.in_chat = True
        self.recieve_thread = threading.Thread(target=lambda: async_run(self.recieve_msg(chat)), daemon=True)
        self.send_thread = threading.Thread(target=lambda: async_run(self.send_msg(chat)), daemon=True)
        get_console().clear()
        self.recieve_thread.start()
        self.send_thread.start()

        with keyboard.Listener(on_press=self.on_press) as listener:
            listener.join()

    async def start(self):
        get_console().clear()
        print(Panel.fit("open [chat name || settings]\nexit\nhotkeys", title="Available commands", title_align="center"))
        command = input("Command: ")
        if command[:4] == "open":
            chat_name = command[5:]
            if chat_name == '':
                await self.start()
            else:
                await self.open_chat(chat_name)
        elif command == "exit":
            exit(0)
        elif command == "hotkeys":
            get_console().clear()
            print(Panel.fit("Escape - back\nEnter - sends message when chat is open", title="Available hotkyes", title_align="center"))

            with keyboard.Listener(on_press=self.on_press) as listener:
                listener.join()
        else:
            print("Incorrect command!")
            await async_sleep(1)
            await self.start()
