# Quiz Data Structure

This directory contains the quiz data for the Academic Quiz Bot.

## Directory Structure

```
quiz_data/
├── questions/
│   ├── internet_technology/
│   │   ├── lecture1.json
│   │   └── ...
│   ├── software_engineering/
│   │   ├── lecture1.json
│   │   └── ...
│   └── ...
└── leaderboard.json
```

## Question Format

Each lecture file follows this JSON format:

```json
{
  "lecture": 1,
  "questions": [
    {
      "text": "What is HTTP?",
      "options": ["Hypertext Transfer Protocol", "...", "...", "..."],
      "correct": 0,
      "explanation": "HTTP is the foundation of web communication..."
    },
    ...
  ]
}
```

## Leaderboard Format

The leaderboard file follows this JSON format:

```json
{
  "version": "2025-May",
  "users": {
    "USER_ID_123": {
      "name": "Ahmed",
      "score": 45,
      "last_active": "2025-05-21"
    },
    ...
  }
}
```

## Customization

To add or modify subjects and lectures, simply add or edit the corresponding JSON files in the questions directory.
