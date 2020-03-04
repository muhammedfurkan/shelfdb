import shutil
import unittest
from multiprocessing import Process
from pathlib import Path
from time import sleep
import uuid
from datetime import datetime
from shelfdb import server
import shelfquery
from dictify import Model, Field, define

shelfdb_process = None
db = None

def setUpModule():
    global shelfdb_process
    global db
    shelfdb_process = Process(target=server.main, daemon=True)
    shelfdb_process.start()
    db = shelfquery.db()
    i = 0
    while True:
        sleep(0.1)
        try:
            db.shelf('note').first().run()
            break
        except ConnectionRefusedError:
            if i >= 10:
                raise TimeoutError
            i += 1


def tearDownModule():
    global shelfdb_process
    shelfdb_process.terminate()
    shutil.rmtree(Path('db'))


class Note(Model):
    title = Field().required().type(str)
    note = Field().type(str)
    datetime = Field().default(datetime.utcnow)


class TestRetrieveData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.notes = []
        for i in range(5):
            cls.notes.append(Note({'title': 'note-' + str(i)}))
        for note in cls.notes:
            id = db.shelf('note').insert(note.copy()).run()
            note.id = id

    @classmethod
    def tearDownClass(cls):
        db.shelf('note').delete().run()

    def test_iterator(self):
        notes = db.shelf('note').run()
        self.assertEqual(len(notes), len(self.notes))

    def test_get(self):
        note = db.shelf('note').get(self.notes[0].id).run()
        self.assertDictEqual(self.notes[0], note)

    def test_first(self):
        note = db.shelf('note').first().run()
        self.assertIsInstance(note, dict)

    def test_filter(self):
        notes = db.shelf('note').filter(lambda note: note['title'] == 'note-1').run()
        self.assertIsInstance(notes, list)
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]['title'], 'note-1')


class TestModifyData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.notes = []
        for i in range(5):
            cls.notes.append(Note({'title': 'note-' + str(i)}))
        for note in cls.notes:
            id = db.shelf('note').insert(note.copy()).run()
            note.id = id

    @classmethod
    def tearDownClass(cls):
        db.shelf('note').delete().run()

    def test_update(self):
        db.shelf('note').first().update({'title': 'test_update'}).run()
        note = db.shelf('note').first().run()
        self.assertEqual(note['title'], 'test_update')
