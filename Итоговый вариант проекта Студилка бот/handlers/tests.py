# handlers/tests.py

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile

import os
from config.bot_config import dp
from handlers.import_results import *
from states.user_states import UserState
from datetime import datetime
from data_storage import user_results, user_data_manager
from handlers.import_results import load_variant_data

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Путь к корневой директории проекта
BASE_DIR: Path = Path(__file__).resolve().parent.parent


@dp.callback_query(lambda c: c.data.startswith("start_test_"))
async def start_test(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        data = callback.data.replace("start_test_", "")
        subject, year, variant_num = data.split("_")
        
        # Для внутренней обработки используем "Демоверсия", но пользователю показываем "Вариант" для математики 2024
        internal_variant = f"Демоверсия {variant_num}"
        display_variant = f"Вариант {variant_num}" if subject == "math" and year == "2024" else internal_variant

        await state.set_state(UserState.taking_test)
        await state.update_data(
            current_question=1,
            correct_answers=0,
            subject=subject,
            year=year,
            variant=internal_variant,
            display_variant=display_variant,
            answered_questions=set(),
            user_id=callback.from_user.id
        )

        image_path = get_task_image_path(subject, year, internal_variant, 1)

        if image_path:
            await callback.message.answer(f"Отлично, начинаем {display_variant}! 🚀")
            builder = InlineKeyboardBuilder()
            builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            builder.adjust(1)

            photo = FSInputFile(image_path)
            await callback.message.answer_photo(
                photo=photo,
                caption="Введите ответ МАЛЕНЬКИМИ БУКВАМИ (нижний регистр)",
                reply_markup=builder.as_markup()
            )

            await callback.message.delete()
            logging.info(f"Тест по {subject} начат для пользователя {callback.from_user.id}.")
        else:
            await callback.message.answer("❌ Ошибка: Задание не найдено")
            logging.error(f"Задание не найдено для {subject}, {year}, {variant_num}")

    except Exception as e:
        logging.error(f"Error in start_test: {e}")
        await callback.message.answer("Произошла ошибка при запуске теста")

def get_task_image_path(subject: str, year: str, variant: str, task_number: int) -> str | None:
    try:
        # Приводим к нужному формату: "Демоверсия 1" -> "demo 1", "Вариант 1" -> "variant 1"
        variant_key = variant.lower()
        variant_key = variant_key.replace("демоверсия ", "demo ").replace("вариант ", "variant ")
        base_path = BASE_DIR / "assets" / "test_images" / subject / year / variant_key / "tasks"
        
        logging.info(f"Поиск изображения: subject={subject}, year={year}, variant={variant}, variant_key={variant_key}")
        logging.info(f"Путь к директории заданий: {base_path}")

        if not base_path.exists():
            logging.error(f"Directory does not exist: {base_path}")
            return None

        # Формат имени файла зависит от варианта
        file_suffix = "demo1" if "demo" in variant_key else "variant1"
        logging.info(f"Используемый суффикс файла: {file_suffix}")

        # Проверяем PNG
        png_path = base_path / f"task{task_number}_{file_suffix}.png"
        logging.info(f"Проверка пути к PNG: {png_path}, существует: {png_path.exists()}")
        if png_path.exists():
            return str(png_path)

        # Проверяем JPG
        jpg_path = base_path / f"task{task_number}_{file_suffix}.jpg"
        logging.info(f"Проверка пути к JPG: {jpg_path}, существует: {jpg_path.exists()}")
        if jpg_path.exists():
            return str(jpg_path)

        # Попробуем найти файл по другим шаблонам
        possible_names = [
            f"task{task_number}_demo1.png",
            f"task{task_number}_demo1.jpg",
            f"task{task_number}_variant1.png",
            f"task{task_number}_variant1.jpg",
            f"task{task_number}.png",
            f"task{task_number}.jpg"
        ]
        
        for name in possible_names:
            test_path = base_path / name
            logging.info(f"Проверка альтернативного имени: {test_path}, существует: {test_path.exists()}")
            if test_path.exists():
                logging.info(f"Найден файл по альтернативному имени: {test_path}")
                return str(test_path)
        
        # Показываем все файлы в директории для отладки
        try:
            files_in_dir = list(base_path.glob('*.*'))
            logging.info(f"Файлы в директории {base_path}: {[f.name for f in files_in_dir]}")
        except Exception as e:
            logging.error(f"Ошибка при попытке просмотра файлов в директории: {e}")
        
        logging.error(f"Изображение для задания {task_number} не найдено в {base_path}")
        return None
    except Exception as e:
        logging.error(f"Error in get_task_image_path: {e}", exc_info=True)
        return None

@dp.message()
async def process_test_answer(message: types.Message, state: FSMContext):
    try:
        if await state.get_state() == UserState.taking_test:
            data = await state.get_data()
            current_question = data.get("current_question", 1)
            answered_questions = data.get("answered_questions", set())
            subject = data.get("subject")
            year = data.get("year")

            # --- math подпункты ---
            if subject == "math" and isinstance(current_question, tuple):
                qnum, sub = current_question
                if (qnum, sub) in answered_questions:
                    await message.answer("⚠️ Вы уже ответили на этот подпункт. Используйте кнопки навигации ниже.")
                    return
                builder = InlineKeyboardBuilder()
                variant_data = load_variant_data(subject, year)
                is_last = (qnum == 19 and sub == 'c')
                if is_last:
                    builder.button(text="Посмотреть результаты", callback_data="end_test")
                    await state.update_data(full_complete=True)
                else:
                    next_question = qnum + 1 if sub == list(variant_data[qnum].keys())[-1] else qnum
                    builder.button(text="▶️ Следующее задание", callback_data=f"next_task_{next_question}")
                    builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
                builder.adjust(1)
                user_answer = message.text.lower().strip()
                answered_questions.add((qnum, sub))
                await state.update_data(answered_questions=answered_questions)
                answer_data = variant_data[qnum][sub]
                correct_answer = answer_data["correct"]
                is_correct = user_answer == correct_answer
                await send_answer(is_correct, correct_answer, answer_data["explanation"], message, builder, year, subject)
                if is_correct:
                    await state.update_data(correct_answers=data.get("correct_answers", 0) + 1)
                return

            # --- обычные задания ---
            if current_question in answered_questions:
                await message.answer("⚠️ Вы уже ответили на этот вопрос. Используйте кнопки навигации ниже.")
                return

            builder = InlineKeyboardBuilder()
            is_last = (subject == "rus" and current_question == 26) or (subject == "math" and current_question == 19)
            if is_last:
                builder.button(text="Посмотреть результаты", callback_data="end_test")
                await state.update_data(full_complete=True)
            else:
                next_question = current_question + 1
                builder.button(text="▶️ Следующее задание", callback_data=f"next_task_{next_question}")
                builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            builder.adjust(1)

            user_answer = message.text.lower().strip()
            answered_questions.add(current_question)
            await state.update_data(answered_questions=answered_questions)

            variant_data = load_variant_data(subject, year)

            if current_question in variant_data:
                answer_data = variant_data[current_question]
                if 'correct' not in answer_data:
                    return
                correct_answer = answer_data["correct"]

                if answer_data["type"] == "numbers":
                    user_answer = "".join(user_answer.split())
                    is_correct = user_answer == correct_answer
                else:
                    is_correct = user_answer == correct_answer

                await send_answer(is_correct, correct_answer, answer_data["explanation"], message, builder, year, subject)

                if is_correct:
                    await state.update_data(correct_answers=data.get("correct_answers", 0) + 1)
            else:
                await message.answer("❌ Ошибка: Вопрос не найден.")
    except Exception as e:
        await message.answer("Произошла ошибка при обработке ответа. Пожалуйста, попробуйте еще раз.")

async def send_answer(
    is_correct: bool,
    correct_answer: str,
    explanation: str,
    message,
    builder,
    year: str,
    subject: str
):
    from pathlib import Path
    if subject == "math":
        BASE_DIR = Path(__file__).resolve().parent.parent
        photo_path = BASE_DIR / f"assets/test_images/math/{year}/demo 1/explanations/{explanation}"
        caption = (
            f"{'✅ Верно!' if is_correct else '❌ Неверно.'}\n"
            f"Правильный ответ: {correct_answer}\n"
            f"Смотрите решение ниже:"
        )
        try:
            await message.answer_photo(
                FSInputFile(str(photo_path)),
                caption=caption,
                reply_markup=builder.as_markup()
            )
        except Exception:
            await message.answer("⚠️ Не удалось отправить фото решения.")
    else:
        caption = (
            f"{'✅ Верно!' if is_correct else '❌ Неверно.'}\n"
            f"Правильный ответ: {correct_answer}\n"
            f"Объяснение: {explanation}"
        )
        await message.answer(caption, reply_markup=builder.as_markup())

@dp.callback_query(lambda c: c.data.startswith("math_subtask_"))
async def show_math_subtask(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        _, _, qnum, sub = callback.data.split("_")
        qnum = int(qnum)
        data = await state.get_data()
        subject = data.get("subject")
        year = data.get("year")
        internal_variant = data.get("variant")
        
        # Получаем путь к изображению
        image_path = get_task_image_path(subject, year, internal_variant, qnum)
        
        # Проверка существования файла
        if not image_path:
            logging.error(f"Не удалось найти изображение для задания {qnum} (подпункт {sub})")
            builder = InlineKeyboardBuilder()
            builder.button(text="▶️ Перейти к следующему", callback_data=f"next_task_{qnum+1}")
            builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            builder.adjust(1)
            await callback.message.answer(
                f"⚠️ Извините, изображение для задания {qnum} (подпункт {sub}) не найдено.\n"
                "Вы можете перейти к следующему заданию или завершить тест.",
                reply_markup=builder.as_markup()
            )
            return
            
        # Проверка размера файла
        file_size = Path(image_path).stat().st_size
        if file_size == 0:
            logging.error(f"Файл {image_path} пустой (0 байт). Невозможно отправить.")
            builder = InlineKeyboardBuilder()
            builder.button(text="▶️ Перейти к следующему", callback_data=f"next_task_{qnum+1}")
            builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            builder.adjust(1)
            await callback.message.answer(
                f"⚠️ Извините, изображение для задания {qnum} (подпункт {sub}) повреждено.\n"
                "Вы можете перейти к следующему заданию или завершить тест.",
                reply_markup=builder.as_markup()
            )
            return
        
        # Получаем данные варианта
        variant_data = load_variant_data(subject, year)
        if not variant_data or qnum not in variant_data or sub not in variant_data[qnum]:
            logging.error(f"Данные для задания {qnum} (подпункт {sub}) не найдены")
            builder = InlineKeyboardBuilder()
            builder.button(text="▶️ Перейти к следующему", callback_data=f"next_task_{qnum+1}")
            builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            builder.adjust(1)
            await callback.message.answer(
                f"⚠️ Извините, данные для задания {qnum} (подпункт {sub}) не найдены.\n"
                "Вы можете перейти к следующему заданию или завершить тест.",
                reply_markup=builder.as_markup()
            )
            return
            
        task_data = variant_data.get(qnum, {})
        sub_data = task_data.get(sub, {})
        options_builder = InlineKeyboardBuilder()
        for opt in sub_data.get("options", []):
            options_builder.button(
                text=opt,
                callback_data=f"answer_option_{qnum}_{sub}_{opt}"
            )
        options_builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
        options_builder.adjust(1)
        
        photo = FSInputFile(image_path)
        await callback.message.answer_photo(
        photo=photo,
        caption=sub_data.get("hint", f"Пункт {sub} — выберите ответ"),
        reply_markup=options_builder.as_markup()
        )
        await state.update_data(current_question=(qnum, sub))
        try:
            await callback.message.delete()
        except Exception as e:
            logging.error(f"Ошибка при отправке изображения для задания {qnum} (подпункт {sub}): {e}")
            builder = InlineKeyboardBuilder()
            builder.button(text="▶️ Перейти к следующему", callback_data=f"next_task_{qnum+1}")
            builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            builder.adjust(1)
            await callback.message.answer(
                f"⚠️ Извините, возникла проблема при загрузке задания {qnum} (подпункт {sub}).\n"
                "Вы можете перейти к следующему заданию или завершить тест.",
                reply_markup=builder.as_markup()
            )
    except Exception as e:
        logging.error(f"Error in show_math_subtask: {e}", exc_info=True)
        try:
            _, _, qnum, _ = callback.data.split("_")
            qnum = int(qnum)
            builder = InlineKeyboardBuilder()
            builder.button(text="▶️ Перейти к следующему", callback_data=f"next_task_{qnum+1}")
            builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            builder.adjust(1)
            await callback.message.answer(
                "⚠️ Произошла ошибка при загрузке задания.\n"
                "Вы можете перейти к следующему заданию или завершить тест.",
                reply_markup=builder.as_markup()
            )
        except Exception as e2:
            logging.error(f"Ошибка при обработке исключения: {e2}")
            await callback.message.answer("Произошла ошибка. Попробуйте начать тест заново.")


@dp.callback_query(lambda c: c.data.startswith("next_task_"))
async def show_next_task(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        data = await state.get_data()
        subject = data.get("subject")
        year = data.get("year")
        internal_variant = data.get("variant")
        next_question = int(callback.data.split("_")[2])

        logging.info(
            f"Переход к следующему заданию: {next_question}, subject={subject}, year={year}, variant={internal_variant}")

        max_tasks = 19 if subject == "math" else 26
        if next_question > max_tasks:
            await end_test(callback.message, state, is_early_end=False)
            return

        # Особая логика для 13
        if next_question == 13 and subject == "math":
            builder = InlineKeyboardBuilder()
            builder.button(text="Перейти к заданию 13а", callback_data="math_subtask_13_a")
            builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            builder.adjust(1)
            await callback.message.answer(
                "Задание 13 состоит из нескольких подпунктов. Нажмите кнопку ниже, чтобы перейти к первому подпункту.",
                reply_markup=builder.as_markup()
            )
            return

        # Особая логика для 19
        if next_question == 19 and subject == "math":
            builder = InlineKeyboardBuilder()
            builder.button(text="Перейти к подпункту а", callback_data="math_subtask_19_a")
            builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            builder.adjust(1)
            await callback.message.answer(
                "Задание 19 состоит из нескольких подпунктов. Нажмите кнопку ниже, чтобы перейти к первому подпункту.",
                reply_markup=builder.as_markup()
            )
            return

        # Получаем путь к изображению
        image_path = get_task_image_path(subject, year, internal_variant, next_question)
        variant_data = load_variant_data(subject, year)
        task_data = variant_data.get(next_question, {}) if variant_data else {}

        # Значение по умолчанию для hint
        hint = "Введите ответ"

        # Если есть варианты ответа (options)
        if "options" in task_data:
            options_builder = InlineKeyboardBuilder()
            for opt in task_data["options"]:
                options_builder.button(
                    text=opt,
                    callback_data=f"answer_option_{next_question}_{opt}"
                )
            options_builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            options_builder.adjust(1)
            try:
                photo = FSInputFile(image_path)
                await callback.message.answer_photo(
                    photo=photo,
                    caption=task_data.get("hint", hint),
                    reply_markup=options_builder.as_markup()
                )
                await state.update_data(current_question=next_question)
                try:
                    await callback.message.delete()
                except Exception as e:
                    logging.error(f"Ошибка при удалении сообщения: {e}")
            except Exception as e:
                logging.error(f"Ошибка при отправке изображения: {e}")
                builder = InlineKeyboardBuilder()
                builder.button(text="▶️ Перейти к следующему", callback_data=f"next_task_{next_question + 1}")
                builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
                builder.adjust(1)
                await callback.message.answer(
                    f"⚠️ Извините, возникла проблема при загрузке задания {next_question}.\n"
                    "Вы можете перейти к следующему заданию или завершить тест.",
                    reply_markup=builder.as_markup()
                )
            return

        # Обычное поведение (на всякий случай)
        builder = InlineKeyboardBuilder()
        builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
        builder.adjust(1)
        hint = task_data.get("hint", hint)  # если есть, переопределяем

        try:
            photo = FSInputFile(image_path)
            await callback.message.answer_photo(
                photo=photo,
                caption=hint,
                reply_markup=builder.as_markup()
            )
            await state.update_data(current_question=next_question)
            try:
                await callback.message.delete()
            except Exception as e:
                logging.error(f"Ошибка при удалении сообщения: {e}")
        except Exception as e:
            logging.error(f"Ошибка при отправке изображения: {e}")
            builder = InlineKeyboardBuilder()
            builder.button(text="▶️ Перейти к следующему", callback_data=f"next_task_{next_question + 1}")
            builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            builder.adjust(1)
            await callback.message.answer(
                f"⚠️ Извините, возникла проблема при загрузке задания {next_question}.\n"
                "Вы можете перейти к следующему заданию или завершить тест.",
                reply_markup=builder.as_markup()
            )
    except Exception as e:
        logging.error(f"Ошибка в show_next_task: {e}")


@dp.callback_query(lambda c: c.data.startswith("answer_option_13_"))
async def process_13_option_answer(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    answered_questions = data.get("answered_questions", set())
    correct_answers = data.get("correct_answers", 0)
    subject = data.get("subject")
    year = data.get("year")
    variant = data.get("variant")
    if not (subject and year and variant):
        await callback.message.answer("Ошибка: не удалось определить вариант теста. Попробуйте начать тест заново.")
        return
    _, _, qnum, sub, opt = callback.data.split("_")
    qnum = int(qnum)
    variant_data = load_variant_data(subject, year)
    sub_data = variant_data[qnum][sub]
    correct_answer = sub_data["correct"]

    if (qnum, sub) in answered_questions:
        await callback.message.answer("⚠️ Вы уже ответили на этот подпункт.")
        return
    answered_questions.add((qnum, sub))
    is_correct = opt == correct_answer
    await state.update_data(answered_questions=answered_questions)
    await state.update_data(**{f"answer_13_{sub}": opt})
    if is_correct:
        correct_answers += 1
        await state.update_data(correct_answers=correct_answers)

    state_data = await state.get_data()
    user_a = state_data.get("answer_13_a", "-")
    user_b = state_data.get("answer_13_b", "-")
    correct_a = variant_data[qnum]["a"]["correct"]
    correct_b = variant_data[qnum]["b"]["correct"]
    explanation = variant_data[qnum]["explanation"]

    if user_a != "-" and user_b != "-":
        msg = ""
        if user_a == correct_a:
            msg += f"✅ Пункт а): Ваш ответ: {user_a}\n"
        else:
            msg += f"❌ Пункт а): Ваш ответ: {user_a}\n"
        msg += f"Правильный ответ: {correct_a}\n"
        if user_b == correct_b:
            msg += f"✅ Пункт б): Ваш ответ: {user_b}\n"
        else:
            msg += f"❌ Пункт б): Ваш ответ: {user_b}\n"
        msg += f"Правильный ответ: {correct_b}\n"
        builder = InlineKeyboardBuilder()
        builder.button(text="▶️ Следующее задание", callback_data=f"next_task_{qnum+1}")
        builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
        builder.adjust(1)
        if subject == "math":
            from pathlib import Path
            BASE_DIR = Path(__file__).resolve().parent.parent
            photo_path = BASE_DIR / f"assets/test_images/math/{year}/demo 1/explanations/{explanation}"
            try:
                await callback.message.answer_photo(
                    FSInputFile(str(photo_path)),
                    caption=msg + "\nРешение:",
                    reply_markup=builder.as_markup()
                )
            except Exception:
                await callback.message.answer(msg + "\n⚠️ Не удалось отправить фото решения.", reply_markup=builder.as_markup())
        else:
            msg += f"\nОбъяснение: {explanation}"
            await callback.message.answer(msg, reply_markup=builder.as_markup())
    else:
        if sub == "a":
            builder = InlineKeyboardBuilder()
            builder.button(text="Перейти к подпункту б", callback_data=f"math_subtask_13_b")
            builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            builder.adjust(1)
            await callback.message.answer(
                f"Ответ на подпункт а) {'✅ верный' if is_correct else '❌ неверный'}. "
                "Нажмите кнопку ниже, чтобы перейти к подпункту б.",
                reply_markup=builder.as_markup()
            )

@dp.callback_query(lambda c: c.data.startswith("answer_option_19_"))
async def process_19_option_answer(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    answered_questions = data.get("answered_questions", set())
    correct_answers = data.get("correct_answers", 0)
    subject = data.get("subject")
    year = data.get("year")
    variant = data.get("variant")
    _, _, qnum, sub, opt = callback.data.split("_")
    qnum = int(qnum)
    variant_data = load_variant_data(subject, year)
    sub_data = variant_data[qnum][sub]
    correct_answer = sub_data["correct"]

    if (qnum, sub) in answered_questions:
        await callback.message.answer("⚠️ Вы уже ответили на этот подпункт.")
        return
    answered_questions.add((qnum, sub))
    is_correct = opt == correct_answer
    await state.update_data(answered_questions=answered_questions)
    await state.update_data(**{f"answer_19_{sub}": opt})
    if is_correct:
        correct_answers += 1
        await state.update_data(correct_answers=correct_answers)

    if sub == "a":
        builder = InlineKeyboardBuilder()
        builder.button(text="Перейти к подпункту б", callback_data=f"math_subtask_19_b")
        builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
        builder.adjust(1)
        await callback.message.answer(
            f"Ответ на подпункт а) {'✅ верный' if is_correct else '❌ неверный'}. "
            "Нажмите кнопку ниже, чтобы перейти к подпункту б.",
            reply_markup=builder.as_markup()
        )
        return
    if sub == "b":
        builder = InlineKeyboardBuilder()
        builder.button(text="Перейти к подпункту в", callback_data=f"math_subtask_19_c")
        builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
        builder.adjust(1)
        await callback.message.answer(
            f"Ответ на подпункт б) {'✅ верный' if is_correct else '❌ неверный'}. "
            "Нажмите кнопку ниже, чтобы перейти к подпункту в.",
            reply_markup=builder.as_markup()
        )
        return

    is_last = (qnum == 19 and sub == 'c')
    builder = InlineKeyboardBuilder()
    if is_last:
        builder.button(text="Посмотреть результаты", callback_data="end_test")
        await state.update_data(full_complete=True)
    else:
        builder.button(text="▶️ Следующее задание", callback_data=f"next_task_{qnum+1}")
        builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
    builder.adjust(1)

    state_data = await state.get_data()
    user_a = state_data.get("answer_19_a", "-")
    user_b = state_data.get("answer_19_b", "-")
    user_c = state_data.get("answer_19_c", "-")
    correct_a = variant_data[qnum]["a"]["correct"]
    correct_b = variant_data[qnum]["b"]["correct"]
    correct_c = variant_data[qnum]["c"]["correct"]
    explanation = variant_data[qnum].get("explanation", "task19_demo1.jpg")

    if user_a != "-" and user_b != "-" and user_c != "-":
        msg = ""
        if user_a == correct_a:
            msg += f"✅ Пункт а): Ваш ответ: {user_a}\n"
        else:
            msg += f"❌ Пункт а): Ваш ответ: {user_a}\n"
        msg += f"Правильный ответ: {correct_a}\n"
        if user_b == correct_b:
            msg += f"✅ Пункт б): Ваш ответ: {user_b}\n"
        else:
            msg += f"❌ Пункт б): Ваш ответ: {user_b}\n"
        msg += f"Правильный ответ: {correct_b}\n"
        if user_c == correct_c:
            msg += f"✅ Пункт в): Ваш ответ: {user_c}\n"
        else:
            msg += f"❌ Пункт в): Ваш ответ: {user_c}\n"
        msg += f"Правильный ответ: {correct_c}\n"
        if subject == "math":
            from pathlib import Path
            BASE_DIR = Path(__file__).resolve().parent.parent
            explanations_dir = BASE_DIR / f"assets/test_images/math/{year}/demo 1/explanations"
            photo_path = None
            for ext in ("jpg", "png"):
                candidate = explanations_dir / f"task19.{ext}"
                if candidate.exists():
                    photo_path = candidate
                    break
            try:
                if photo_path:
                    await callback.message.answer_photo(
                        types.FSInputFile(str(photo_path)),
                        caption=msg + "\nРешение:",
                        reply_markup=builder.as_markup()
                    )
                else:
                    await callback.message.answer(msg + "\n(Фото решения не найдено)", reply_markup=builder.as_markup())
            except Exception:
                await callback.message.answer(msg + "\n⚠️ Не удалось отправить фото решения.", reply_markup=builder.as_markup())
        else:
            msg += f"\nОбъяснение: {explanation}"
            await callback.message.answer(msg, reply_markup=builder.as_markup())
        return
    else:
        if sub == "a":
            builder = InlineKeyboardBuilder()
            builder.button(text="Перейти к подпункту б", callback_data=f"math_subtask_19_b")
            builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            builder.adjust(1)
            await callback.message.answer(
                f"Ответ на подпункт а) {'✅ верный' if is_correct else '❌ неверный'}. "
                "Нажмите кнопку ниже, чтобы перейти к подпункту б.",
                reply_markup=builder.as_markup()
            )
            return
        if sub == "b":
            builder = InlineKeyboardBuilder()
            builder.button(text="Перейти к подпункту в", callback_data=f"math_subtask_19_c")
            builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
            builder.adjust(1)
            await callback.message.answer(
                f"Ответ на подпункт б) {'✅ верный' if is_correct else '❌ неверный'}. "
                "Нажмите кнопку ниже, чтобы перейти к подпункту в.",
                reply_markup=builder.as_markup()
            )
            return

@dp.callback_query(lambda c: c.data.startswith("answer_option_"))
async def process_option_answer(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    subject = data.get("subject")
    year = data.get("year")
    variant = data.get("variant")
    if not (subject and year and variant):
        await callback.message.answer("Ошибка: не удалось определить вариант теста. Попробуйте начать тест заново.")
        return
    current_question = data.get("current_question")
    answered_questions = data.get("answered_questions", set())
    correct_answers = data.get("correct_answers", 0)

    _, _, qnum, opt = callback.data.split("_")
    qnum = int(qnum)

    variant_data = load_variant_data(subject, year)
    answer_data = variant_data[qnum]
    correct_answer = answer_data["correct"]
    if qnum in answered_questions:
        await callback.message.answer("⚠️ Вы уже ответили на этот вопрос.")
        return
    answered_questions.add(qnum)

    is_correct = opt == correct_answer
    is_last = (subject == "rus" and qnum == 26) or (subject == "math" and qnum == 19)
    builder = InlineKeyboardBuilder()
    if is_last:
        builder.button(text="Посмотреть результаты", callback_data="end_test")
        await state.update_data(full_complete=True)
    else:
        builder.button(text="▶️ Следующее задание", callback_data=f"next_task_{qnum+1}")
        builder.button(text="⏩ Закончить досрочно", callback_data="end_test")
    builder.adjust(1)
    await state.update_data(answered_questions=answered_questions)
    if is_correct:
        correct_answers += 1
        await state.update_data(correct_answers=correct_answers)
    await send_answer(is_correct, correct_answer, answer_data["explanation"], callback.message, builder, year, subject)


async def update_user_stats(user_id: int) -> None:
    """Обновление статистики пользователя"""
    try:
        # Получаем все результаты тестов пользователя
        test_results = user_data_manager.get_user_results(user_id)
        
        total_tests = len(test_results)
        total_score = sum(result['score'] for result in test_results)
        avg_score = total_score / total_tests if total_tests > 0 else 0
        
        # Обновляем профиль пользователя с новой статистикой
        profile_data = {
            'stats': {
                'total_tests': total_tests,
                'total_score': total_score,
                'avg_score': avg_score
            }
        }
        user_data_manager.update_profile(user_id, profile_data)
        
    except Exception as e:
        logging.error(f"Ошибка при обновлении статистики пользователя {user_id}: {e}")

async def save_test_completion(user_id: int, test_id: str, correct_answers: int, 
                             total_questions: int, test_type: str = "practice") -> None:
    """Сохранение результатов прохождения теста"""
    try:
        # Сохраняем результат теста
        test_data = {
            'test_type': test_type,
            'answers': correct_answers,
            'total_questions': total_questions,
            'completion_time': datetime.now().isoformat()
        }
        
        user_data_manager.save_test_results(
            user_id=user_id,
            test_id=test_id,
            score=correct_answers,
            max_score=total_questions,
            answers=test_data
        )

        # Обновляем общую статистику
        await update_user_stats(user_id)

    except Exception as e:
        logging.error(f"Ошибка при сохранении результатов теста для пользователя {user_id}: {e}")

async def end_test(message: types.Message, state: FSMContext, is_early_end: bool = False) -> None:
    try:
        data = await state.get_data()
        correct_answers = data.get("correct_answers", 0)
        answered_questions = data.get("answered_questions", set())
        total_questions = len(answered_questions)
        subject = data.get("subject")
        year = data.get("year")
        internal_variant = data.get("variant")
        display_variant = data.get("display_variant", internal_variant)
        user_id = data.get("user_id")

        if not user_id:
            user_id = (
                message.chat.id if isinstance(message, types.Message)
                else message.from_user.id if hasattr(message, 'from_user')
                else None
            )

        if not user_id:
            raise ValueError("Could not determine user ID")

        await save_test_completion(
            user_id=user_id,
            test_id=f"{subject}_demo_{year}",
            correct_answers=correct_answers,
            total_questions=total_questions
        )

        # Определяем общее количество заданий для памятки, если пользователь не ответил ни на один вопрос
        if total_questions == 0:
            if subject == "math":
                total_questions = 19
            else:
                total_questions = 26

        if total_questions > 0:
            percentage = (correct_answers / total_questions * 100)
            result_text = f"""🏁 Тест {display_variant} {('завершен досрочно!' if is_early_end else 'завершен!')}
\n📊 Ваши результаты:\nПравильных ответов: {correct_answers} из {total_questions}\nПроцент выполнения: {percentage:.1f}%"""
        else:
            result_text = f"""🏁 Тест {display_variant} {('завершен досрочно!' if is_early_end else 'завершен!')}
\n📊 Ваши результаты:\nВы не ответили ни на один вопрос"""

        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Пройти заново", callback_data=f"start_test_{subject}_{year}_1")
        builder.button(text="⬅️ К выбору варианта", callback_data=f"year_{subject}_{year}")
        builder.adjust(1)

        from pathlib import Path
        BASE_DIR = Path(__file__).resolve().parent.parent
        variant_key = "demo 1"
        files_dir = BASE_DIR / "assets" / "test_images" / subject / year / variant_key / "files"
        tasks_file = files_dir / "variant_demo1.pdf"
        keys_file = files_dir / "keys_demo1.pdf"
        files_sent = False

        if is_early_end:
            # При досрочном завершении только сообщение с результатами
            result_text += "\n\n📥 Файлы с заданиями и ответами можно получить только после полного прохождения теста. Пройдите все задания, чтобы получить доступ к материалам."
            await message.answer(result_text, reply_markup=builder.as_markup())
        else:
            # При полном завершении — всегда отправлять файлы, если они есть
            try:
                if tasks_file.exists():
                    document = FSInputFile(str(tasks_file))
                    await message.answer_document(document=document, caption=f"📝 Вот файл с заданиями {display_variant}")
                    files_sent = True
                if keys_file.exists():
                    document = FSInputFile(str(keys_file))
                    await message.answer_document(document=document, caption=f"🔑 Вот файл с ответами {display_variant}")
                    files_sent = True
                if not files_sent:
                    await message.answer("❌ Файлы с заданиями и ответами не найдены.")
                await message.answer(result_text, reply_markup=builder.as_markup())
            except Exception as e:
                await message.answer("❌ Произошла ошибка при отправке файлов с заданиями и ответами.")
                await message.answer(result_text, reply_markup=builder.as_markup())

        await state.clear()
        logging.info(f"Тест завершен для пользователя {user_id}. Результаты: {correct_answers}/{total_questions}")

    except Exception as e:
        logging.error(f"Error in end_test: {e}")
        await message.answer("❌ Произошла ошибка при завершении теста")

@dp.callback_query(lambda c: c.data == "end_test")
async def end_test_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик досрочного завершения теста"""
    try:
        await callback.answer()
        await state.update_data(user_id=callback.from_user.id)
        logging.info(f"Saving user_id to state: {callback.from_user.id}")
        data = await state.get_data()
        is_full = data.get("full_complete", False)
        await end_test(callback.message, state, is_early_end=not is_full)
    except Exception as e:
        logging.error(f"Error in end_test_handler: {e}")


@dp.callback_query(lambda c: c.data.startswith("download_"))
async def send_test_files(callback: types.CallbackQuery):
    """Обработчик скачивания файлов заданий и ответов"""
    try:
        await callback.answer()
        _, file_type, subject, year = callback.data.split("_")
        variant_key = "demo 1"

        file_path = BASE_DIR / "assets" / "test_images" / subject / year / variant_key / "files"

        if file_type == "tasks":
            file_path = file_path / "variant_demo1.pdf"
            caption = "📝 Вот файл с заданиями"
        else:  # keys
            file_path = file_path / "keys_demo1.pdf"
            caption = "🔑 Вот файл с ответами"

        if file_path.exists():
            document = FSInputFile(str(file_path))
            await callback.message.answer_document(
                document=document,
                caption=caption
            )
            logging.info(f"Файл {file_path} отправлен пользователю {callback.from_user.id}.")
        else:
            await callback.message.answer("❌ Извините, файл не найден")
            logging.error(f"Файл не найден: {file_path}")

    except Exception as e:
        logging.error(f"Error in send_test_files: {e}")
        await callback.message.answer("❌ Произошла ошибка при отправке файла")

