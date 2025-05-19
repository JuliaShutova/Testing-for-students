import datetime
from database import Database
from datetime import datetime
from datetime import date
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

logger = logging.getLogger(__name__)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Состояния для ConversationHandler
(MAIN_MENU, VIEW_DATA, EDIT_DATA, MANAGE_SUBJECTS, MANAGE_THEMES, MANAGE_QUESTIONS,
REPORTS, ADD_SUBJECT_NAME, GET_TEST_GROUP_IDS, ADD_QUESTION_TEXT, ADD_QUESTION_ANSWERS,
GET_PERIOD_DATES, VIEW_GROUP_REPORTS, VIEW_STUDENT_RESULTS, SELECT_THEME_FOR_QUESTION,
VIEW_TEST_REPORTS, DATE_SELECTION, THEME_SELECTION,
GROUP_SELECTION, VIEW_RESULTS, SELECT_SUBJECT, SELECT_THEME,
GROUP_RESULTS_DETAIL , SELECT_SUBJECT_FOR_THEME,
VIEW_DETAILED_RESULTS,

ADD_THEME_NAME,  CONFIRM_DELETE_THEME,
    ADD_QUESTION, EDIT_QUESTION, CONFIRM_EDIT_QUESTION, DELETE_QUESTION, CONFIRM_DELETE_QUESTION,
SELECT_GROUP_FOR_TEST,
SELECT_SUBJECT_FOR_TEST,
SELECT_THEMES_FOR_TEST,
SELECT_QUESTIONS_FOR_TEST,
    ) = range(36)

