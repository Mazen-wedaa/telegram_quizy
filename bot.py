#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TOKEN = "7705883869:AAF5KsIeyMnUWfQC3qGbeJNJwmasR_8Xi3c" # Make sure this is correct

# Quiz Configuration
SUBJECTS = ["Internet Technology", "Software Engineering", "Data Structures", "Computer Networks", "Database Systems"]
LECTURES_PER_SUBJECT = 14  # Default, can be modified
QUESTIONS_PER_LECTURE = 10
# TIMER_SECONDS = 30 # Removed timer

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUIZ_DATA_DIR = os.path.join(BASE_DIR, "quiz_data")
QUESTIONS_DIR = os.path.join(QUIZ_DATA_DIR, "questions")
LEADERBOARD_FILE = os.path.join(QUIZ_DATA_DIR, "leaderboard.json")

# Ensure directories exist
os.makedirs(QUESTIONS_DIR, exist_ok=True)
for subject in SUBJECTS:
    subject_dir = os.path.join(QUESTIONS_DIR, subject.lower().replace(" ", "_"))
    os.makedirs(subject_dir, exist_ok=True)

# Egyptian Arabic humor responses
PERFECT_SCORE_RESPONSES = [
    "ما شاء الله عليك! 🚀 انت دلوقتي في المركز {position} على لوحة المتصدرين!",
    "برافو عليك! 💯 شغل عالي المستوى! انت دلوقتي في المركز {position}!",
    "عبقرية مصرية خالصة! 🧠 مركزك دلوقتي {position} على اللوحة!"
]

LOW_SCORE_RESPONSES = [
    "معلش يا صاحبي، المرة الجاية هتكسرها! 💪 استمر في المذاكرة!",
    "ولا يهمك! الدنيا مش آخرها! 😄 شد حيلك شوية وهتبقى تمام!",
    "طب ما تحاول تاني؟ 🙈 المذاكرة هي الحل!"
]

# User session storage
user_data = {}

def get_or_create_leaderboard():
    """Get existing leaderboard or create a new one"""
    current_month = datetime.datetime.now().strftime("%Y-%B")

    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
                leaderboard = json.load(f)
                # Reset if month changed
                if leaderboard.get("version") != current_month:
                    logger.info(f"Leaderboard month changed from {leaderboard.get('version')} to {current_month}. Resetting scores.")
                    leaderboard = {
                        "version": current_month,
                        "users": {}
                    }
        except json.JSONDecodeError:
             logger.error(f"Error decoding leaderboard JSON from {LEADERBOARD_FILE}. Creating new one.")
             leaderboard = {
                 "version": current_month,
                 "users": {}
             }
    else:
        logger.info(f"Leaderboard file {LEADERBOARD_FILE} not found. Creating new one.")
        leaderboard = {
            "version": current_month,
            "users": {}
        }

    return leaderboard

def save_leaderboard(leaderboard):
    """Save leaderboard to file"""
    try:
        with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
            json.dump(leaderboard, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f"Error saving leaderboard to {LEADERBOARD_FILE}: {e}")


