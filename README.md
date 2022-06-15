# Discord Bots
3
 
To run the discord bots, just use the docker compose file. 
4
 
Ensure that the following files exist:
5
 
- config.ini (Must have actual app configs)
6
 
- data.json
7
 
- data-bets.json
8
 
- data-polling.json
9
 
- data-lottery.json
10
 
- output.log
11
 
=======
12
 
# MadVibes Discord bots
13
 
For our small discord server, "Mad Vibes", we decided that we wanted some fun bots to add entertaining features to the discord. As well as reward and punish people for spending more time active. So we decided to create a collection if different bots each with their own behavior and responsibilities. This includes our own currency system to
14
 
​
15
 
Instead of going with the sensible approach of implementing different COGS to handle varying functionality, we thought it would be more interesting and run multiple bots that can interact to each other via HTTP requests. To be more specific, currently the bots use a shared library that allows them to pull data and execute currency transactions.
16
 
​
17
 
## Current Bots
18
 
​
19
 
- Bank: Accrues and Fades currency (VBC). Manages user currency (spending, transferring, taxing and 'destroying'). Also inserts Coin Emojis for other bots to use.
20
 
- Chameleon: Soundboard, can play a set list of sounds, Can perform TTS on behalf of users without permissions.
21
 
- Gambling: Handles gambling games that use currency. Allows user to win and lose money, mostly lose. 
22
 
- Polling: Users can create a poll to vote on things (Basically strawpoll).
23
 
- Store: Buy services (actions) that the bot will do. Mostly punish other users (Kick, Timeout, Move to AFK, Mute etc)
24
 
- Lotto: Every action, a cut goes into 'tax'. This can then be won each week by buying a ticket.
25
 
​
26
 
## Final Notes
27
 
Feel free to use these bots, But there is no support for bugs. If you do find an issue, feel free to raise it and it will probably get fixed eventually :) 
28
 
​
29
 
To run the bots, Update the sample config.ini and add the bots to your server. Then run the python 'main.py's for each bot (Make sure to start the bank first). Or, build and run from the docker images (The Dockerfile uses the image from DockerfileBase from a private registry, remember to change Dockerfile to use local/your own registry). 
