from .model.utils import UserChatHistory
from dataclasses import dataclass, field
import sqlite3


@dataclass
class User():
    stream: int = False
    model: str = "flash"
    lang: str = "en"
    english: UserChatHistory = field(default_factory=UserChatHistory)
    other: UserChatHistory = field(default_factory=UserChatHistory)

class Users():
    """
    Class containing users information.
    """

    def __init__(self):
        self.dict: dict[int, User] = {}

    def stream(self, user_id: int):
        return self.dict.setdefault(user_id, User()).stream

    def model(self, user_id: int):
        return self.dict.setdefault(user_id, User()).model

    def lang(self, user_id: int):
        return self.dict.setdefault(user_id, User()).lang

    def english(self, user_id: int):
        return self.dict.setdefault(user_id, User()).english

    def other(self, user_id: int):
        return self.dict.setdefault(user_id, User()).other

    def add_user(self, user_id: int, **kwargs):
        self.dict[user_id] = User(**kwargs)

    def clear_english(self, user_id: int):
        """
        Clears english history

        Args:
            user_id: user identifier whose 'english' history will be deleted
        """
        self.dict[user_id].english.clear()

    def clear_other(self, user_id: int):
        """
        Clears other history

        Args:
            user_id: user identifier whose 'other' history will be deleted
        """
        self.dict[user_id].other.clear()

    def get_user_history(self, user_id: int, lang_group: str) -> UserChatHistory:
        if lang_group == 'eng':
            return self.english(user_id)
        elif lang_group == 'oth':
            return self.other(user_id)
        else:
            raise ValueError(f"Unsupported lang_group: {lang_group}")

    def load_from_db(self, db_path: str):
        """
        Loads users from the SQL table.

        Args:
            db_path: path to data base.
        """

        connection = sqlite3.connect(db_path)

        try:
            cursor = connection.cursor()
            cursor.execute('SELECT id, stream, model, lang, eng_his, oth_his FROM users')
            rows = cursor.fetchall()

            for row in rows:
                user_id, stream, model, lang, eng_his, oth_his = row

                english_history = UserChatHistory.model_validate_json(eng_his) if eng_his else UserChatHistory()
                other_history = UserChatHistory.model_validate_json(oth_his) if oth_his else UserChatHistory()

                self.add_user(
                    user_id,
                    stream=stream,
                    model=model,
                    lang=lang,
                    english=english_history,
                    other=other_history
                )
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            connection.close()