def get_or_create_question_file(subject, lecture_num):
    """Get existing question file or create a sample one"""
    subject_dir = os.path.join(QUESTIONS_DIR, subject.lower().replace(" ", "_"))
    file_path = os.path.join(subject_dir, f"lecture{lecture_num}.json")

    if not os.path.exists(file_path):
        logger.info(f"Question file {file_path} not found. Creating sample questions.")
        # Create sample questions if file doesn't exist
        sample_questions = {
            "lecture": lecture_num,
            "questions": []
        }

        # Generate 10 sample questions
        for i in range(1, QUESTIONS_PER_LECTURE + 1):
            question = {
                "text": f"Sample question {i} for {subject} Lecture {lecture_num}?",
                "options": [
                    f"Option A for question {i}",
                    f"Option B for question {i}",
                    f"Option C for question {i}",
                    f"Option D for question {i}"
                ],
                "correct": 0,  # First option is correct in sample
                "explanation": f"This is a sample explanation for question {i}."
            }
            sample_questions["questions"].append(question)

        # Save sample questions
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sample_questions, f, ensure_ascii=False, indent=2)
            logger.info(f"Sample question file created at {file_path}")
        except IOError as e:
            logger.error(f"Error creating sample question file {file_path}: {e}")
            return {"lecture": lecture_num, "questions": []} # Return empty if error

    # Load and return questions
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logger.error(f"Error loading question file {file_path}: {e}")
        return {"lecture": lecture_num, "questions": []} # Return empty if error

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.first_name}) started the bot.")
    keyboard = [
        [InlineKeyboardButton("Choose Subject 📚", callback_data='choose_subject')],
        [InlineKeyboardButton("Leaderboard 🏆", callback_data='leaderboard')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        f'مرحباً {user.first_name}! 👋\n\n'
        f'أنا بوت الاختبارات الأكاديمية. اختر موضوعاً للبدء في الاختبار أو اعرض لوحة المتصدرين.',
        reply_markup=reply_markup
    )

def button_callback(update: Update, context: CallbackContext) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    query.answer() # Important to answer callback queries

    data = query.data
    user_id = str(update.effective_user.id)
    logger.info(f"User {user_id} pressed button with data: {data}")

    if data == 'choose_subject':
        show_subjects(update, context)
    elif data == 'leaderboard':
        show_leaderboard(update, context)
    elif data.startswith('subject_'):
        try:
            subject_index = int(data.split('_')[1])
            show_lectures(update, context, subject_index)
        except (IndexError, ValueError):
             logger.warning(f"Invalid subject callback data: {data}")
             query.edit_message_text("حدث خطأ. يرجى المحاولة مرة أخرى.")
    elif data.startswith('lecture_'):
        try:
            parts = data.split('_')
            subject_index = int(parts[1])
            lecture_num = int(parts[2])
            start_quiz(update, context, subject_index, lecture_num)
        except (IndexError, ValueError):
             logger.warning(f"Invalid lecture callback data: {data}")
             query.edit_message_text("حدث خطأ. يرجى المحاولة مرة أخرى.")
    elif data.startswith('answer_'):
        try:
            parts = data.split('_')
            selected_option = int(parts[1])
            handle_answer(update, context, selected_option)
        except (IndexError, ValueError):
             logger.warning(f"Invalid answer callback data: {data}")
             query.edit_message_text("حدث خطأ. يرجى المحاولة مرة أخرى.")
    elif data == 'next_question':
        show_next_question(update, context)
    elif data == 'main_menu':
        show_main_menu(update, context)
    else:
        logger.warning(f"Unhandled callback data: {data}")


def show_subjects(update: Update, context: CallbackContext) -> None:
    """Show available subjects."""
    keyboard = []
    for i, subject in enumerate(SUBJECTS):
        keyboard.append([InlineKeyboardButton(subject, callback_data=f'subject_{i}')])

    keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    query = update.callback_query
    try:
        query.edit_message_text(
            text="اختر الموضوع الذي ترغب في اختباره:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error editing message in show_subjects: {e}")


def show_lectures(update: Update, context: CallbackContext, subject_index: int) -> None:
    """Show available lectures for a subject."""
    if not (0 <= subject_index < len(SUBJECTS)):
        logger.warning(f"Invalid subject index {subject_index} in show_lectures.")
        query = update.callback_query
        query.edit_message_text("حدث خطأ في اختيار الموضوع. يرجى المحاولة مرة أخرى.")
        return

    subject = SUBJECTS[subject_index]
    keyboard = []

    # Create rows with 3 lectures each
    row = []
    for i in range(1, LECTURES_PER_SUBJECT + 1):
        row.append(InlineKeyboardButton(f"Lecture {i}", callback_data=f'lecture_{subject_index}_{i}'))
        if len(row) == 3:
            keyboard.append(row)
            row = []

    # Add any remaining lectures
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("Back to Subjects", callback_data='choose_subject')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    query = update.callback_query
    try:
        query.edit_message_text(
            text=f"اختر المحاضرة من {subject}:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error editing message in show_lectures: {e}")


def start_quiz(update: Update, context: CallbackContext, subject_index: int, lecture_num: int) -> None:
    """Start a quiz for the selected subject and lecture."""
    user_id = str(update.effective_user.id)

    if not (0 <= subject_index < len(SUBJECTS)):
        logger.warning(f"Invalid subject index {subject_index} in start_quiz.")
        query = update.callback_query
        query.edit_message_text("حدث خطأ في اختيار الموضوع. يرجى المحاولة مرة أخرى.")
        return

    subject = SUBJECTS[subject_index]
    logger.info(f"User {user_id} starting quiz for {subject} - Lecture {lecture_num}")

    # Load questions
    quiz_content = get_or_create_question_file(subject, lecture_num)
    questions = quiz_content.get("questions", [])

    if not questions:
         logger.warning(f"No questions found for {subject} - Lecture {lecture_num}. File path: {os.path.join(QUESTIONS_DIR, subject.lower().replace(' ', '_'), f'lecture{lecture_num}.json')}")
         query = update.callback_query
         query.edit_message_text(f"عذراً، لا توجد أسئلة متاحة لهذه المحاضرة ({subject} - المحاضرة {lecture_num}). يرجى اختيار محاضرة أخرى.")
         return

    # Initialize user session
    user_data[user_id] = {
        'subject': subject,
        'lecture': lecture_num,
        'questions': questions,
        'current_question': 0,
        'score': 0,
        'start_time': datetime.datetime.now() # Keep start time for potential future use (e.g., duration tracking)
    }

    query = update.callback_query
    try:
        query.edit_message_text(
            text=f"بدء الاختبار: {subject} - المحاضرة {lecture_num}\n"
                 f"عدد الأسئلة: {len(questions)}\n\n" # Removed timer mention
                 # f"الوقت لكل سؤال: {TIMER_SECONDS} ثانية\n\n" # Removed timer mention
                 f"استعد... انطلق! 🚀"
        )
        # Show first question immediately after brief delay for message edit
        context.job_queue.run_once(lambda ctx: show_next_question(update, ctx), 0.5, context=context)

    except Exception as e:
        logger.error(f"Error editing message in start_quiz: {e}")


def show_next_question(update: Update, context: CallbackContext) -> None:
    """Show the next question in the quiz."""
    query = update.callback_query
    user_id = str(update.effective_user.id)

    if user_id not in user_data:
        logger.warning(f"User {user_id} attempted to continue quiz, but no session data found.")
        if query:
             try:
                 query.edit_message_text("حدث خطأ في الجلسة. يرجى بدء اختبار جديد.")
             except Exception as e:
                 logger.error(f"Error editing message in show_next_question (no session): {e}")
        return

    session = user_data[user_id]

    # Check if quiz is complete
    if session['current_question'] >= len(session['questions']):
        logger.info(f"User {user_id} completed quiz for {session['subject']} - Lecture {session['lecture']}.")
        show_quiz_results(update, context)
        return

    # Get current question
    question_idx = session['current_question']
    question = session['questions'][question_idx]

    # Create options keyboard
    keyboard = []
    options = question.get("options", [])
    if not options:
         logger.error(f"Question {question_idx} for {session['subject']} L{session['lecture']} has no options.")
         # Handle error - maybe skip question or end quiz
         if query:
             query.edit_message_text("حدث خطأ في السؤال الحالي. جار الانتقال للسؤال التالي.")
         session['current_question'] += 1
         context.job_queue.run_once(lambda ctx: show_next_question(update, ctx), 1, context=context) # Try next question after delay
         return

    for i, option in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{chr(65+i)}. {option}", callback_data=f'answer_{i}')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Display question (without timer)
    question_text = question.get("text", "Error: Question text missing.")
    message_text = (
        f"سؤال {question_idx + 1}/{len(session['questions'])}\n\n"
        # f"⏱️ {TIMER_SECONDS} ثانية\n\n" # Removed timer display
        f"{question_text}"
    )

    if query:
        try:
            query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup
            )
        except Exception as e:
            # Handle potential "Message is not modified" error if user clicks 'Next' quickly
            if "Message is not modified" not in str(e):
                 logger.error(f"Error editing message in show_next_question: {e}")
    else:
         # This case might happen if called directly (e.g., from start_quiz delay)
         # Need a way to send the message if query is None
         # For now, log it. A better solution might involve passing chat_id/message_id
         logger.warning("show_next_question called without a callback query.")
         # Attempt to send a new message if possible (requires chat_id)
         # chat_id = update.effective_chat.id # This might not be available if update is None
         # context.bot.send_message(chat_id=chat_id, text=message_text, reply_markup=reply_markup)


