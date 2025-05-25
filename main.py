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
TOKEN = "7880947646:AAHGXQePLW3d-NNe0vKRpCFn1nWYPrZCMJA"

# Quiz Configuration
SUBJECTS = ["Internet Technology", "Software Engineering", "Data Structures", "Computer Networks", "Database Systems"]
LECTURES_PER_SUBJECT = 14  # Default, can be modified
QUESTIONS_PER_LECTURE = 10
TIMER_SECONDS = 30

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
        with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
            leaderboard = json.load(f)
            # Reset if month changed
            if leaderboard.get("version") != current_month:
                leaderboard = {
                    "version": current_month,
                    "users": {}
                }
    else:
        leaderboard = {
            "version": current_month,
            "users": {}
        }
    
    return leaderboard

def save_leaderboard(leaderboard):
    """Save leaderboard to file"""
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(leaderboard, f, ensure_ascii=False, indent=2)

def get_or_create_question_file(subject, lecture_num):
    """Get existing question file or create a sample one"""
    subject_dir = os.path.join(QUESTIONS_DIR, subject.lower().replace(" ", "_"))
    file_path = os.path.join(subject_dir, f"lecture{lecture_num}.json")
    
    if not os.path.exists(file_path):
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
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(sample_questions, f, ensure_ascii=False, indent=2)
    
    # Load and return questions
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
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
    query.answer()
    
    data = query.data
    user_id = str(update.effective_user.id)
    
    if data == 'choose_subject':
        show_subjects(update, context)
    elif data == 'leaderboard':
        show_leaderboard(update, context)
    elif data.startswith('subject_'):
        subject_index = int(data.split('_')[1])
        show_lectures(update, context, subject_index)
    elif data.startswith('lecture_'):
        parts = data.split('_')
        subject_index = int(parts[1])
        lecture_num = int(parts[2])
        start_quiz(update, context, subject_index, lecture_num)
    elif data.startswith('answer_'):
        parts = data.split('_')
        selected_option = int(parts[1])
        handle_answer(update, context, selected_option)
    elif data == 'next_question':
        show_next_question(update, context)
    elif data == 'main_menu':
        show_main_menu(update, context)

def show_subjects(update: Update, context: CallbackContext) -> None:
    """Show available subjects."""
    keyboard = []
    for i, subject in enumerate(SUBJECTS):
        keyboard.append([InlineKeyboardButton(subject, callback_data=f'subject_{i}')])
    
    keyboard.append([InlineKeyboardButton("Back to Main Menu", callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query = update.callback_query
    query.edit_message_text(
        text="اختر الموضوع الذي ترغب في اختباره:",
        reply_markup=reply_markup
    )

def show_lectures(update: Update, context: CallbackContext, subject_index: int) -> None:
    """Show available lectures for a subject."""
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
    query.edit_message_text(
        text=f"اختر المحاضرة من {subject}:",
        reply_markup=reply_markup
    )

def start_quiz(update: Update, context: CallbackContext, subject_index: int, lecture_num: int) -> None:
    """Start a quiz for the selected subject and lecture."""
    user_id = str(update.effective_user.id)
    subject = SUBJECTS[subject_index]
    
    # Load questions
    questions = get_or_create_question_file(subject, lecture_num)
    
    # Initialize user session
    user_data[user_id] = {
        'subject': subject,
        'lecture': lecture_num,
        'questions': questions['questions'],
        'current_question': 0,
        'score': 0,
        'start_time': datetime.datetime.now()
    }
    
    query = update.callback_query
    query.edit_message_text(
        text=f"بدء الاختبار: {subject} - المحاضرة {lecture_num}\n"
             f"عدد الأسئلة: {len(questions['questions'])}\n"
             f"الوقت لكل سؤال: {TIMER_SECONDS} ثانية\n\n"
             f"استعد... انطلق! 🚀"
    )
    
    # Show first question
    show_next_question(update, context)

def show_next_question(update: Update, context: CallbackContext) -> None:
    """Show the next question in the quiz."""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    
    if user_id not in user_data:
        query.edit_message_text("حدث خطأ. يرجى بدء اختبار جديد.")
        return
    
    session = user_data[user_id]
    
    # Check if quiz is complete
    if session['current_question'] >= len(session['questions']):
        show_quiz_results(update, context)
        return
    
    # Get current question
    question_idx = session['current_question']
    question = session['questions'][question_idx]
    
    # Create options keyboard
    keyboard = []
    for i, option in enumerate(question['options']):
        keyboard.append([InlineKeyboardButton(f"{chr(65+i)}. {option}", callback_data=f'answer_{i}')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Display question with timer
    query.edit_message_text(
        text=f"سؤال {question_idx + 1}/{len(session['questions'])}\n\n"
             f"⏱️ {TIMER_SECONDS} ثانية\n\n"
             f"{question['text']}",
        reply_markup=reply_markup
    )
    
    # Set timer for auto-advancing if no answer
    context.job_queue.run_once(
        question_timeout, 
        TIMER_SECONDS,
        context={'update': update, 'user_id': user_id}
    )

def question_timeout(context: CallbackContext) -> None:
    """Handle question timeout."""
    job = context.job
    user_id = job.context['user_id']
    update = job.context['update']
    
    if user_id in user_data:
        session = user_data[user_id]
        current_q = session['current_question']
        
        # Only advance if still on the same question (user hasn't answered)
        if current_q < len(session['questions']):
            session['current_question'] += 1
            
            # Show timeout message
            query = update.callback_query
            query.edit_message_text(
                text="⏱️ انتهى الوقت!\n\n"
                     "لم يتم اختيار إجابة في الوقت المحدد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("التالي", callback_data='next_question')]
                ])
            )

def handle_answer(update: Update, context: CallbackContext, selected_option: int) -> None:
    """Handle user answer selection."""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    
    if user_id not in user_data:
        query.edit_message_text("حدث خطأ. يرجى بدء اختبار جديد.")
        return
    
    session = user_data[user_id]
    question_idx = session['current_question']
    question = session['questions'][question_idx]
    
    # Check if answer is correct
    is_correct = selected_option == question['correct']
    if is_correct:
        session['score'] += 1
    
    # Prepare feedback message
    correct_option = question['correct']
    correct_letter = chr(65 + correct_option)
    selected_letter = chr(65 + selected_option)
    
    feedback = f"سؤال {question_idx + 1}:\n\n{question['text']}\n\n"
    
    if is_correct:
        feedback += f"✅ إجابتك صحيحة: {selected_letter}. {question['options'][selected_option]}\n\n"
    else:
        feedback += f"❌ إجابتك: {selected_letter}. {question['options'][selected_option]}\n"
        feedback += f"✅ الإجابة الصحيحة: {correct_letter}. {question['options'][correct_option]}\n\n"
    
    feedback += f"💡 {question['explanation']}"
    
    # Advance to next question
    session['current_question'] += 1
    
    # Show feedback
    query.edit_message_text(
        text=feedback,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("التالي", callback_data='next_question')]
        ])
    )

