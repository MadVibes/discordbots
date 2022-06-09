# MadVibes Discord bots
For our small discord server, "Mad Vibes", we decided that we wanted some fun bots to add entertaining features to the discord. As well as reward and punish people for spending more time active. So we decided to create a collection if different bots each with their own behavior and responsibilities. This includes our own currency system to

Instead of going with the sensible approach of implementing different COGS to handle varying functionality, we thought it would be more interesting and run multiple bots that can interact to each other via HTTP requests. To be more specific, currently the bots use a shared library that allows them to pull data and execute currency transactions.

## Current Bots

- Bank: Accrues and Fades currency (VBC). Manages user currency (spending, transferring, taxing and 'destroying'). Also inserts Coin Emojis for other bots to use.
- Chameleon: Soundboard, can play a set list of sounds, Can perform TTS on behalf of users without permissions.
- Gambling: Handles gambling games that use currency. Allows user to win and lose money, mostly lose. 
- Polling: Users can create a poll to vote on things (Basically strawpoll).
- Store: Buy services (actions) that the bot will do. Mostly punish other users (Kick, Timeout, Move to AFK, Mute etc)
- Lotto: Every action, a cut goes into 'tax'. This can then be won each week by buying a ticket.

## Final Notes
Feel free to use these bots, But there is no support for bugs. If you do find an issue, feel free to raise it and it will probably get fixed eventually :) 

To run the bots, Update the sample config.ini and add the bots to your server. Then run the python 'main.py's for each bot (Make sure to start the bank first). Or, build and run from the docker images (The Dockerfile uses the image from DockerfileBase from a private registry, remember to change Dockerfile to use local/your own registry). 