# Removed question_timeout function entirely

def handle_answer(update: Update, context: CallbackContext, selected_option: int) -> None:
    """Handle user answer selection."""
    query = update.callback_query
    user_id = str(update.effective_user.id)

    if user_id not in user_data:
        logger.warning(f"User {user_id} answered, but no session data found.")
        query.edit_message_text("حدث خطأ في الجلسة. يرجى بدء اختبار جديد.")
        return

    session = user_data[user_id]
    question_idx = session['current_question']

    # Prevent answering same question multiple times or after quiz ends
    if question_idx >= len(session['questions']):
         logger.warning(f"User {user_id} tried to answer after quiz ended.")
         query.edit_message_text("لقد انتهى الاختبار بالفعل.")
         return

    question = session['questions'][question_idx]
    correct_option = question.get('correct')
    options = question.get('options', [])
    explanation = question.get('explanation', 'لا يوجد شرح متاح.')

    # Validate selected_option and correct_option
    if not (isinstance(correct_option, int) and 0 <= correct_option < len(options)):
         logger.error(f"Invalid correct answer index ({correct_option}) for Q{question_idx} in {session['subject']} L{session['lecture']}.")
         query.edit_message_text("حدث خطأ في بيانات السؤال. جار الانتقال للسؤال التالي.")
         session['current_question'] += 1
         context.job_queue.run_once(lambda ctx: show_next_question(update, ctx), 1, context=context)
         return

    if not (0 <= selected_option < len(options)):
         logger.warning(f"Invalid selected option index ({selected_option}) received from user {user_id}.")
         query.edit_message_text("خيار غير صالح. يرجى المحاولة مرة أخرى.")
         return # Don't advance, let user try again? Or show correct answer? Let's show correct.

    # Check if answer is correct
    is_correct = selected_option == correct_option
    if is_correct:
        session['score'] += 1
        logger.info(f"User {user_id} answered Q{question_idx} correctly.")
    else:
        logger.info(f"User {user_id} answered Q{question_idx} incorrectly (chose {selected_option}, correct was {correct_option}).")


    # Prepare feedback message
    correct_letter = chr(65 + correct_option)
    selected_letter = chr(65 + selected_option)

    feedback = f"سؤال {question_idx + 1}:\n\n{question.get('text', 'N/A')}\n\n"

    if is_correct:
        feedback += f"✅ إجابتك صحيحة: {selected_letter}. {options[selected_option]}\n\n"
    else:
        feedback += f"❌ إجابتك: {selected_letter}. {options[selected_option]}\n"
        feedback += f"✅ الإجابة الصحيحة: {correct_letter}. {options[correct_option]}\n\n"

    feedback += f"💡 {explanation}"

    # Advance to next question state
    session['current_question'] += 1

    # Show feedback
    try:
        query.edit_message_text(
            text=feedback,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("التالي", callback_data='next_question')]
            ])
        )
    except Exception as e:
        logger.error(f"Error editing message in handle_answer: {e}")