def show_quiz_results(update: Update, context: CallbackContext) -> None:
    """Show quiz results and update leaderboard."""
    query = update.callback_query
    user_id = str(update.effective_user.id)
    user = update.effective_user
    
    if user_id not in user_data:
        query.edit_message_text("حدث خطأ. يرجى بدء اختبار جديد.")
        return
    
    session = user_data[user_id]
    score = session['score']
    total = len(session['questions'])
    subject = session['subject']
    lecture = session['lecture']
    
    # Update leaderboard
    leaderboard = get_or_create_leaderboard()
    if user_id not in leaderboard['users']:
        leaderboard['users'][user_id] = {
            'name': user.first_name,
            'score': 0,
            'last_active': datetime.datetime.now().strftime("%Y-%m-%d")
        }
    
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
    elif score < 3:
        result_message = LOW_SCORE_RESPONSES[hash(user_id) % len(LOW_SCORE_RESPONSES)]
    else:
        result_message = f"أحسنت! حصلت على {score} من {total}. 🎯"
    
    query.edit_message_text(
        text=f"انتهى الاختبار: {subject} - المحاضرة {lecture}\n\n"
             f"النتيجة: {score}/{total}\n\n"
             f"{result_message}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("العودة إلى القائمة الرئيسية", callback_data='main_menu')]
        ])
    )
    
    # Clean up session
    del user_data[user_id]

def show_leaderboard(update: Update, context: CallbackContext) -> None:
    """Show the leaderboard."""
    leaderboard = get_or_create_leaderboard()
    
    # Sort users by score
    sorted_users = sorted(leaderboard['users'].items(), 
                         key=lambda x: x[1]['score'], 
                         reverse=True)
    
    # Prepare leaderboard message
    message = f"🏆 المتصدرون الشهريون 🏆\n({leaderboard['version']})\n\n"
    
    if not sorted_users:
        message += "لا يوجد متسابقون بعد. كن أول من يظهر هنا!"
    else:
        for i, (user_id, user_data) in enumerate(sorted_users[:10]):
            medal = ""
            if i == 0:
                medal = "👑 "
            elif i == 1:
                medal = "🥈 "
            elif i == 2:
                medal = "🥉 "
            
            message += f"{i+1}. {medal}{user_data['name']}: {user_data['score']} نقطة\n"
    
    query = update.callback_query
    query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("العودة إلى القائمة الرئيسية", callback_data='main_menu')]
        ])
    )

def show_main_menu(update: Update, context: CallbackContext) -> None:
    """Show the main menu."""
    keyboard = [
        [InlineKeyboardButton("Choose Subject 📚", callback_data='choose_subject')],
        [InlineKeyboardButton("Leaderboard 🏆", callback_data='leaderboard')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query = update.callback_query
    query.edit_message_text(
        text='مرحباً بك في بوت الاختبارات الأكاديمية! 👋\n\n'
             'اختر موضوعاً للبدء في الاختبار أو اعرض لوحة المتصدرين.',
        reply_markup=reply_markup
    )

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    
    # Register callback query handler
    dispatcher.add_handler(CallbackQueryHandler(button_callback))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
