User
  │
  ├─── Conversation (One-to-Many)
  │       │
  │       └─── ChatSession (One-to-Many)
  │               │
  │               └─── ChatMessage (One-to-Many)
  │
  └─── ChatSession (One-to-Many)

BotPersonality
  │
  └─── ConversationSetting (One-to-Many)

ChatMessage
  │
  └─── UserFeedback (One-to-One)