class TestBot:
    def __init__(self, token: str):
        """Инициализация бота"""
        self.token = token
        self.db = None
        self.application = Application.builder().token(token).build()

        # Настройка обработчиков
        self.setup_handlers()

    def set_database(self, db: Database):
        """Установка подключения к базе данных"""
        self.db = db

    def setup_handlers(self):
        """Настройка всех обработчиков команд"""
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={

                MAIN_MENU: [
                    CallbackQueryHandler(self.view_data, pattern='^view_data$'),
                    CallbackQueryHandler(self.edit_data, pattern='^edit_data$'),
                    CallbackQueryHandler(self.reports_menu, pattern='^reports$'),
                    CallbackQueryHandler(self.create_test_start, pattern='^create_test$'),
                ],

                SELECT_GROUP_FOR_TEST: [
                    CallbackQueryHandler(self.select_group_for_test, pattern='^select_group_for_test$'),
                    CallbackQueryHandler(self.handle_selected_group_for_test, pattern=r'^test_group_\d+$'),
                    CallbackQueryHandler(self.create_test_start, pattern="^back_to_create_test$"),
                    CallbackQueryHandler(self.cancel_operation, pattern="^cancel$"),
                    CallbackQueryHandler(self.start, pattern="^back_to_main$"),
                ],

                SELECT_SUBJECT_FOR_TEST: [
                    CallbackQueryHandler(self.handle_selected_subject_for_test, pattern=r"^test_subject_\d+$"),
                    CallbackQueryHandler(self.select_group_for_test, pattern="^back_to_select_group$"),
                    CallbackQueryHandler(self.cancel_operation, pattern="^cancel$"),
                ],

                SELECT_THEMES_FOR_TEST: [
                    CallbackQueryHandler(self.handle_selected_theme_for_test, pattern=r"^test_theme_\d+$"),
                    CallbackQueryHandler(self.done_selecting_themes_for_test, pattern="^done_selecting_themes$"),
                    CallbackQueryHandler(self.select_subjects_for_test, pattern="^back_to_select_subject$"),
                    CallbackQueryHandler(self.cancel_operation, pattern="^cancel$"),
                ],

                SELECT_QUESTIONS_FOR_TEST: [
                    CallbackQueryHandler(self.handle_selected_question_for_test, pattern=r"^test_question_\d+$"),
                    CallbackQueryHandler(self.done_selecting_questions_for_test, pattern="^done_selecting_questions$"),
                    CallbackQueryHandler(self.select_themes_for_test, pattern="^back_to_select_themes$"),
                    CallbackQueryHandler(self.cancel_operation, pattern="^cancel$"),
                ],

                VIEW_DATA: [
                    # Студенты
                    CallbackQueryHandler(self.view_students_list, pattern='^view_students$'),
                    CallbackQueryHandler(self.show_student_results, pattern='^student_'),
                    CallbackQueryHandler(self.view_students_list, pattern='^back_to_students$'),

                    # Группы
                    CallbackQueryHandler(self.view_groups_list, pattern='^view_groups$'),
                    CallbackQueryHandler(self.view_groups_list, pattern='^back_to_groups$'),
                    CallbackQueryHandler(self.show_group_tests, pattern='^group_'),

                    # Тесты
                    CallbackQueryHandler(self.show_test_questions, pattern='^test_'),

                    # Специальности
                    CallbackQueryHandler(self.view_specialties_list, pattern='^view_specialties$'),
                    CallbackQueryHandler(self.show_specialty_subjects, pattern='^spec_'),
                    CallbackQueryHandler(self.view_specialties_list, pattern='^back_to_specs$'),

                    # Предметы и темы
                    CallbackQueryHandler(self.show_subject_themes, pattern='^subject_'),
                    CallbackQueryHandler(self.show_theme_tests, pattern='^theme_'),
                    CallbackQueryHandler(self.show_subject_themes, pattern='^back_to_themes$'),

                    # Навигация
                    CallbackQueryHandler(self.start, pattern='^back_to_main$'),
                    CallbackQueryHandler(self.view_data, pattern='^back_to_view$')
                ],

                EDIT_DATA: [
                    CallbackQueryHandler(self.manage_subjects, pattern="^manage_subjects$"),
                    CallbackQueryHandler(self.manage_themes, pattern="^manage_themes$"),
                    CallbackQueryHandler(self.manage_questions, pattern="^manage_questions$"),
                    CallbackQueryHandler(self.start, pattern="^back_to_main$")
                ],

                MANAGE_SUBJECTS: [
                    # CallbackQueryHandler(self.add_subject, pattern="^add_subject$"),
                    CallbackQueryHandler(self.select_subject_for_adding_theme, pattern='^add_theme$'),
                    CallbackQueryHandler(self.cancel_operation, pattern="^cancel$"),
                    CallbackQueryHandler(self.edit_data, pattern="^back_to_edit$")
                ],

                SELECT_SUBJECT: [
                    CallbackQueryHandler(self.add_subject, pattern="^add_subject$"),
                    CallbackQueryHandler(self.cancel_operation, pattern="^cancel$")
                ],


                MANAGE_THEMES: [
                    CallbackQueryHandler(self.select_subject_for_adding_theme, pattern="^add_theme$"),
                    CallbackQueryHandler(self.cancel_operation, pattern="^cancel$"),
                    CallbackQueryHandler(self.edit_data, pattern="^back_to_edit$")
                ],

                REPORTS: [

                    CallbackQueryHandler(self.show_group_results_menu, pattern='^report_test_group$'),
                    CallbackQueryHandler(self.init_period_report, pattern='^report_period$'),
                    CallbackQueryHandler(self.show_low_grades, pattern='^report_low_grades$'),
                    CallbackQueryHandler(self.start, pattern='^back_to_main$'),
                ],

                # Состояния для ввода данных
                ADD_SUBJECT_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_subject),
                    CallbackQueryHandler(self.cancel_operation, pattern="^cancel$")
                ],


                GET_TEST_GROUP_IDS: [  # Добавить для отчетов
                    CallbackQueryHandler(self.cancel_report, pattern='^cancel$')
                ],

                GET_PERIOD_DATES: [  # Добавить для отчетов
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_period_dates),
                    CallbackQueryHandler(self.cancel_report, pattern='^cancel$')
                ],

                MANAGE_QUESTIONS: [
                    CallbackQueryHandler(self.select_theme_for_adding_question, pattern='^add_question$'),
                    CallbackQueryHandler(self.edit_data, pattern='^back_to_edit$')
                ],

                EDIT_QUESTION: [
                    CallbackQueryHandler(self.handle_edit_question, pattern='^editquest_'),
                    CallbackQueryHandler(self.cancel_operation, pattern='^cancel$')
                ],

                VIEW_GROUP_REPORTS: [
                    CallbackQueryHandler(self.show_group_tests_report, pattern=r'^group_report_\d+$'),
                    CallbackQueryHandler(self.reports_menu, pattern='^back_to_reports$')
                ],

                VIEW_TEST_REPORTS: [
                    CallbackQueryHandler(self.show_test_students_results, pattern=r'^test_report_\d+$'),
                    CallbackQueryHandler(self.show_group_results_menu, pattern='^back_to_groups_report$')
                ],

                VIEW_STUDENT_RESULTS: [
                    CallbackQueryHandler(self.show_group_tests_report, pattern=r'^group_report_\d+$'),
                    CallbackQueryHandler(self.show_group_tests_report2, pattern=r'^group_report_\d+$'),
                    CallbackQueryHandler(self.show_group_results_menu, pattern='^back_to_groups_report$')
                ],

                DATE_SELECTION: [
                    CallbackQueryHandler(self.handle_date_selection, pattern='^date_'),
                    CallbackQueryHandler(self.cancel_report, pattern='^cancel$')
                ],

                GROUP_SELECTION: [
                    CallbackQueryHandler(self.handle_group_selection, pattern='^group_\d+$'),
                    CallbackQueryHandler(self.show_group_tests_report, pattern=r'^group_report_\d+$'),
                    CallbackQueryHandler(self.start, pattern='^back_to_main$'),
                ],
                GROUP_RESULTS_DETAIL: [

                    CallbackQueryHandler(self.start, pattern='^back_to_main$'),
                ],

                THEME_SELECTION: [
                    CallbackQueryHandler(self.handle_theme_selection, pattern=r'^theme_\d+_\d+$'),
                    CallbackQueryHandler(self.handle_group_selection, pattern='^back_to_groups$'),
                    CallbackQueryHandler(self.start, pattern='^back_to_main$')
                ],

                VIEW_RESULTS: [
                    CallbackQueryHandler(self.show_test_students_results, pattern=r'^test_report_\d+$'),
                    CallbackQueryHandler(self.show_theme_tests_report, pattern='^back_to_themes$'),
                    CallbackQueryHandler(self.start, pattern='^back_to_main$'),
                ],
                ADD_THEME_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_theme),
                    CallbackQueryHandler(self.cancel_operation, pattern="^cancel$")
                ],

                SELECT_SUBJECT_FOR_THEME: [
                    CallbackQueryHandler(self.handle_selected_subject_for_theme, pattern=r"^select_theme_subject_\d+$"),
                    CallbackQueryHandler(self.cancel_operation, pattern="^cancel$")
                ],


                SELECT_THEME_FOR_QUESTION: [
                    CallbackQueryHandler(self.handle_selected_theme_for_question,
                                         pattern=r"^select_question_theme_\d+$"),
                    CallbackQueryHandler(self.cancel_operation, pattern='^cancel$')
                ],
                ADD_QUESTION_TEXT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_question_text),
                    CallbackQueryHandler(self.cancel_operation, pattern='^cancel$')
                ],
                ADD_QUESTION_ANSWERS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_question_answers),
                    CallbackQueryHandler(self.cancel_operation, pattern='^cancel$')
                ],


            },
            fallbacks=[CommandHandler('start', self.start)],
        )

        self.application.add_handler(conv_handler)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Начало работы с ботом"""
        keyboard = [
            [InlineKeyboardButton("Просмотр данных", callback_data='view_data')],
            [InlineKeyboardButton("Управление данными", callback_data='edit_data')],
            [InlineKeyboardButton("Создать тест", callback_data="create_test")],
            [InlineKeyboardButton("Отчеты", callback_data='reports')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)
        else:
            await update.callback_query.edit_message_text(
                text='Выберите действие:',
                reply_markup=reply_markup
            )

        return MAIN_MENU

    async def some_method(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text("Текст")
        else:
            # Если пришло обычное сообщение
            await update.message.reply_text("Текст")

    async def create_test_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        keyboard = [
            [InlineKeyboardButton("Выбрать группу", callback_data="select_group_for_test")],
            [InlineKeyboardButton("← Назад", callback_data="back_to_main")]
        ]

        await query.edit_message_text(
            text="Создание теста:\n\nВыберите группу для теста:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_GROUP_FOR_TEST

    async def select_group_for_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        groups = self.db.get_groups2()
        if not groups:
            await query.edit_message_text("❌ Нет доступных групп.")
            return SELECT_GROUP_FOR_TEST

        keyboard = [
            [InlineKeyboardButton(group['name'], callback_data=f"test_group_{group['id']}")]
            for group in groups
        ]
        keyboard.append([InlineKeyboardButton("← Назад", callback_data="back_to_create_test")])

        await query.edit_message_text(
            "Выберите группу для теста:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_GROUP_FOR_TEST

    async def handle_selected_group_for_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        group_id = int(query.data.split("_")[2])  # test_group_123
        context.user_data["selected_group"] = group_id
        await self.select_subjects_for_test(update, context)
        return SELECT_SUBJECT_FOR_TEST

    async def select_subjects_for_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        subjects = self.db.get_all_subjects()
        if not subjects:
            await query.edit_message_text("❌ Нет доступных предметов.")
            return SELECT_SUBJECT_FOR_TEST

        keyboard = [
            [InlineKeyboardButton(subject['name'], callback_data=f"test_subject_{subject['id']}")]
            for subject in subjects
        ]
        keyboard.append([InlineKeyboardButton("← Назад", callback_data="back_to_select_group")])

        await query.edit_message_text(
            "Выберите предмет для теста:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_SUBJECT_FOR_TEST

    async def handle_selected_subject_for_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        subject_id = int(update.callback_query.data.split("_")[2])
        context.user_data["selected_subject"] = subject_id
        await self.select_themes_for_test(update, context)
        return SELECT_THEMES_FOR_TEST

    async def done_selecting_themes_for_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        selected_themes = context.user_data.get("selected_themes", set())
        if not selected_themes:
            await query.edit_message_text("⚠️ Вы не выбрали ни одной темы.")
            return SELECT_THEMES_FOR_TEST

        await self.select_questions_for_test(update, context)
        return SELECT_QUESTIONS_FOR_TEST

    async def select_themes_for_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        subject_id = context.user_data.get("selected_subject")
        themes = self.db.get_themes_by_subject(subject_id)

        if not themes:
            await query.edit_message_text("❌ У этого предмета нет тем.")
            return SELECT_THEMES_FOR_TEST

        keyboard = []
        selected_themes = context.user_data.setdefault("selected_themes", set())

        for theme in themes:
            label = f"✅ {theme['name']}" if theme["id"] in selected_themes else theme["name"]
            keyboard.append([InlineKeyboardButton(label, callback_data=f"test_theme_{theme['id']}")])

        keyboard.append([InlineKeyboardButton("Готово", callback_data="done_selecting_themes")])
        keyboard.append([InlineKeyboardButton("← Назад", callback_data="back_to_select_subject")])

        await query.edit_message_text(
            "Выберите темы для теста:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_THEMES_FOR_TEST

    async def handle_selected_theme_for_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        theme_id = int(update.callback_query.data.split("_")[2])
        selected_themes = context.user_data.setdefault("selected_themes", set())
        if theme_id in selected_themes:
            selected_themes.remove(theme_id)
        else:
            selected_themes.add(theme_id)
        return await self.select_themes_for_test(update, context)

    async def done_selecting_questions_for_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        try:
            # Получаем выбранные вопросы
            selected_questions = context.user_data.get("selected_questions", set())
            if not selected_questions:
                await query.edit_message_text("⚠️ Вы не выбрали ни одного вопроса.")
                return SELECT_QUESTIONS_FOR_TEST

            # Получаем ID группы и предмета
            selected_group_id = context.user_data.get("selected_group")
            selected_subject_id = context.user_data.get("selected_subject")

            if not selected_group_id or not selected_subject_id:
                await query.edit_message_text("❌ Не выбраны группа или предмет.")
                return SELECT_QUESTIONS_FOR_TEST

            # Получаем текущую дату (ИСПРАВЛЕННАЯ ЧАСТЬ)
            today = today = date.today()  # При импорте всего модуля
            # ИЛИ
            theme_id = next(iter(context.user_data.get("selected_themes", set())), None)

            if not theme_id:
                await query.edit_message_text("❌ Не выбрана ни одна тема")
                return SELECT_THEMES_FOR_TEST
            today = date.today()  # При импорте from datetime import date

            # Создаем тест
            test_id = self.db.create_test(
                group_id=context.user_data["selected_group"],
                theme_id=theme_id,  # Теперь всегда передаем тему
                date=today
            )

            # Добавляем вопросы к тесту
            self.db.add_questions_to_test(test_id, selected_questions)

            await query.edit_message_text(f"✅ Тест успешно создан! ID: {test_id}")

        except Exception as e:
            logger.error(f"Ошибка при создании теста: {str(e)}", exc_info=True)
            await query.edit_message_text("❌ Произошла ошибка при создании теста. Попробуйте позже.")
            return ConversationHandler.END

        finally:
            # Очищаем данные
            for key in ["selected_questions", "selected_themes", "selected_group", "selected_subject"]:
                context.user_data.pop(key, None)

        return MAIN_MENU

        #return MAIN_MENU

    async def select_questions_for_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        selected_themes = context.user_data.get("selected_themes", set())
        if not selected_themes:
            await query.edit_message_text("❌ Темы не выбраны.")
            return SELECT_THEMES_FOR_TEST

        questions = self.db.get_questions_by_themes(selected_themes)

        keyboard = []
        selected_questions = context.user_data.setdefault("selected_questions", set())

        for question in questions:
            label = f"✅ {question['text'][:40]}..." if question["id"] in selected_questions else question['text'][
                                                                                                 :50] + "..."
            keyboard.append([InlineKeyboardButton(label, callback_data=f"test_question_{question['id']}")])

        keyboard.append([InlineKeyboardButton("Завершить", callback_data="done_selecting_questions")])
        keyboard.append([InlineKeyboardButton("← Назад", callback_data="back_to_select_themes")])

        await query.edit_message_text(
            "Выберите вопросы для теста:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_QUESTIONS_FOR_TEST

    async def handle_selected_question_for_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        question_id = int(query.data.split("_")[2])  # test_question_123
        selected_questions = context.user_data.setdefault("selected_questions", set())

        if question_id in selected_questions:
            selected_questions.remove(question_id)
        else:
            selected_questions.add(question_id)

        return await self.select_questions_for_test(update, context)

    async def view_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка просмотра данных"""
        query = update.callback_query
        await query.answer()

        keyboard = [
            [InlineKeyboardButton("Студенты", callback_data='view_students')],
            [InlineKeyboardButton("Группы", callback_data='view_groups')],
            [InlineKeyboardButton("Специальности", callback_data='view_specialties')],
            [InlineKeyboardButton("Назад", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text='Что вы хотите просмотреть?',
            reply_markup=reply_markup
        )
        return VIEW_DATA

    async def view_students_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Просмотр списка студентов с кнопками"""
        query = update.callback_query
        await query.answer()

        try:
            students = self.db.get_all_students()  # Нужно реализовать метод
            if not students:
                await query.edit_message_text(text="Нет данных о студентах")
                return VIEW_DATA

            keyboard = []
            for student in students:
                student_id = student[0]
                fio = student[2]  # Структура: (id, group_id, ФИО)
                keyboard.append(
                    [InlineKeyboardButton(
                        f"{fio}",
                        callback_data=f"student_{student_id}"
                    )]
                )

            keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_view')])
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                text="👨🎓 Выберите студента:",
                reply_markup=reply_markup
            )
            return VIEW_DATA

        except Exception as e:
            logger.error(f"Ошибка при получении студентов: {e}")
            await query.edit_message_text(text="❌ Ошибка при загрузке студентов")
            return VIEW_DATA

    async def show_student_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        student_id = int(query.data.split("_")[1])

        try:
            student_info = self.db.get_student_info(student_id)
            results = self.db.get_student_results(student_id)

            if not student_info:
                await query.edit_message_text(text="Студент не найден")
                return VIEW_DATA

            fio = student_info[2]
            group_id = student_info[1]

            message = f"📊 Результаты студента:\n\n👤 {fio}\n🏫 Группа: {group_id}\n\n"

            if not results:
                message += "Пока нет результатов тестов"
            else:
                for result in results:
                    total_score = result[0]
                    grade = result[1]
                    date = result[2].strftime("%d.%m.%Y")
                    question_id = result[3]
                    answer = result[4]
                    question_score = result[5]

                    message += (
                        f"📅 {date}\n"
                        f"💯 Общий балл: {total_score}\n"
                        f"⭐ Оценка: {grade}\n"
                        f"➖➖➖➖➖➖➖➖\n"
                        f"Вопрос #{question_id}\n"
                        f"Ответ: {answer[:50]}...\n"
                        f"Балл за вопрос: {question_score}\n"
                        f"――――――――――――――――――\n"
                    )

            keyboard = [
                [InlineKeyboardButton("← Назад к списку", callback_data='back_to_students')],
                [InlineKeyboardButton("🏠 В главное меню", callback_data='back_to_main')]
            ]

            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return VIEW_DATA

        except Exception as e:
            logger.error(f"Ошибка показа результатов: {e}")
            await query.edit_message_text(text="❌ Ошибка загрузки результатов")
            return VIEW_DATA

    async def view_groups_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        try:
            groups = self.db.get_groups()
            if not groups:
                await query.edit_message_text(text="Нет данных о группах")
                return VIEW_DATA

            keyboard = []
            for group in groups:
                group_id = group[0]
                specialty_name = group[1]
                year = group[2]
                # Создаем кнопки для каждой группы
                keyboard.append(
                    [InlineKeyboardButton(
                        f"{specialty_name} ({year})",
                        callback_data=f"group_{group_id}"
                    )]
                )

            # Добавляем кнопку "Назад"
            keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_view')])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                text="📚 Выберите группу:",
                reply_markup=reply_markup
            )
            return VIEW_DATA

        except Exception as e:
            logger.error(f"Ошибка при получении групп: {e}")
            await query.edit_message_text(text="❌ Ошибка при загрузке групп")
            return VIEW_DATA

    async def show_group_tests(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        try:
            group_id = int(query.data.split("_")[1])
            logger.info(f"Запрошены тесты для группы {group_id}")  # Логируем ID группы

            tests = self.db.get_tests_for_group(group_id)
            logger.debug(f"Получены тесты из БД: {tests}")  # Логируем сырые данные

            if not tests:
                await query.edit_message_text(text="📭 Для этой группы нет активных тестов")
                return VIEW_DATA

            message = f"📋 Доступные тесты (Группа {group_id}):\n\n"
            keyboard = []

            for test in tests:
                try:
                    test_id = test[0]
                    test_date = test[1].strftime("%d.%m.%Y")  # Проверка типа даты
                    topic_name = test[2]

                    message += f"▫️ {topic_name} ({test_date})\n"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"тест {test_id}, {topic_name}",
                            callback_data=f"test_{test_id}"
                        )
                    ])
                except IndexError as e:
                    logger.error(f"Ошибка формата данных теста: {test} - {str(e)}")
                    continue

            keyboard.append([InlineKeyboardButton("← Назад к группам", callback_data='back_to_groups')])

            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return VIEW_DATA

        except Exception as e:
            logger.error(f"Критическая ошибка в show_group_tests: {str(e)}", exc_info=True)
            await query.edit_message_text(text="❌ Произошла системная ошибка")
            return VIEW_DATA

    async def view_specialties_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Просмотр списка специальностей с кнопками"""
        query = update.callback_query
        await query.answer()

        try:
            specialties = self.db.get_specialties()
            if not specialties:
                await query.edit_message_text(text="Нет данных о специальностях")
                return VIEW_DATA

            keyboard = []
            for spec in specialties:
                keyboard.append([
                    InlineKeyboardButton(
                        spec[1],  # Название специальности
                        callback_data=f"spec_{spec[0]}"  # ID специальности
                    )
                ])

            keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_view')])

            await query.edit_message_text(
                text="📚 Выберите специальность:",
                reply_markup=InlineKeyboardMarkup(keyboard))
            return VIEW_DATA

        except Exception as e:
            logger.error(f"Ошибка при получении специальностей: {e}")
            await query.edit_message_text(text="❌ Ошибка при загрузке специальностей")
            return VIEW_DATA

    async def show_specialty_subjects(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        spec_id = int(query.data.split("_")[1])
        context.user_data["current_spec_id"] = spec_id  # Сохраняем ID специальности

        try:
            subjects = self.db.get_subjects_by_specialty(spec_id)

            if not subjects:
                await query.edit_message_text(text="Для этой специальности нет предметов")
                return VIEW_DATA

            keyboard = []
            for subj in subjects:
                keyboard.append([
                    InlineKeyboardButton(
                        subj[1],  # Название предмета
                        callback_data=f"subject_{subj[0]}"  # ID предмета
                    )
                ])

            keyboard.append([
                InlineKeyboardButton("← Назад к специальностям", callback_data='back_to_specs'),
                InlineKeyboardButton("🏠 В главное меню", callback_data='back_to_main')
            ])

            await query.edit_message_text(
                text="📚 Выберите предмет:",
                reply_markup=InlineKeyboardMarkup(keyboard))
            return VIEW_DATA

        except Exception as e:
            logger.error(f"Ошибка показа предметов: {e}")
            await query.edit_message_text(text="❌ Ошибка загрузки предметов")
            return VIEW_DATA

    async def show_test_questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        test_id = int(query.data.split("_")[1])

        try:
            # Сохраняем ID группы в контексте для кнопки "Назад"
            context.user_data["current_group"] = self.db.get_group_id_by_test(test_id)

            questions = self.db.get_test_questions(test_id)

            if not questions:
                await query.edit_message_text(text="📭 В этом тесте пока нет вопросов")
                return VIEW_DATA

            message = "📝 Вопросы теста:\n\n"
            for idx, question in enumerate(questions, 1):
                message += (
                    f"{idx}. {question[1]}\n"
                    f"✅ Правильный ответ: {question[2]}\n"
                    f"――――――――――――――――――\n"
                )

            keyboard = [
                [InlineKeyboardButton("← Назад к тестам", callback_data=f'group_{context.user_data["current_group"]}')],
                [InlineKeyboardButton("🏠 В главное меню", callback_data='back_to_main')]
            ]

            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return VIEW_DATA

        except Exception as e:
            logger.error(f"Ошибка: {str(e)}", exc_info=True)
            await query.edit_message_text(text="❌ Ошибка загрузки вопросов")
            return VIEW_DATA

    async def show_subject_themes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        subject_id = int(query.data.split("_")[1])
        context.user_data["current_subject_id"] = subject_id  # Сохраняем ID предмета

        try:
            themes = self.db.get_themes_by_subject(subject_id)

            if not themes:
                await query.edit_message_text(text="Для этого предмета пока нет тем")
                return VIEW_DATA

            keyboard = []
            for theme in themes:
                keyboard.append([
                    InlineKeyboardButton(
                        theme[1],  # Название темы
                        callback_data=f"theme_{theme[0]}"  # ID темы
                    )
                ])

            keyboard.append([
                InlineKeyboardButton("← Назад к предметам",
                                     callback_data=f'spec_{context.user_data["current_spec_id"]}'),
                InlineKeyboardButton("🏠 В главное меню", callback_data='back_to_main')
            ])

            await query.edit_message_text(
                text="📚 Выберите тему:",
                reply_markup=InlineKeyboardMarkup(keyboard))
            return VIEW_DATA

        except Exception as e:
            logger.error(f"Ошибка показа тем: {e}")
            await query.edit_message_text(text="❌ Ошибка загрузки тем")
            return VIEW_DATA

    async def show_theme_tests(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        theme_id = int(query.data.split("_")[1])

        try:
            tests = self.db.get_tests_by_theme(theme_id)

            if not tests:
                await query.edit_message_text(text="Для этой темы пока нет тестов")
                return VIEW_DATA

            message = "📝 Список тестов (ID):\n\n"
            keyboard = []

            for test in tests:
                test_id = test[0]  # Получаем первый элемент кортежа (id_теста)
                keyboard.append([
                    InlineKeyboardButton(
                        f"Тест #{test_id}",
                        callback_data=f"test_{test_id}"
                    )
                ])

            keyboard.append([
                InlineKeyboardButton("← Назад к темам",
                                     callback_data=f'subject_{context.user_data["current_subject_id"]}'),
                InlineKeyboardButton("🏠 В главное меню", callback_data='back_to_main')
            ])

            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return VIEW_DATA

        except Exception as e:
            logger.error(f"Ошибка показа тестов: {e}")
            await query.edit_message_text(text="❌ Ошибка загрузки тестов")
            return VIEW_DATA

    async def edit_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Редактирование данных"""
        query = update.callback_query
        await query.answer()

        keyboard = [
            [InlineKeyboardButton("Управление предметами", callback_data='manage_subjects')],
            [InlineKeyboardButton("Управление темами", callback_data='manage_themes')],
            [InlineKeyboardButton("Управление вопросами", callback_data='manage_questions')],
            [InlineKeyboardButton("Назад", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text='Что вы хотите изменить?',
            reply_markup=reply_markup
        )
        return EDIT_DATA

    async def save_new_student(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сохранение нового студента в БД"""
        student_name = update.message.text

        try:
            # Нужно реализовать этот метод в Database
            student_id = self.db.add_student(student_name)
            await update.message.reply_text(f"Студент добавлен. ID: {student_id}")
        except Exception as e:
            logger.error(f"Ошибка при добавлении студента: {e}")
            await update.message.reply_text(f"Ошибка: {str(e)}")

        return await self.start(update, context)

    async def reports_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        keyboard = [
            [InlineKeyboardButton("Результаты теста для группы", callback_data='report_test_group')],
            [InlineKeyboardButton("Результаты за период", callback_data='report_period')],
            [InlineKeyboardButton("Список двоечников", callback_data='report_low_grades')],
            [InlineKeyboardButton("Назад", callback_data='back_to_main')]
        ]
        await update.callback_query.edit_message_text(
            text="Выберите тип отчета:",
            reply_markup=InlineKeyboardMarkup(keyboard))
        return REPORTS

    async def show_low_grades(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        try:
            low_grades = self.db.get_low_grades()
            logger.debug(f"Raw data from DB: {low_grades}")  # Проверьте логи здесь!

            if not low_grades:
                await query.edit_message_text(text="🎉 Нет студентов с оценкой 2!")
                return REPORTS

            message = "📉 Список студентов с оценкой 2:\n\n"
            for record in low_grades:
                # Проверка количества элементов в записи
                if len(record) < 4:
                    logger.error(f"Некорректная запись: {record}")
                    continue

                student_name = record[0]  # s."ФИО"
                group_id = record[1]  # g."id_Группы"
                test_id = record[2]  # t."id_теста"
                test_date = record[3]  # t."дата"

                # Форматирование даты
                try:
                    test_date_str = test_date.strftime("%d.%m.%Y") if test_date else "Нет данных"
                except AttributeError:
                    test_date_str = "Неверный формат даты"

                message += (
                    f"👤 Студент: {student_name}\n"
                    f"🏫 Группа: {group_id}\n"
                    f"📝 Тест ID: {test_id}\n"
                    f"📅 Дата теста: {test_date_str}\n"
                    f"――――――――――――――――――\n"
                )

            #keyboard = [
              #  [InlineKeyboardButton("◀️ Назад", callback_data='back_to_reports')]
            #]
            #await query.edit_message_text(text=message)
            #return REPORTS
            keyboard = [
                [InlineKeyboardButton("🏠 В главное меню", callback_data='back_to_main')]
            ]

            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return REPORTS

        except Exception as e:
            logger.error(f"Ошибка: {str(e)}", exc_info=True)
            await query.edit_message_text(text="❌ Ошибка при загрузке данных")
            return REPORTS

      # ADD SUBJECT

    async def manage_subjects(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Главное меню управления предметами."""
        keyboard = [
            [InlineKeyboardButton("Добавить новый предмет", callback_data="add_subject")],
            [InlineKeyboardButton("← Назад", callback_data='back_to_edit')]
        ]
        await update.callback_query.edit_message_text(
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MANAGE_SUBJECTS

    async def add_subject(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Запрос на ввод названия нового предмета."""
        await update.callback_query.edit_message_text(
            "Введите название нового предмета:\n(для отмены введите /cancel)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Отмена", callback_data="cancel")]])
        )
        return ADD_SUBJECT_NAME

    async def save_subject(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сохранение нового предмета в базу данных."""
        subject_name = update.message.text.strip()
        if not subject_name:
            await update.message.reply_text("❌ Название предмета не может быть пустым.")
            return ADD_SUBJECT_NAME

        try:
            subject_id = self.db.add_subject(subject_name)
            await update.message.reply_text(f"✅ Предмет '{subject_name}' успешно добавлен! (ID: {subject_id})")
        except Exception as e:
            logger.error(f"Ошибка добавления предмета: {str(e)}")
            await update.message.reply_text("❌ Ошибка при добавлении предмета.")

        return await self.manage_subjects(update, context)

    async def cancel_operation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена операции."""
        await update.callback_query.edit_message_text("❌ Операция отменена.")
        return await self.manage_subjects(update, context)

    # ADD THEMES

    async def manage_themes(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Меню управления темами"""
        query = update.callback_query
        await query.answer()

        keyboard = [
            [InlineKeyboardButton("Добавить тему", callback_data='add_theme')],
            [InlineKeyboardButton("← Назад", callback_data='back_to_edit')]
        ]

        await query.edit_message_text(
            text="Управление темами:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MANAGE_THEMES

    async def add_theme(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "Введите название новой темы:\n(для отмены введите /cancel)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Отмена", callback_data="cancel")]])
        )
        return ADD_THEME_NAME

    async def save_theme(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        theme_name = update.message.text.strip()
        subject_id = context.user_data.get("current_subject_id")

        if not subject_id:
            await update.message.reply_text("❌ Не выбран предмет для добавления темы.")
            return ADD_THEME_NAME

        if not theme_name:
            await update.message.reply_text("❌ Название темы не может быть пустым.")
            return ADD_THEME_NAME

        try:
            self.db.add_theme(subject_id, theme_name)
            await update.message.reply_text(f"✅ Тема '{theme_name}' успешно добавлена!")
        except Exception as e:
            logger.error(f"Ошибка добавления темы: {str(e)}")
            await update.message.reply_text("❌ Ошибка при добавлении темы.")

        return await self.manage_themes(update, context)

    async def select_subject_for_adding_theme(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Позволяет пользователю выбрать предмет для добавления темы."""
        query = update.callback_query
        await query.answer()

        subjects = self.db.get_all_subjects()
        if not subjects:
            await query.edit_message_text("❌ Нет доступных предметов.")
            return MANAGE_THEMES

        keyboard = [
            [InlineKeyboardButton(subject['name'], callback_data=f"select_theme_subject_{subject['id']}")]
            for subject in subjects
        ]
        keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])

        await query.edit_message_text(
            "Выберите предмет для добавления темы:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_SUBJECT_FOR_THEME

    async def handle_selected_subject_for_theme(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора предмета для добавления темы."""
        query = update.callback_query
        await query.answer()

        subject_id = int(query.data.split("_")[3])  # select_theme_subject_123
        context.user_data["current_subject_id"] = subject_id

        await query.edit_message_text("Введите название новой темы:")
        return ADD_THEME_NAME

    # ADD questions

    async def manage_questions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Меню управления вопросами"""
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                text="Управление вопросами:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Добавить вопрос", callback_data='add_question')],
                    [InlineKeyboardButton("← Назад", callback_data='back_to_edit')]
                ])
            )
        else:
            # Если вызван через message (например, после ввода текста)
            await update.message.reply_text(
                text="Управление вопросами:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Добавить вопрос", callback_data='add_question')],
                    [InlineKeyboardButton("← Назад", callback_data='back_to_edit')]
                ])
            )

        return MANAGE_QUESTIONS

    async def save_question_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сохранение текста вопроса"""
        context.user_data["new_question"] = {
            "text": update.message.text
        }
        await update.message.reply_text(
            "Введите правильные ответы (через запятую):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Отмена", callback_data='cancel')]])
        )
        return EDIT_DATA

    async def save_question_full(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сохранение полного вопроса"""
        answers = update.message.text
        question_data = context.user_data["new_question"]

        try:
            self.db.add_question(
                theme_id=context.user_data["current_theme_id"],
                text=question_data["text"],
                answers=answers
            )
            await update.message.reply_text("✅ Вопрос успешно добавлен!")
        except Exception as e:
            logger.error(f"Ошибка добавления вопроса: {str(e)}")
            await update.message.reply_text("❌ Ошибка при добавлении вопроса")

        return await self.manage_questions(update, context)

    async def handle_edit_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора вопроса"""
        query = update.callback_query
        await query.answer()

        question_id = int(query.data.split("_")[1])
        context.user_data["current_question_id"] = question_id

        await query.edit_message_text(text="Введите новый текст вопроса:")
        return CONFIRM_EDIT_QUESTION

    async def select_theme_for_adding_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Позволяет выбрать тему перед добавлением вопроса."""
        query = update.callback_query
        await query.answer()

        themes = self.db.get_all_themes()  # ← должен быть реализован
        if not themes:
            await query.edit_message_text("❌ Нет доступных тем.")
            return MANAGE_QUESTIONS

        keyboard = [
            [InlineKeyboardButton(theme['name'], callback_data=f"select_question_theme_{theme['id']}")]
            for theme in themes
        ]
        keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])

        await query.edit_message_text(
            "Выберите тему для добавления вопроса:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_THEME_FOR_QUESTION

    async def handle_selected_theme_for_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сохраняет выбранную тему и переходит к вводу текста вопроса."""
        query = update.callback_query
        await query.answer()

        theme_id = int(query.data.split("_")[3])  # select_question_theme_123
        context.user_data["current_theme_id"] = theme_id

        await query.edit_message_text("Введите текст вопроса:")
        return ADD_QUESTION_TEXT

    async def save_question_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сохраняет текст вопроса и запрашивает правильные ответы."""
        question_text = update.message.text.strip()
        if not question_text:
            await update.message.reply_text("❌ Текст вопроса не может быть пустым.")
            return ADD_QUESTION_TEXT

        context.user_data["new_question"] = {
            "text": question_text
        }

        await update.message.reply_text("Введите правильные ответы (через запятую):")
        return ADD_QUESTION_ANSWERS

    async def save_question_answers(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Сохраняет правильные ответы и добавляет вопрос в БД."""
        answers = update.message.text.strip()
        question_data = context.user_data.get("new_question", {})
        theme_id = context.user_data.get("current_theme_id")

        if not answers:
            await update.message.reply_text("❌ Правильные ответы не могут быть пустыми.")
            return ADD_QUESTION_ANSWERS

        try:
            self.db.add_question(
                theme_id=theme_id,
                text=question_data["text"],
                answers=answers
            )
            await update.message.reply_text("✅ Вопрос успешно добавлен!")
        except Exception as e:
            logger.error(f"Ошибка добавления вопроса: {str(e)}")
            await update.message.reply_text("❌ Ошибка при добавлении вопроса.")

        return await self.manage_questions(update, context)

    async def show_group_results_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Меню выбора группы для просмотра результатов"""
        query = update.callback_query
        await query.answer()

        try:
            groups = self.db.get_groups()
            keyboard = [
                [InlineKeyboardButton(f"{g[1]} ({g[2]})", callback_data=f'group_report_{g[0]}')]
                for g in groups
            ]
            keyboard.append([InlineKeyboardButton("← Назад", callback_data='back_to_reports')])

            await query.edit_message_text(
                text="📋 Выберите группу:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return VIEW_GROUP_REPORTS

        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            await query.edit_message_text(text="❌ Ошибка загрузки групп")
            return REPORTS

    async def show_group_tests_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показать тесты выбранной группы"""
        query = update.callback_query
        await query.answer()

        try:
            group_id = int(query.data.split('_')[2])
            context.user_data['current_group'] = group_id

            tests = self.db.get_tests_for_group2(group_id)

            if not tests:
                await query.edit_message_text(text="📭 В этой группе пока нет тестов")
                return VIEW_GROUP_REPORTS

            message = f"📋 Тесты группы {group_id}:\n\n"
            keyboard = []

            for test in tests:
                test_id = test[0]
                test_date = test[1].strftime("%d.%m.%Y")
                topic = test[2]

                keyboard.append([
                    InlineKeyboardButton(
                        f"{topic} ({test_date})",
                        callback_data=f"test_report_{test_id}"
                    )
                ])

            keyboard.append([InlineKeyboardButton("← Назад к группам", callback_data='back_to_groups_report')])

            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return VIEW_TEST_REPORTS

        except Exception as e:  # Добавлен блок except
            logger.error(f"Ошибка в show_group_tests_report: {str(e)}", exc_info=True)
            await query.edit_message_text(text="❌ Ошибка загрузки тестов группы")
            return VIEW_GROUP_REPORTS

    async def show_group_tests_report2(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показать тесты выбранной группы"""
        query = update.callback_query
        await query.answer()

        try:
            group_id = int(query.data.split('_')[2])  # Извлекаем ID группы
            context.user_data['current_group'] = group_id
            logger.info(f"Загрузка тестов для группы {group_id}")

            tests = self.db.get_tests_for_group2(group_id)

            if not tests:
                await query.edit_message_text(text="📭 В этой группе пока нет тестов")
                return VIEW_GROUP_REPORTS

            # Формируем сообщение
            message = f"📋 Тесты группы {group_id}:\n\n"
            keyboard = []

            for test in tests:
                test_id = test[0]
                test_date = test[1].strftime("%d.%m.%Y")
                topic = test[2]

                keyboard.append([
                    InlineKeyboardButton(
                        f"{topic} ({test_date})",
                        callback_data=f"test_report_{test_id}"
                    )
                ])

            keyboard.append([InlineKeyboardButton("← Назад к группам", callback_data='back_to_groups_report')])

            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return VIEW_TEST_REPORTS

        except Exception as e:
            logger.error(f"Ошибка загрузки тестов: {str(e)}", exc_info=True)
            await query.edit_message_text(text="❌ Ошибка загрузки тестов группы")
            return VIEW_GROUP_REPORTS

    async def show_test_students_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показать результаты студентов по выбранному тесту"""
        query = update.callback_query
        await query.answer()

        try:
            test_id = int(query.data.split('_')[2])
            group_id = context.user_data['current_group']

            results = self.db.get_students_results_for_test(group_id, test_id)
            test_info = self.db.get_test_info(test_id)

            message = (
                f"📊 Результаты теста:\n"
                f"Группа: {group_id}\n"
                f"Тема: {test_info[1]}\n"
                f"Дата: {test_info[2].strftime('%d.%m.%Y')}\n\n"
            )

            if not results:
                message += "Нет результатов"
            else:
                message += "Студент            Балл  \n"
                message += "――――――――――――――――――――――――――――――――\n"
                for student in results:
                    message += f"{student[0]:<18} {student[1]:<5} \n"

            keyboard = [
                [InlineKeyboardButton("← К списку тестов", callback_data=f'group_report_{group_id}')],
                [InlineKeyboardButton("🏠 В главное меню", callback_data='back_to_main')]
            ]

            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return VIEW_STUDENT_RESULTS

        except Exception as e:  # Добавлен блок except
            logger.error(f"Ошибка: {str(e)}", exc_info=True)
            await query.edit_message_text(text="❌ Ошибка загрузки результатов")
            return VIEW_TEST_REPORTS

    async def init_period_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Инициализация отчета по периоду"""
        query = update.callback_query
        await query.answer()

        try:
            # Сбрасываем предыдущие данные
            context.user_data.clear()

            # Запрашиваем период
            await query.edit_message_text(
                text="📅 Введите период в формате: ДД.ММ.ГГГГ ДД.ММ.ГГГГ\nПример: 01.03.2024 15.03.2024",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Отмена", callback_data="cancel_report")]])
            )
            return GET_PERIOD_DATES

        except Exception as e:
            logger.error(f"Ошибка инициализации отчета: {str(e)}")
            await query.edit_message_text(text="❌ Ошибка при запуске отчета")
            return REPORTS

    async def handle_period_dates(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка ввода периода и показ списка дат"""
        try:
            start_date_str, end_date_str = update.message.text.split()
            start_date = datetime.strptime(start_date_str, "%d.%m.%Y").date()
            end_date = datetime.strptime(end_date_str, "%d.%m.%Y").date()

            # Сохраняем период в контексте
            context.user_data["period"] = (start_date, end_date)

            # Получаем уникальные даты тестов
            dates = self.db.get_test_dates_in_period(start_date, end_date)

            if not dates:
                await update.message.reply_text("📭 Нет тестов за указанный период")
                return REPORTS

            # Формируем кнопки с датами
            keyboard = [
                [InlineKeyboardButton(
                    date.strftime("%d.%m.%Y"),
                    callback_data=f"date_{date.strftime('%Y-%m-%d')}"
                )] for date in dates
            ]
            keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='cancel')])

            await update.message.reply_text(
                "📅 Выберите дату тестирования:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return DATE_SELECTION

        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            await update.message.reply_text("❌ Ошибка при обработке периода")
            return REPORTS

    async def handle_date_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора даты и показ групп"""
        query = update.callback_query
        await query.answer()

        try:
            selected_date = datetime.strptime(query.data.split('_')[1], "%Y-%m-%d").date()
            context.user_data["selected_date"] = selected_date

            # Получаем группы для выбранной даты
            groups = self.db.get_groups_for_date(selected_date)

            keyboard = [
                [InlineKeyboardButton(
                    f"Группа {group_id}",
                    callback_data=f"group_{group_id}"
                )] for group_id in groups
            ]
            keyboard.append([InlineKeyboardButton("↩️ Назад к датам", callback_data='back_to_dates')])

            await query.edit_message_text(
                f"🏫 Выберите группу ({selected_date.strftime('%d.%m.%Y')}):",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return GROUP_SELECTION

        except Exception as e:
            logger.error(f"Ошибка выбора даты: {str(e)}")
            await query.edit_message_text(text="❌ Ошибка при загрузке групп")
            return DATE_SELECTION

    async def handle_group_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Обработка выбора группы и показ списка тем"""
        query = update.callback_query
        await query.answer()

        try:
            group_id = int(query.data.split('_')[1])
            context.user_data['current_group'] = group_id
            logger.info(f"Выбрана группа ID: {group_id}")

            # Получаем темы для группы
            themes = self.db.get_group_themes(group_id)
            logger.debug(f"Получены темы: {themes}")

            if not themes:
                await query.edit_message_text(text="📭 В этой группе нет доступных тем")
                return GROUP_SELECTION

            # Формируем кнопки с темами
            keyboard = []
            for theme in themes:
                # Обращаемся к элементам кортежа по индексу
                # theme[0] - id темы, theme[1] - название темы
                keyboard.append([
                    InlineKeyboardButton(
                        theme[1],  # Название темы
                        callback_data=f"theme_{theme[0]}_{group_id}"  # theme_id и group_id
                    )
                ])

            keyboard.append([InlineKeyboardButton("↩️ Назад к группам", callback_data='back_to_groups')])

            await query.edit_message_text(
                text="📚 Выберите тему тестирования:",
                reply_markup=InlineKeyboardMarkup(keyboard))
            return THEME_SELECTION

        except Exception as e:
            logger.error(f"Ошибка загрузки тем: {str(e)}", exc_info=True)
            await query.edit_message_text(text="❌ Ошибка при загрузке тем")
            return GROUP_SELECTION

    async def handle_theme_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показ результатов по выбранной теме"""
        query = update.callback_query
        await query.answer()

        try:
            # 1. Получаем данные из callback
            parts = query.data.split('_')
            if len(parts) < 3:
                raise ValueError("Неверный формат callback_data")

            theme_id = int(parts[1])
            group_id = int(parts[2])

            # 2. Сохраняем group_id в контексте
            context.user_data['current_group'] = group_id
            logger.info(f"Загрузка результатов для темы {theme_id} группы {group_id}")

            # 3. Получаем данные из БД
            results = self.db.get_theme_results(group_id, theme_id)
            theme_info = self.db.get_theme_info(theme_id)

            if not theme_info:
                raise ValueError(f"Тема с ID {theme_id} не найдена")

            # 4. Формируем сообщение
            theme_name = theme_info[1]  # Название темы - второй элемент кортежа
            message = (
                f"📊 Результаты группы {group_id}\n"
                f"📚 Тема: {theme_name}\n"
                f"═══════════════════════════════\n"
            )

            if not results:
                message += "\nℹ️ Нет результатов по данной теме"
            else:
                message += "Студент            Балл  Оценка\n"
                message += "―――――――――――――――――――――――――――――――\n"
                for student in results:
                    # Предполагаем структуру: (ФИО, балл, оценка)
                    message += f"{student[0]:<18} {student[1]:<6} {student[2]}\n"

            # 5. Создаем клавиатуру
            keyboard = [
                [InlineKeyboardButton("↩️ Назад к темам", callback_data=f'group_{group_id}')],
                [InlineKeyboardButton("🏠 В меню", callback_data='back_to_main')]
            ]

            # 6. Отправляем сообщение
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard))

            return VIEW_RESULTS

        except ValueError as ve:
            logger.error(f"Ошибка данных: {str(ve)}")
            await query.edit_message_text(text=f"❌ {str(ve)}")
            return THEME_SELECTION
        except Exception as e:
            logger.error(f"Ошибка загрузки результатов: {str(e)}", exc_info=True)
            await query.edit_message_text(text="❌ Ошибка при загрузке данных")
            return THEME_SELECTION

    async def show_group_themes_report2(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показать темы выбранной группы"""
        query = update.callback_query
        await query.answer()

        try:
            # Исправлено: берем второй элемент вместо третьего
            group_id = int(query.data.split('_')[1])  # Было [2], теперь [1]
            context.user_data['current_group'] = group_id

            # Логируем полученный group_id
            logger.info(f"Выбрана группа: {group_id}")

            themes = self.db.get_themes_for_group(group_id)

            # Логируем результат запроса
            logger.debug(f"Получены темы: {themes}")

            if not themes:
                await query.edit_message_text(text="📭 В этой группе пока нет тем")
                return VIEW_GROUP_REPORTS

            message = f"📚 Темы группы {group_id}:\n\n"
            keyboard = []

            for theme in themes:
                theme_id = theme[0]
                theme_name = theme[1]
                keyboard.append([
                    InlineKeyboardButton(
                        theme_name,
                        callback_data=f"theme_{theme_id}_{group_id}"  # Добавляем group_id в callback
                    )
                ])

            keyboard.append([InlineKeyboardButton("← Назад к группам", callback_data='back_to_groups')])

            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard))
            return THEME_SELECTION

        except IndexError as ie:
            logger.error(f"Ошибка формата callback_data: {query.data} | {str(ie)}")
            await query.edit_message_text(text="❌ Ошибка в данных запроса")
            return REPORTS
        except Exception as e:
            logger.error(f"Ошибка загрузки тем: {str(e)}", exc_info=True)
            await query.edit_message_text(text="❌ Ошибка загрузки тем группы")
            return VIEW_GROUP_REPORTS

    async def show_group_themes_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показать темы выбранной группы"""
        query = update.callback_query
        await query.answer()

        try:
            # Получаем group_id из callback_data (group_123)
            group_id = int(query.data.split('_')[1])
            context.user_data['current_group'] = group_id
            logger.info(f"Обработка группы ID: {group_id}")

            # Получаем темы для группы
            themes = self.db.get_themes_for_group(group_id)
            logger.debug(f"Получены темы: {themes}")

            if not themes:
                await query.edit_message_text(text="📭 В этой группе пока нет тем")
                return VIEW_GROUP_REPORTS

            # Формируем кнопки
            keyboard = [
                [InlineKeyboardButton(
                    theme[1],  # Название темы
                    callback_data=f"theme_{theme[0]}_{group_id}"  # theme_id и group_id
                )] for theme in themes
            ]
            keyboard.append([InlineKeyboardButton("← Назад к группам", callback_data='back_to_groups')])

            await query.edit_message_text(
                text=f"📚 Темы группы {group_id}:",
                reply_markup=InlineKeyboardMarkup(keyboard))
            return THEME_SELECTION

        except Exception as e:
            logger.error(f"Ошибка в show_group_themes_report: {str(e)}", exc_info=True)
            await query.edit_message_text(text="❌ Ошибка загрузки тем группы")
            return REPORTS

    async def show_theme_tests_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Показать тесты по выбранной теме"""
        query = update.callback_query
        await query.answer()

        try:
            # Получаем theme_id и group_id из callback_data (theme_123_456)
            parts = query.data.split('_')
            theme_id = int(parts[1])
            group_id = int(parts[2])
            context.user_data['current_group'] = group_id

            logger.info(f"Загрузка тестов для темы {theme_id} группы {group_id}")

            tests = self.db.get_tests_for_theme(group_id, theme_id)
            if not tests:
                await query.edit_message_text(text="📭 По этой теме пока нет тестов")
                return THEME_SELECTION

            # Формируем сообщение
            message = f"📋 Тесты группы {group_id}:\n\n"
            keyboard = [
                [InlineKeyboardButton(
                    f"{test[2]} ({test[1].strftime('%d.%m.%Y')})",  # Название и дата
                    callback_data=f"test_report_{test[0]}"  # test_id
                )] for test in tests
            ]

            keyboard.append([
                InlineKeyboardButton("← Назад к темам", callback_data=f'group_{group_id}'),
                InlineKeyboardButton("🏠 В главное меню", callback_data='back_to_main')
            ])

            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard))
            return VIEW_TEST_REPORTS

        except Exception as e:
            logger.error(f"Ошибка в show_theme_tests_report: {str(e)}", exc_info=True)
            await query.edit_message_text(text="❌ Ошибка загрузки тестов")
            return REPORTS

    async def cancel_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Отмена формирования отчёта и возврат в меню"""
        query = update.callback_query
        await query.answer()

        # Удаляем временные данные (если есть)
        context.user_data.pop("report_params", None)

        # Отправляем сообщение об отмене
        await query.edit_message_text("❌ Формирование отчёта отменено")

        # Возвращаемся в меню отчётов
        return await self.reports_menu(update, context)

# замеры по времени
    # @measure_time(repeats=1)
    # def delete_until_200_remain(table):
    #     cur.execute(f"""
    #         DELETE FROM {table}
    #         WHERE {table}.patient_id IN (
    #             SELECT patient_id FROM {table}
    #             ORDER BY patient_id
    #             OFFSET 200
    #         )
    #     """)
    #     conn.commit()
    #
    # @measure_time(repeats=1)
    # def vacuum_if_only_200_left(table):
    #     cur.execute(f"SELECT COUNT(*) FROM {table}")
    #     count = cur.fetchone()[0]
    #     if count == 200:
    #         print(f"В таблице {table} осталось ровно 200 строк. Выполняем VACUUM.")
    #         self.conn = psycopg2.connect(
    #             dbname="postgres",
    #             user="postgres",
    #             password="123",
    #             host="localhost",
    #             port="5432",
    #         )
    #         conn_vacuum.autocommit = True
    #         vacuum_cur = conn_vacuum.cursor()
    #         vacuum_cur.execute("VACUUM")
    #         vacuum_cur.close()
    #         conn_vacuum.close()
    #     else:
    #         print(f"В таблице {table} осталось {count} строк. Сжатие не выполнено.")
    #     conn.commit()

    def run(self):
        """Запуск бота"""
        try:
            logger.info("🤖 Бот запускается...")
            self.application.run_polling()
        except Exception as e:
            logger.critical(f"Ошибка запуска бота: {e}")

if __name__ == "__main__":
    db = Database()
    bot = TestBot("8197718248:AAEBQe7pewSOzaKMaUxeJzPAgzVwvshnnaI")
    bot.set_database(db)
    bot.run()
