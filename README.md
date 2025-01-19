# # **PunishmentSync**

> **PunishmentSync** is a powerful Discord bot that synces moderation punishments across multiple guilds and in game servers.

---

## Getting Started

0. **Creating**: Visit [Discord Developer Portal](https://discord.com/developers/applications) and create a "New Application". Name it whatever you want and agree to the TOS and Developer Policy.
1. **Intents**: Click `Bot` and enable `Presence Intent`, `Server Members Intent`, and `Message Content Intent`.
2. **Inviting**: Click `OAuth2` and select the `bot` and `applications.commands` scopes, scroll down and select the `Administrator` permission, scroll down and `Copy` the `Generated URL`, paste it into your web browser and invite the bot to **ALL** guilds you want it to function in.
3. **Generating Bot Token**: Click `Bot` and `Reset Token` and keep that token handy for the next step.
4. **Configurating**: Visit the `example_config.yml` file, copy all the contents, and create a `config.yml` file where you paste all the contents of the example config in. Paste the bot token in `TOKEN` and configure everything else to your needs.
5. **Start Punishing**: Start by typing `/` in a server that the bot shares with you to view all the commands it has to offer.

---

## **Folder Structure**

A quick overview of the project's structure:

```
├── cogs/
│   ├── commands/         # Main bot commands
│   ├── events/           # Main guild events
│   ├── functions/        # Helper functions
├── .gitignore            # Ignore files
├── main.py               # Main bot file
├── config.yml            # Configuration file
└── README.md             # This file
```

---

## **Support**

**PunishmentSync** was created by `someone0171` (503641822141349888). As you have commissioned me to create this bot, Someone has the obligation to provide support for up to 90 days. After that 90 day period, additional support may require compensation. Support commences on January 21st, 2025 (01/21/25).

Please feel free to tip/donate to help my work: [PayPal](https://paypal.me/Someone0171)