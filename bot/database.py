import psycopg2
from datetime import date
from psycopg2 import OperationalError, DatabaseError
from psycopg2.extras import DictCursor
from typing import Set
from typing import Optional

import logging
from typing import List, Dict, Tuple, Any

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect()


    # def connect(self):
    #     """Устанавливаем соединение с базой данных"""
    #     try:
    #         self.conn = psycopg2.connect(
    #             dbname="postgres",
    #             user="postgres",
    #             password="123",
    #             host="localhost",
    #             port="5432",
    #             connect_timeout=5
    #         )
    #
    #         logger.info("✅ Успешное подключение к PostgreSQL")
    #     except OperationalError as e:
    #         logger.critical(f"❌ Ошибка подключения: {e}")
    #         raise

    def connect(self):
        """Устанавливаем соединение с базой данных"""
        try:
            self.conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="123",
                host="localhost",
                port="5432",
                connect_timeout=5
            )
            self.cursor = self.conn.cursor()  # Инициализация курсора
            logger.info("✅ Успешное подключение к PostgreSQL")
        except OperationalError as e:
            logger.critical(f"❌ Ошибка подключения: {e}")
            self.conn = None
            self.cursor = None
            raise

    def reconnect(self):
        """Переподключение к базе при разрыве соединения"""
        try:
            if self.conn and not self.conn.closed:
                self.conn.close()
            self.connect()
            return True
        except Exception as e:
            logger.error(f"Ошибка переподключения: {e}")
            return False

    def get_specialties(self) -> List[Tuple[int, str]]:
        """Получение списка специальностей"""
        query = '''
        SELECT "id_Специальности", "название" 
        FROM "Специальность"
        ORDER BY "id_Специальности"
        '''
        return self.execute_query(query)

    def execute_query(self, query: str, params: tuple = None) -> List[Tuple[Any, ...]]:
        """Выполнение SQL запроса с возвратом результатов"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if cursor.description:  # Если есть результаты
                    return cursor.fetchall()
                self.conn.commit()
                return []
        except (OperationalError, DatabaseError) as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            if self.reconnect():
                return self.execute_query(query, params)
            raise


    def get_students(self) -> List[Tuple[int, str]]:
        """Получение списка студентов"""
        query = "SELECT ID_студента, ФИО FROM Студенты ORDER BY ФИО"
        return self.execute_query(query)

    def get_student_results(self, student_id: int) -> List[Tuple]:
        """Получение результатов студента по вашей структуре таблиц"""
        query = """
        SELECT 
            r."Балл_студента",
            r."Оценка",
            r."дата",
            p."id_вопроса",
            p."ответ_студента",
            p."балл"
        FROM "Результаты" r
        LEFT JOIN "Проходимый_тест" p 
            ON r."id_проходимого_теста" = p."id_проходимого_теста"
        WHERE r."id_студента" = %s
        ORDER BY r."дата" DESC
        """
        return self.execute_query(query, (student_id,))

    def get_all_students(self) -> List[Tuple]:
        """Получение списка всех студентов"""
        query = '''SELECT * FROM "Студенты" ORDER BY "ФИО"'''
        return self.execute_query(query)

    def get_student_info(self, student_id: int) -> Tuple:
        """Получение информации о студенте"""
        query = '''SELECT * FROM "Студенты" WHERE "id_студента" = %s'''
        result = self.execute_query(query, (student_id,))
        return result[0] if result else None

    # def get_tests_for_group(self, group_id: int) -> list:
    #     """Возвращает список тестов для группы"""
    #     query = """
    #         SELECT t.id_теста, t.дата, tm.название
    #         FROM "Тесты" t
    #         JOIN "Темы" tm ON t.id_темы = tm.id_темы
    #         WHERE t.id_группы = %s
    #         ORDER BY t.дата DESC
    #     """
    #     self.cursor.execute(query, (group_id,))
    #     return self.cursor.fetchall()

    def get_themes_for_group(self, group_id: int) -> list:
        """Получение тем для группы"""
        query = """
        SELECT DISTINCT t.id_темы, t.название
        FROM "Темы" t
        JOIN "Тесты" ts ON t.id_темы = ts.id_темы
        WHERE ts.id_группы = %s
        ORDER BY t.название
        """
        self.cursor.execute(query, (group_id,))
        return self.cursor.fetchall()

    def add_student(self, name: str) -> int:
        """Добавление нового студента"""
        query = "INSERT INTO Студенты (ФИО) VALUES (%s) RETURNING ID_студента"
        result = self.execute_query(query, (name,))
        return result[0][0] if result else None

    def get_groups(self) -> list:
        """Получение списка групп"""
        query = """
        SELECT g.id_Группы, s.название, g.год_поступления 
        FROM Группа g
        JOIN Специальность s ON g.id_Специальности = s.id_Специальности
        ORDER BY g.год_поступления DESC
        """
        result = self.execute_query(query)
        print(f"[DEBUG] Groups query result: {result}")
        return result

    def get_groups2(self) -> list:
        query = """
            SELECT g."id_Группы", s."название", g."год_поступления"
            FROM "Группа" g
            JOIN "Специальность" s ON g."id_Специальности" = s."id_Специальности"
            ORDER BY g."год_поступления" DESC
        """
        result = self.execute_query(query)
        print(f"[DEBUG] Groups query result: {result}")

        # Преобразуем результат в список словарей
        return [
            {"id": row[0], "name": f"{row[1]} ({row[2].year})"} for row in result
        ]

    def get_themes_by_subject(self, subject_id):
        query = """
            SELECT "id_темы", "название"
            FROM "Темы"
            WHERE "id_предмета" = %s
            ORDER BY "название"
        """
        result = self.execute_query(query, (subject_id,))
        return [{"id": row[0], "name": row[1]} for row in result]

    def get_group_id_by_test(self, test_id: int) -> int:
        """Получение ID группы по тесту"""
        query = '''SELECT "id_группы" FROM "Тесты" WHERE "id_теста" = %s'''
        result = self.execute_query(query, (test_id,))
        return result[0][0] if result else None

    def get_subjects_by_specialty(self, spec_id: int) -> List[Tuple]:
        """Получение предметов по специальности"""
        query = """
        SELECT p."id_Предмета", p."Название"
        FROM "Спец_пред" sp
        JOIN "Предмет" p ON sp."id_Предмета" = p."id_Предмета"
        WHERE sp."id_Специальности" = %s
        ORDER BY p."Название"
        """
        return self.execute_query(query, (spec_id,))

    def get_themes_by_subject(self, subject_id):
        query = 'SELECT "id_темы", "название" FROM "Темы" WHERE "id_предмета" = %s'
        result = self.execute_query(query, (subject_id,))
        return [{"id": row[0], "name": row[1]} for row in result]

    def get_questions_by_themes(self, theme_ids):
        """Получение всех вопросов по списку тем"""
        if not theme_ids:
            return []

        query = """
            SELECT "id_вопроса", "текст"
            FROM "Вопросы"
            WHERE "id_темы" IN ({})
        """.format(','.join(map(str, theme_ids)))

        self.cursor.execute(query)
        return [{"id": row[0], "text": row[1]} for row in self.cursor.fetchall()]


    def get_test_questions(self, test_id: int) -> List[Tuple]:
        query = """
        SELECT 
            q."id_вопроса",
            q."текст",
            q."правильные_ответы"
        FROM "Вопросы_теста" qt
        JOIN "Вопросы" q ON qt."id_вопроса" = q."id_вопроса"
        WHERE qt."id_теста" = %s
        """
        print(f"[DEBUG] Executing query: {query % (test_id,)}")  # Логирование
        result = self.execute_query(query, (test_id,))
        print(f"[DEBUG] Results: {result}")  # Вывод результатов
        return result

    def get_tests_by_theme(self, theme_id: int) -> List[Tuple]:
        """Получение тестов (ID и дата, но дату не используем)"""
        query = """
        SELECT "id_теста", "дата"  -- Дату выбираем, но не используем
        FROM "Тесты"
        WHERE "id_темы" = %s
        ORDER BY "id_теста" DESC
        """
        return self.execute_query(query, (theme_id,))

    def get_all_groups(self) -> List[Dict]:
        query = ("""
            SELECT g.*, sp.название as специальность
            FROM Группа g
            JOIN Специальность sp ON g.id_Специальности = sp.id_Специальности
            ORDER BY g.год_поступления DESC
        """)
        self.cursor.execute(query)
        return [dict(row) for row in self.cursor.fetchall()]




    def get_low_grades(self):
        """Получение списка студентов с оценкой 2"""
        query = '''
        SELECT 
            s."ФИО" AS student_name,
            g."id_Группы" AS group_id,
            t."id_теста" AS test_id,
            t."дата" AS test_date
        FROM "Результаты" r
        JOIN "Студенты" s ON r."id_студента" = s."id_студента"
        JOIN "Группа" g ON s."id_группы" = g."id_Группы"  -- Проверьте регистр "id_группы"!
        JOIN "Тесты" t ON r."id_теста" = t."id_теста" 
        WHERE r."Оценка" = 2  -- Проверьте название столбца "Оценка"!
        ORDER BY t."дата" DESC
        '''
        results = self.execute_query(query)
        return results

    def add_subject(self, name: str):
        query = '''INSERT INTO "Предметы" ("Название") VALUES (%s)'''
        self.execute_query(query, (name,))

    def get_subjects(self):
        query = '''SELECT * FROM "Предметы" ORDER BY "Название"'''
        return self.execute_query(query)



    def update_subject(self, subject_id: int, new_name: str):
        """Обновление названия предмета в базе данных"""
        query = '''
        UPDATE "Предметы" 
        SET "Название" = %s 
        WHERE "id_Предмета" = %s
        '''
        self.execute_query(query, (new_name, subject_id))


    def get_themes(self, subject_id: int):
        """Получение списка тем по предмету"""
        query = '''
        SELECT "id_темы", "название" 
        FROM "Темы" 
        WHERE "id_предмета" = %s
        ORDER BY "название"
        '''
        return self.execute_query(query, (subject_id,))

    def add_question(self, theme_id: int, text: str, answers: str):
        """Добавление нового вопроса"""
        query = '''
        INSERT INTO "Вопросы" ("id_темы", "текст", "правильные_ответы") 
        VALUES (%s, %s, %s)
        '''
        self.execute_query(query, (theme_id, text, answers))

    def get_questions(self, theme_id: int):
        """Получение вопросов по теме"""
        query = '''
        SELECT "ID_вопроса", "текст" 
        FROM "Вопросы" 
        WHERE "id_темы" = %s
        ORDER BY "id_вопроса"
        '''
        return self.execute_query(query, (theme_id,))

    def build_menu(self, buttons, n_cols=1):
        """Создание структуры меню для кнопок"""
        return [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]

    def test_exists(self, test_id: int) -> bool:
        query = "SELECT EXISTS(SELECT 1 FROM Тесты WHERE id_теста = %s)"
        return self.execute_query(query, (test_id,))[0][0]

    def get_test_dates_in_period(self, start: date, end: date) -> List[date]:
        """Получение уникальных дат тестирования в периоде"""
        query = """
        SELECT DISTINCT дата 
        FROM Тесты 
        WHERE дата BETWEEN %s AND %s 
        ORDER BY дата DESC
        """
        return [row[0] for row in self.execute_query(query, (start, end))]

    def get_groups_for_date(self, target_date: date) -> List[int]:
        """Получение групп с тестами на указанную дату"""
        query = """
        SELECT DISTINCT g.id_Группы 
        FROM Тесты t
        JOIN Группа g ON t.id_группы = g.id_Группы
        WHERE t.дата = %s
        """
        return [row[0] for row in self.execute_query(query, (target_date,))]

    def get_group_results_details(self, group_id: int, date: date) -> List[Dict]:
        """Безопасное получение результатов группы"""
        try:
            query = """
               SELECT 
                   s.ФИО as name,
                   COALESCE(r.Балл_студента, 0) as score,
                   COALESCE(r.Оценка, 0) as grade
               FROM Студенты s
               LEFT JOIN Результаты r ON s.id_студента = r.id_студента
               LEFT JOIN Тесты t ON r.id_теста = t.id_теста
               WHERE 
                   s.id_группы = %s AND
                   t.дата = %s
               ORDER BY s.ФИО
               """
            logger.debug(f"Выполнение запроса: {query} с параметрами ({group_id}, {date})")

            connection = self.get_connection()
            with connection.cursor() as cursor:
                cursor.execute(query, (group_id, date))
                result = cursor.fetchall()

                if not result:
                    logger.info(f"Нет данных для группы {group_id} на {date}")
                    return []

                return [dict(row) for row in result]

        except psycopg2.Error as e:
            logger.error(f"Ошибка PostgreSQL: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Общая ошибка БД: {str(e)}")
            raise

    def get_group_themes(self, group_id: int) -> List[Dict]:
        """Получение тем для конкретной группы"""
        query = """
        SELECT DISTINCT 
            t.id_темы as id,
            t.название as name
        FROM Тесты test
        JOIN Темы t ON test.id_темы = t.id_темы
        WHERE test.id_группы = %s
        ORDER BY t.название
        """
        return self.execute_query(query, (group_id,))

    def get_theme_results(self, group_id: int, theme_id: int) -> List[Dict]:
        """Получение результатов по группе и теме"""
        query = """
        SELECT 
            s.ФИО as name,
            r.Балл_студента as score,
            r.Оценка as grade
        FROM Результаты r
        JOIN Студенты s ON r.id_студента = s.id_студента
        JOIN Тесты t ON r.id_теста = t.id_теста
        WHERE 
            s.id_группы = %s AND
            t.id_темы = %s
        ORDER BY s.ФИО
        """
        return self.execute_query(query, (group_id, theme_id))

    def get_theme_info(self, theme_id: int) -> Dict:
        """Получение информации о теме"""
        query = "SELECT название FROM Темы WHERE id_темы = %s"
        return self.execute_query(query, (theme_id,))[0]

    def get_themes_for_group(self, group_id: int) -> List[Tuple]:
        """Получение списка тем для группы с обработкой ошибок"""
        try:
            query = """
            SELECT 
                t.theme_id,
                t.theme_name 
            FROM themes t
            JOIN tests ON t.theme_id = tests.theme_id
            WHERE tests.group_id = %s
            GROUP BY t.theme_id
            ORDER BY t.theme_name
            """
            logger.debug(f"Выполнение запроса для группы {group_id}")

            with self.connection.cursor() as cursor:
                cursor.execute(query, (group_id,))
                result = cursor.fetchall()
                logger.info(f"Найдено {len(result)} тем")
                return result

        except psycopg2.Error as e:
            logger.error(f"Ошибка PostgreSQL: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Общая ошибка БД: {str(e)}")
            return []

    def get_tests_for_theme(self, group_id: int, theme_id: int) -> List[Tuple]:
        """Получить тесты по теме и группе"""
        query = """
           SELECT 
               test.id_теста,
               test.дата,
               t.название
           FROM Тесты test
           JOIN Темы t ON test.id_темы = t.id_темы
           WHERE 
               test.id_группы = %s AND
               test.id_темы = %s
           ORDER BY test.дата DESC
           """
        return self.execute_query(query, (group_id, theme_id))

    def get_all_themes(self):
        """Получение всех тем"""
        query = '''SELECT * FROM "Темы"'''
        return self.execute_query(query)

    def update_theme(self, theme_id: int, new_name: str):
        """Обновление названия темы"""
        query = '''UPDATE "Темы" SET "название" = %s WHERE "id_темы" = %s'''
        self.execute_query(query, (new_name, theme_id))

    def get_all_questions(self):
        """Получение всех вопросов"""
        query = '''SELECT * FROM "Вопросы"'''
        return self.execute_query(query)

    def get_groups_with_specialty(self) -> List[Tuple]:
        """Получение списка групп с названиями специальностей"""
        query = """
        SELECT g.id_Группы, s.название, g.год_поступления 
        FROM Группа g
        JOIN Специальность s ON g.id_Специальности = s.id_Специальности
        ORDER BY g.год_поступления DESC
        """
        return self.execute_query(query)

    def get_test_info(self, test_id: int) -> Tuple:
        """Получение информации о тесте (предмет, тема, дата)"""
        query = """
        SELECT 
            p.Название,
            tm.название,
            t.дата
        FROM Тесты t
        JOIN Темы tm ON t.id_темы = tm.id_темы
        JOIN Предмет p ON tm.id_предмета = p.id_Предмета
        WHERE t.id_теста = %s
        """
        return self.execute_query(query, (test_id,))[0]

    def get_theme_info(self, theme_id: int) -> Tuple:
        """Получение информации о теме (id, название, id предмета)"""
        query = """
        SELECT id_темы, название, id_предмета 
        FROM Темы
        WHERE id_темы = %s
        """
        result = self.execute_query(query, (theme_id,))
        return result[0] if result else None

    def get_theme_results(self, group_id: int, theme_id: int) -> List[Tuple]:
        """Получение результатов по теме и группе"""
        query = """
        SELECT s.ФИО, r.Балл_студента, r.Оценка
        FROM Результаты r
        JOIN Студенты s ON r.id_студента = s.id_студента
        JOIN Тесты t ON r.id_теста = t.id_теста
        WHERE t.id_группы = %s AND t.id_темы = %s
        ORDER BY s.ФИО
        """
        return self.execute_query(query, (group_id, theme_id))

    def get_students_results_for_test(self, test_id: int, group_id: int) -> List[Tuple]:
        """Полные результаты студентов по тесту"""
        query = """
        SELECT 
            s.ФИО,
            r.Балл_студента,
            (SELECT SUM(p.балл) 
             FROM Проходимый_тест p 
             WHERE p.id_проходимого_теста = r.id_проходимого_теста) as max_score,
            r.Оценка
        FROM Результаты r
        JOIN Студенты s ON r.id_студента = s.id_студента
        WHERE r.id_теста = %s AND s.id_группы = %s
        ORDER BY s.ФИО
        """
        return self.execute_query(query, (test_id, group_id))

    def get_avg_test_score_for_test(self, test_id: int, group_id: int) -> float:
        """Средний балл по тесту для группы"""
        query = """
        SELECT AVG(r.Балл_студента)
        FROM Результаты r
        JOIN Студенты s ON r.id_студента = s.id_студента
        WHERE r.id_теста = %s AND s.id_группы = %s
        """
        result = self.execute_query(query, (test_id, group_id))
        return float(result[0][0]) if result and result[0][0] else 0.0

    def get_all_subjects(self):
        """Получение всех предметов из базы данных."""
        query = """
            SELECT "id_Предмета", "Название"
            FROM "Предмет"
            ORDER BY "Название"
        """
        try:
            self.cursor.execute(query)
            subjects = self.cursor.fetchall()
            # Возвращаем список словарей для удобства
            return [{"id": subj[0], "name": subj[1]} for subj in subjects]
        except Exception as e:
            logger.error(f"Ошибка получения предметов: {e}")
            raise

    def add_theme(self, subject_id: int, theme_name: str):
        # Проверяем, существует ли предмет
        check_subject_query = 'SELECT 1 FROM "Предмет" WHERE "id_Предмета" = %s'
        self.cursor.execute(check_subject_query, (subject_id,))
        if not self.cursor.fetchone():
            raise ValueError(f"Предмет с ID {subject_id} не найден.")

        # Добавляем тему
        insert_query = """
            INSERT INTO "Темы" ("id_предмета", "название")
            VALUES (%s, %s)
            RETURNING "id_темы"
        """
        try:
            self.cursor.execute(insert_query, (subject_id, theme_name))
            self.conn.commit()
            result = self.cursor.fetchone()[0]
            logger.info(f"✅ Тема '{theme_name}' успешно добавлена с ID: {result}")
            return result
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Ошибка добавления темы: {e}", exc_info=True)
            raise

    def get_subject_by_id(self, subject_id: int):
        """Получение предмета по его ID."""
        query = """
               SELECT "id_Предмета" AS id, "Название" AS name
               FROM "Предмет"
               WHERE "id_Предмета" = %s
           """
        try:
            self.cursor.execute(query, (subject_id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Ошибка получения предмета по ID: {e}")
            raise

    def close(self):
        """Закрытие подключения к базе данных."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("Подключение к базе данных закрыто.")

    def add_theme(self, subject_id: int, theme_name: str):
        """Добавление новой темы в базу данных."""
        query = """
            INSERT INTO "Темы" ("id_предмета", "название")
            VALUES (%s, %s)
            RETURNING "id_темы"
        """
        try:
            self.cursor.execute(query, (subject_id, theme_name))
            self.conn.commit()
            result = self.cursor.fetchone()[0]
            logger.info(f"✅ Тема '{theme_name}' успешно добавлена с ID: {result}")
            return result
        except psycopg2.IntegrityError as ie:
            self.conn.rollback()
            logger.error(f"❌ Ошибка добавления темы: {ie}")
            raise ValueError("Тема с таким названием уже существует.")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Ошибка добавления темы: {e}")
            raise

    def get_all_themes(self):
        query = """
            SELECT "id_темы", "название"
            FROM "Темы"
            ORDER BY "название"
        """
        try:
            self.cursor.execute(query)
            themes = self.cursor.fetchall()
            return [{"id": t[0], "name": t[1]} for t in themes]
        except Exception as e:
            logger.error(f"Ошибка получения тем: {e}")
            raise

    def add_question(self, theme_id: int, text: str, answers: str):
        query = """
            INSERT INTO "Вопросы" ("id_темы", "текст", "правильные_ответы")
            VALUES (%s, %s, %s)
            RETURNING "id_вопроса"
        """
        try:
            self.cursor.execute(query, (theme_id, text, answers))
            self.conn.commit()
            logger.info(f"✅ Вопрос '{text}' успешно добавлен к теме ID={theme_id}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Ошибка добавления вопроса: {e}")
            raise

    def get_theme_by_id(self, theme_id: int):
        """Получение темы по её ID."""
        query = """
            SELECT "id_темы" AS id, "название" AS name
            FROM "Темы"
            WHERE "id_темы" = %s
        """
        try:
            self.cursor.execute(query, (theme_id,))
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"❌ Ошибка получения темы по ID: {e}")
            raise

    def create_test(self, group_id: int, theme_id: int | None, date) -> int:
        """Создаёт тест и возвращает его ID"""
        query = """
            INSERT INTO "Тесты" ("id_группы", "id_темы", "дата")
            VALUES (%s, %s, %s)
            RETURNING "id_теста"
        """
        try:
            # Проверка существования группы
            if not self.group_exists(group_id):
                raise ValueError(f"Группа с ID {group_id} не существует")

            # Проверка существования темы, если указана
            if theme_id and not self.theme_exists(theme_id):
                raise ValueError(f"Тема с ID {theme_id} не существует")

            self.cursor.execute(query, (group_id, theme_id, date))
            test_id = self.cursor.fetchone()[0]
            self.conn.commit()
            return test_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при создании теста. Группа: {group_id}, Тема: {theme_id}. Ошибка: {str(e)}")
            raise

    def group_exists(self, group_id: int) -> bool:
        """Проверяет существование группы"""
        self.cursor.execute('SELECT 1 FROM "Группа" WHERE "id_Группы" = %s', (group_id,))
        return self.cursor.fetchone() is not None

    def theme_exists(self, theme_id: int) -> bool:
        """Проверяет существование темы"""
        self.cursor.execute('SELECT 1 FROM "Темы" WHERE "id_темы" = %s', (theme_id,))
        return self.cursor.fetchone() is not None

    def add_questions_to_test(self, test_id: int, question_ids: set[int]):
        """Добавляет вопросы к тесту"""
        if not question_ids:
            return

        query = """
            INSERT INTO "Вопросы_теста" ("id_вопроса", "id_теста")
            VALUES (%s, %s)
        """
        try:
            values = [(q_id, test_id) for q_id in question_ids]
            self.cursor.executemany(query, values)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при добавлении вопросов к тесту: {e}")
            raise

    def create_test_and_questions(self, groups, themes, questions, date):
        """Создает тест для каждой группы и темы и добавляет вопросы в таблицу 'Вопросы_теста'"""
        cursor = self.conn.cursor()
        try:
            test_ids = []
            for group_id in groups:
                for theme_id in themes:
                    # Создаем тест
                    cursor.execute("""
                        INSERT INTO "Тесты" ("id_группы", "id_темы", "дата")
                        VALUES (%s, %s, %s)
                        RETURNING "id_теста"
                    """, (group_id, theme_id, date))
                    test_id = cursor.fetchone()[0]

                    # Добавляем вопросы в тест
                    values = ', '.join([f"({q}, {test_id})" for q in questions])
                    insert_query = f"""
                        INSERT INTO "Вопросы_теста" ("id_вопроса", "id_теста") 
                        VALUES {values}
                    """
                    cursor.execute(insert_query)
                    test_ids.append(test_id)

            self.conn.commit()
            return test_ids
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Ошибка при создании теста: {e}")
            raise

    def get_group_themes(self, group_id: int) -> list:
        """Получение тем для конкретной группы"""
        query = """
        SELECT DISTINCT t.id_темы, t.название 
        FROM "Темы" t
        JOIN "Тесты" ts ON t.id_темы = ts.id_темы
        WHERE ts.id_группы = %s
        ORDER BY t.название
        """
        self.cursor.execute(query, (group_id,))
        return self.cursor.fetchall()

    def get_tests_for_group2(self, group_id: int) -> List[Tuple]:
        """Получение списка тестов для группы"""
        query = """
        SELECT 
            t.id_теста,
            t.дата,
            tm.название
        FROM Тесты t
        JOIN Темы tm ON t.id_темы = tm.id_темы
        WHERE t.id_группы = %s
        ORDER BY t.дата DESC
        """
        self.cursor.execute(query, (group_id,))
        return self.cursor.fetchall()