def show_quiz_results(update: Update, context: CallbackContext) -> None:
    """Show quiz results and update leaderboard."""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    user = update.effective_user

    if user_id not in user_data:
        logger.warning(f"Attempted to show results for user {user_id}, but no session data found.")
        if query:
             query.edit_message_text("حدث خطأ في الجلسة. يرجى بدء اختبار جديد.")
        return

    session = user_data[user_id]
    score = session['score']
    total = len(session['questions'])
    subject = session['subject']
    lecture = session['lecture']

    logger.info(f"Showing results for user {user_id}: {score}/{total} on {subject} L{lecture}.")

    # Update leaderboard
    leaderboard = get_or_create_leaderboard()
    if user_id not in leaderboard['users']:
        leaderboard['users'][user_id] = {
            'name': user.first_name,
            'score': 0,
            'last_active': datetime.datetime.now().strftime("%Y-%m-%d")
        }

    # Anti-cheat: Limit score updates? (Not implemented yet as per prompt)
    # Simple score addition for now
    leaderboard['users'][user_id]['score'] += score
    leaderboard['users'][user_id]['last_active'] = datetime.datetime.now().strftime("%Y-%m-%d")
    save_leaderboard(leaderboard)

    # Get user position
    sorted_users = sorted(leaderboard['users'].items(),
                         key=lambda x: x[1]['score'],
                         reverse=True)
    position = next((i + 1 for i, (uid, _) in enumerate(sorted_users) if uid == user_id), 0)

    # Prepare results message
    if score == total:
        result_message = PERFECT_SCORE_RESPONSES[hash(user_id) % len(PERFECT_SCORE_RESPONSES)].format(position=position)
    elif score < 3 and total > 0: # Avoid division by zero if total is 0
        result_message = LOW_SCORE_RESPONSES[hash(user_id) % len(LOW_SCORE_RESPONSES)]
    elif total > 0:
         percentage = round((score / total) * 100)
         result_message = f"أحسنت! حصلت على {score} من {total} ({percentage}%). 🎯"
    else:
         result_message = "انتهى الاختبار بدون أسئلة."


    final_text = (
        f"انتهى الاختبار: {subject} - المحاضرة {lecture}\n\n"
        f"النتيجة: {score}/{total}\n\n"
        f"{result_message}"
    )

    if query:
        try:
            query.edit_message_text(
                text=final_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("العودة إلى القائمة الرئيسية", callback_data='main_menu')]
                ])
            )
        except Exception as e:
            logger.error(f"Error editing message in show_quiz_results: {e}")

    # Clean up session
    del user_data[user_id]
    logger.info(f"Cleaned up session data for user {user_id}.")


