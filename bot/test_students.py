import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
from typing import List, Dict, Optional, Tuple


class UniversityDB:
    def __init__(self, dbname: str, user: str, password: str, host: str = 'localhost', port: str = '5432'):
        self.conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="123",
            host="localhost",
            port="5432",
        )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor(cursor_factory=DictCursor)

    def close(self):
        self.cursor.close()
        self.conn.close()

    # Студенты
    def add_student(self, group_id: int, full_name: str) -> int:
        query = sql.SQL("""
            INSERT INTO Студенты (id_группы, ФИО)
            VALUES (%s, %s)
            RETURNING id_студента
        """)
        self.cursor.execute(query, (group_id, full_name))
        return self.cursor.fetchone()['id_студента']

    def get_student(self, student_id: int) -> Dict:
        query = sql.SQL("""
            SELECT * FROM Студенты
            WHERE id_студента = %s
        """)
        self.cursor.execute(query, (student_id,))
        return dict(self.cursor.fetchone())

    def update_student(self, student_id: int, group_id: Optional[int] = None, full_name: Optional[str] = None):
        updates = []
        params = []

        if group_id is not None:
            updates.append("id_группы = %s")
            params.append(group_id)
        if full_name is not None:
            updates.append("ФИО = %s")
            params.append(full_name)

        if updates:
            params.append(student_id)
            query = sql.SQL("""
                UPDATE Студенты
                SET {}
                WHERE id_студента = %s
            """).format(sql.SQL(', ').join(map(sql.SQL, updates)))
            self.cursor.execute(query, params)

    def delete_student(self, student_id: int):
        query = sql.SQL("""
            DELETE FROM Студенты
            WHERE id_студента = %s
        """)
        self.cursor.execute(query, (student_id,))

    # Группы
    def add_group(self, specialty_id: int, admission_year: str) -> int:
        query = sql.SQL("""
            INSERT INTO Группа (id_Специальности, год_поступления)
            VALUES (%s, %s)
            RETURNING id_Группы
        """)
        self.cursor.execute(query, (specialty_id, admission_year))
        return self.cursor.fetchone()['id_Группы']

    def get_group(self, group_id: int) -> Dict:
        query = sql.SQL("""
            SELECT * FROM Группа
            WHERE id_Группы = %s
        """)
        self.cursor.execute(query, (group_id,))
        return dict(self.cursor.fetchone())

    # Специальности
    def add_specialty(self, name: str) -> int:
        query = sql.SQL("""
            INSERT INTO Специальность (название)
            VALUES (%s)
            RETURNING id_Специальности
        """)
        self.cursor.execute(query, (name,))
        return self.cursor.fetchone()['id_Специальности']

    # Предметы
    # def add_subject(self, name: str) -> int:
    #     query = sql.SQL("""
    #         INSERT INTO Предмет (Название)
    #         VALUES (%s)
    #         RETURNING id_Предмета
    #     """)
    #     self.cursor.execute(query, (name,))
    #     return self.cursor.fetchone()['id_Предмета']

    # Связь специальностей и предметов
    def add_specialty_subject(self, specialty_id: int, subject_id: int):
        query = sql.SQL("""
            INSERT INTO Спец_пред (id_Специальности, id_Предмета)
            VALUES (%s, %s)
        """)
        self.cursor.execute(query, (specialty_id, subject_id))

    # Темы
    def add_topic(self, subject_id: int, name: str) -> int:
        query = sql.SQL("""
            INSERT INTO Темы (id_предмета, название)
            VALUES (%s, %s)
            RETURNING id_темы
        """)
        self.cursor.execute(query, (subject_id, name))
        return self.cursor.fetchone()['id_темы']

    # Тесты
    def add_test(self, group_id: int, topic_id: int, date: str) -> int:
        query = sql.SQL("""
            INSERT INTO Тесты (id_группы, id_темы, дата)
            VALUES (%s, %s, %s)
            RETURNING id_теста
        """)
        self.cursor.execute(query, (group_id, topic_id, date))
        return self.cursor.fetchone()['id_теста']

    # Вопросы
    def add_question(self, topic_id: int, text: str, correct_answers: str, points: int) -> int:
        query = sql.SQL("""
            INSERT INTO Вопросы (id_темы, текст, правильные_ответы, баллы)
            VALUES (%s, %s, %s, %s)
            RETURNING id_вопроса
        """)
        self.cursor.execute(query, (topic_id, text, correct_answers, points))
        return self.cursor.fetchone()['id_вопроса']

    # Добавление вопроса в тест
    def add_question_to_test(self, test_id: int, question_id: int):
        query = sql.SQL("""
            INSERT INTO Вопросы_теста (id_теста, id_вопроса)
            VALUES (%s, %s)
        """)
        self.cursor.execute(query, (test_id, question_id))

    # Результаты теста
    def add_test_result(self, student_id: int, test_id: int, student_score: int, grade: int, date: str) -> int:
        query = sql.SQL("""
            INSERT INTO Результаты (id_студента, id_теста, Балл_студента, Оценка, дата)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_проходимого_теста
        """)
        self.cursor.execute(query, (student_id, test_id, student_score, grade, date))
        return self.cursor.fetchone()['id_проходимого_теста']

    # Ответы студента на вопросы теста
    def add_student_answer(self, test_result_id: int, question_id: int, student_answer: str, points: int) -> int:
        query = sql.SQL("""
            INSERT INTO Проходимый_тест (ID_проходимого_теста, ID_вопроса, ответ_студента, балл)
            VALUES (%s, %s, %s, %s)
            RETURNING ID_проходимого_теста
        """)
        self.cursor.execute(query, (test_result_id, question_id, student_answer, points))
        return self.cursor.fetchone()['ID_проходимого_теста']

    # Получение результатов теста для студента
    def get_student_test_results(self, student_id: int) -> List[Dict]:
        query = sql.SQL("""
            SELECT r.*, t.дата as дата_теста, tm.название as тема_теста, p.Название as предмет
            FROM Результаты r
            JOIN Тесты t ON r.id_теста = t.id_теста
            JOIN Темы tm ON t.id_темы = tm.id_темы
            JOIN Предмет p ON tm.id_предмета = p.id_Предмета
            WHERE r.id_студента = %s
            ORDER BY r.дата DESC
        """)
        self.cursor.execute(query, (student_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    # Получение деталей прохождения теста
    def get_test_result_details(self, test_result_id: int) -> Dict:
        # Основная информация о результате
        query = sql.SQL("""
            SELECT r.*, s.ФИО as студент, t.дата as дата_теста, 
                   tm.название as тема_теста, p.Название as предмет
            FROM Результаты r
            JOIN Студенты s ON r.id_студента = s.id_студента
            JOIN Тесты t ON r.id_теста = t.id_теста
            JOIN Темы tm ON t.id_темы = tm.id_темы
            JOIN Предмет p ON tm.id_предмета = p.id_Предмета
            WHERE r.id_проходимого_теста = %s
        """)
        self.cursor.execute(query, (test_result_id,))
        result = dict(self.cursor.fetchone())

        # Ответы студента
        query = sql.SQL("""
            SELECT pt.*, q.текст as вопрос, q.правильные_ответы, q.баллы as макс_балл
            FROM Проходимый_тест pt
            JOIN Вопросы q ON pt.ID_вопроса = q.id_вопроса
            WHERE pt.ID_проходимого_теста = %s
        """)
        self.cursor.execute(query, (test_result_id,))
        result['answers'] = [dict(row) for row in self.cursor.fetchall()]

        return result

    # Получение списка студентов в группе
    def get_group_students(self, group_id: int) -> List[Dict]:
        query = sql.SQL("""
            SELECT * FROM Студенты
            WHERE id_группы = %s
            ORDER BY ФИО
        """)
        self.cursor.execute(query, (group_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    # Получение списка тестов для группы
    def get_group_tests(self, group_id: int) -> List[Dict]:
        query = sql.SQL("""
            SELECT t.*, tm.название as тема, p.Название as предмет
            FROM Тесты t
            JOIN Темы tm ON t.id_темы = tm.id_темы
            JOIN Предмет p ON tm.id_предмета = p.id_Предмета
            WHERE t.id_группы = %s
            ORDER BY t.дата DESC
        """)
        self.cursor.execute(query, (group_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    # Получение вопросов для теста
    def get_test_questions(self, test_id: int) -> List[Dict]:
        query = sql.SQL("""
            SELECT q.*
            FROM Вопросы_теста qt
            JOIN Вопросы q ON qt.id_вопроса = q.id_вопроса
            WHERE qt.id_теста = %s
            ORDER BY q.id_вопроса
        """)
        self.cursor.execute(query, (test_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    # Получение статистики по тесту
    def get_test_statistics(self, test_id: int) -> Dict:
        # Основная информация о тесте
        query = sql.SQL("""
            SELECT t.*, tm.название as тема, p.Название as предмет, g.id_Специальности
            FROM Тесты t
            JOIN Темы tm ON t.id_темы = tm.id_темы
            JOIN Предмет p ON tm.id_предмета = p.id_Предмета
            JOIN Группа g ON t.id_группы = g.id_Группы
            WHERE t.id_теста = %s
        """)
        self.cursor.execute(query, (test_id,))
        test_info = dict(self.cursor.fetchone())

        # Результаты студентов
        query = sql.SQL("""
            SELECT r.*, s.ФИО as студент
            FROM Результаты r
            JOIN Студенты s ON r.id_студента = s.id_студента
            WHERE r.id_теста = %s
            ORDER BY r.Балл_студента DESC
        """)
        self.cursor.execute(query, (test_id,))
        test_info['results'] = [dict(row) for row in self.cursor.fetchall()]

        # Статистика
        if test_info['results']:
            scores = [r['Балл_студента'] for r in test_info['results']]
            test_info['average_score'] = sum(scores) / len(scores)
            test_info['max_score'] = max(scores)
            test_info['min_score'] = min(scores)

        return test_info
    def add_subject(self, name: str) -> int:
        """Добавление нового предмета в базу данных."""
        query = """
            INSERT INTO Предмет (Название)
            VALUES (%s)
            RETURNING id_Предмета
        """
        self.cursor.execute(query, (name,))
        self.connection.commit()
        return self.cursor.fetchone()[0]

    def get_all_subjects(self):
        """Получение всех предметов из базы данных."""
        query = """
            SELECT id_Предмета AS id, Название AS name
            FROM Предмет
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_subject_by_id(self, subject_id: int):
        """Получение предмета по его ID."""
        query = """
            SELECT id_Предмета AS id, Название AS name
            FROM Предмет
            WHERE id_Предмета = %s
        """
        self.cursor.execute(query, (subject_id,))
        return self.cursor.fetchone()


    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.cursor()



# Пример использования
if __name__ == "__main__":
    # Подключение к базе данных
    db = UniversityDB(dbname="university", user="postgres", password="password")
    db.close()