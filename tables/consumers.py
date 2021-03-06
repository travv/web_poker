from django.core import serializers
from channels.generic.websocket import WebsocketConsumer
from accounts.models import CustomUser
from .models import Table
from .serializers import TableSerializer
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
import time
from poker.consumers import Players

import json
import threading

class MoneyConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.username = self.scope['url_route']['kwargs']['username']
        self.player = CustomUser.objects.get(username=self.username)
        self.stopEvent = threading.Event()
        self.thread = threading.Thread(target=self.checkMoney, args=(self.stopEvent,), daemon=True)
        self.thread.start()

    def disconnect(self, closeCode):
        self.stopEvent.set()

    def checkMoney(self, stopEvent):
        while not stopEvent.is_set():
            self.player = CustomUser.objects.get(username=self.username)
            self.totalMoney = self.player.money
            self.moneyInTable = 0
            try:
                self.playerGame = Players.objects.get(pk=self.player)
                self.moneyInTable = self.playerGame.moneyInTable
                self.totalMoney += self.moneyInTable

            except Players.DoesNotExist:
                pass

            self.tables = Table.objects.all()
            self.serializedTables = TableSerializer(self.tables, many=True)
            self.tableJSON = JSONRenderer().render(self.serializedTables.data)
            
            self.send(text_data=json.dumps({
                'money': self.totalMoney,
                'moneyInTable': self.moneyInTable,
                'tables': json.loads(self.tableJSON),
            }))
            time.sleep(1)