def show_leaderboard(update: Update, context: CallbackContext) -> None:
    """Show the leaderboard."""
    leaderboard = get_or_create_leaderboard()

    # Sort users by score
    sorted_users = sorted(leaderboard.get('users', {}).items(),
                         key=lambda x: x[1].get('score', 0),
                         reverse=True)

    # Prepare leaderboard message
    message = f"🏆 المتصدرون الشهريون 🏆\n({leaderboard.get('version', 'N/A')})\n\n"

    if not sorted_users:
        message += "لا يوجد متسابقون بعد. كن أول من يظهر هنا!"
    else:
        for i, (user_id, user_info) in enumerate(sorted_users[:10]): # Show top 10
            medal = ""
            if i == 0:
                medal = "👑 "
            elif i == 1:
                medal = "🥈 "
            elif i == 2:
                medal = "🥉 "

            name = user_info.get('name', 'Unknown')
            score = user_info.get('score', 0)
            message += f"{i+1}. {medal}{name}: {score} نقطة\n"

    query = update.callback_query
    try:
        query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("العودة إلى القائمة الرئيسية", callback_data='main_menu')]
            ])
        )
    except Exception as e:
        logger.error(f"Error editing message in show_leaderboard: {e}")


def show_main_menu(update: Update, context: CallbackContext) -> None:
    """Show the main menu."""
    keyboard = [
        [InlineKeyboardButton("Choose Subject 📚", callback_data='choose_subject')],
        [InlineKeyboardButton("Leaderboard 🏆", callback_data='leaderboard')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query = update.callback_query
    try:
        query.edit_message_text(
            text='مرحباً بك في بوت الاختبارات الأكاديمية! 👋\n\n'
                 'اختر موضوعاً للبدء في الاختبار أو اعرض لوحة المتصدرين.',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Error editing message in show_main_menu: {e}")

def error_handler(update: object, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    # Optionally notify user about the error
    if isinstance(update, Update) and update.effective_message:
        try:
            update.effective_message.reply_text("عذراً، حدث خطأ ما. يرجى المحاولة مرة أخرى لاحقاً.")
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")


def main() -> None:
    """Start the bot."""
    logger.info("Starting bot...")
    # Create the Updater and pass it your bot's token
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))

    # Register callback query handlers
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    # Register error handler
    dispatcher.add_error_handler(error_handler)

    # Start the Bot
    updater.start_polling()
    logger.info("Bot started polling.")

    # Run the bot until you press Ctrl-C
    updater.idle()
    logger.info("Bot stopped.")


if __name__ == '__main__':
    main()

