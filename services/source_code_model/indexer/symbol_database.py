import sqlite3

class SymbolDatabase(object):
    VERSION_MAJOR = 0
    VERSION_MINOR = 1

    def __init__(self, db_filename = None):
        self.filename = db_filename
        if db_filename:
            self.db_connection = sqlite3.connect(db_filename)
        else:
            self.db_connection = None

    def __del__(self):
        if self.db_connection:
            self.db_connection.close()

    def open(self, db_filename):
        if not self.db_connection:
            self.db_connection = sqlite3.connect(db_filename)
            self.filename = db_filename

    def close(self):
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None

    def is_open(self):
        return self.db_connection is not None

    def get_all(self):
        # TODO Use generators
        return self.db_connection.cursor().execute('SELECT * FROM symbol')

    def get_by_id(self, id):
        return self.db_connection.cursor().execute('SELECT * FROM symbol WHERE usr=?', (id,))

    def get_definition(self, id):
        return self.db_connection.cursor().execute('SELECT * FROM symbol WHERE usr=? AND is_definition=1', (id,))

    def insert_single(self, filename, line, column, unique_id, context, symbol_kind, is_definition):
        try:
            if unique_id != '':
                self.db_connection.cursor().execute('INSERT INTO symbol VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (filename, line, column, unique_id, context, symbol_kind, is_definition,)
                )
        except sqlite3.IntegrityError:
            pass

    def insert_from(self, symbol_db_filename_list):
        for db in symbol_db_filename_list:
            symbol_db = SymbolDatabase(db)
            rows = symbol_db.get_all()
            if rows:
                for row in rows:
                    self.insert_single(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                self.flush()
            symbol_db.close()

    def flush(self):
        self.db_connection.commit()

    def delete(self, filename):
        self.db_connection.cursor().execute('DELETE FROM symbol WHERE filename=?', (filename,))

    def delete_all(self):
        self.db_connection.cursor().execute('DELETE FROM symbol')

    def create_data_model(self):
        self.db_connection.cursor().execute(
            'CREATE TABLE IF NOT EXISTS symbol ( \
                filename        text,            \
                line            integer,         \
                column          integer,         \
                usr             text,            \
                context         text,            \
                kind            integer,         \
                is_definition   boolean,         \
                PRIMARY KEY(filename, usr, line) \
             )'
        )
        self.db_connection.cursor().execute(
            'CREATE TABLE IF NOT EXISTS version ( \
                major integer,            \
                minor integer,            \
                PRIMARY KEY(major, minor) \
             )'
        )
        self.db_connection.cursor().execute(
            'INSERT INTO version VALUES (?, ?)', (SymbolDatabase.VERSION_MAJOR, SymbolDatabase.VERSION_MINOR,)
        )
