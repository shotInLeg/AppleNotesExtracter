#!/usr/bin/env python
# coding: utf8
import os
import json

import gzip
import sqlite3


APPLE_NOTES_DATABASE = "/Users/{}/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite".format(os.getlogin())
APPLE_NOTES_DATA_TABLE = "ZICNOTEDATA"
APPLE_NOTES_DATA_FIELD = "ZDATA"


def init_table_schema(cursor, table_name):
    cursor.execute("PRAGMA table_info({})".format(table_name))
    return {i: x[1] for i, x in enumerate(cursor.fetchall())}


def select(cursor, table_name, limit=-1, table_schema=None):
    table_schema = table_schema or init_table_schema(cursor, table_name)

    cursor.execute("SELECT * FROM {table_name} LIMIT {limit}".format(
        table_name=table_name,
        limit=limit,
    ))

    rows = []
    for row in cursor.fetchall():
        named_row = {}
        for field_id, field in enumerate(row):
            named_row[table_schema[field_id]] = field
        rows.append(named_row)

    return rows


def decode_apple_note_data(encoded_note_data):
    encoded_note_data = gzip.decompress(encoded_note_data)

    start_index = encoded_note_data.find(b'\x00\x10\x00\x1a')  # Magic seq
    if start_index == -1:
        return ""

    start_index = encoded_note_data.find(b'\x12', start_index + 1) + 2  # Magic byte
    if start_index == -1:
        return ""

    end_index = encoded_note_data.find(b'\x04\x08\x00\x10\x00\x10\x00\x1a\x04\x08\x00', start_index)  # Magic seq
    if end_index < start_index:
        return ""

    note_data = encoded_note_data[start_index:end_index]
    return note_data.decode('utf8', errors='ignore')


def fetch_apple_notes(cursor):
    table_schema = init_table_schema(cursor, APPLE_NOTES_DATA_TABLE)

    apple_notes = []
    for note in select(cursor, APPLE_NOTES_DATA_TABLE, table_schema=table_schema):
        apple_notes.append(decode_apple_note_data(note[APPLE_NOTES_DATA_FIELD]))

    return apple_notes


def main():
    connect = sqlite3.connect(APPLE_NOTES_DATABASE)
    cursor = cursor = connect.cursor()

    apple_notes = fetch_apple_notes(cursor)

    print(json.dumps(apple_notes, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    main()
